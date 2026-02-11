import tempfile
from datetime import datetime
from pathlib import Path
from tkinter import END, Button, Tk, messagebox
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames
from tkinter.ttk import Treeview
from typing import cast
from uuid import uuid4

from pypdf import PdfReader

from converter_app.archive_builder import build_archive_and_save
from converter_app.settings import Settings
from converter_app.xml_inspector import XmlInspector
from datev_creator.ledger_import import (
    AccountsReceivableLedger,
    Consolidate,
    LedgerImport,
    LedgerImportWMetadata,
    LedgerImportWMetadataUUID,
)
from datev_creator.utils import SOFTWARE_NAME
from datev_creator.zugfert2ledger_import import (
    LEDGER_XML_DATA,
    create_ledgger,
    zugfert_to_ledger_import,
)

from .database_retrieve_account_no import get_datev_account_no, mydb


class App:
    def __init__(self):
        self.pdf_path_list: dict[Path, LedgerImportWMetadata | None] = {}
        self._settings = Settings.getinstance()
        # tkinter GUI to select a file
        # pdf_path_list = ["a.pdf", "b.pdf"]

        self.main_window = Tk()

        # draw the window
        self.main_window.title("PDF Selector")
        self.main_window.geometry("2000x1000")

        self.tree = Treeview(
            self.main_window, columns=("xml_status", "date", "account_no")
        )
        self.tree.column("#0", width=150, minwidth=150)
        self.tree.column("xml_status", width=100, minwidth=100)
        self.tree.column("date", width=100, minwidth=100)
        self.tree.column("account_no", width=10, minwidth=10)

        self.tree.heading("#0", text="File Name", anchor="w")
        self.tree.heading("xml_status", text="xml", anchor="w")
        self.tree.heading("date", text="year/month", anchor="w")
        self.tree.heading("account_no", text="account no", anchor="w")

        self.tree.pack(side="top", fill="both", expand=True)

        # add listbox to show selected files

        # add import button
        import_button = Button(
            self.main_window, text="Import pdfs", command=self.import_pdfs
        )

        import_xml_button = Button(
            self.main_window, text="import xml folder", command=self.import_xmls
        )

        import_single_xml_button = Button(
            self.main_window, text="import single xml", command=self.import_single_xml
        )

        # add settings button that opens dialoge to change default paths
        settings_button = Button(
            self.main_window,
            text="Settings",
            command=self._settings.open_tk_settings_dialoge,
        )

        delete_button = Button(
            self.main_window,
            text="Delete selected",
            command=lambda: (
                [
                    self.pdf_path_list.pop(Path(item), None)
                    for item in self.tree.selection()
                ]
                and self.update_treeview()
            ),
        )

        button_inspect = Button(
            self.main_window, text="Inspect selected", command=self.inspect
        )

        button_xml_from_database = Button(
            self.main_window,
            text="import xml from database (selected)",
            command=self.import_xmls_from_database,
        )

        button_save = Button(
            self.main_window,
            text="Save",
            command=self.save,
        )

        import_button.pack(side="left", padx=4, pady=4)
        button_inspect.pack(side="left", padx=4, pady=4)
        import_xml_button.pack(side="left", padx=4, pady=4)
        import_single_xml_button.pack(side="left", padx=4, pady=4)
        button_xml_from_database.pack(side="left", padx=4, pady=4)
        delete_button.pack(side="left", padx=4, pady=4)
        button_save.pack(side="left", padx=4, pady=4)
        settings_button.pack(side="right", padx=4, pady=4)

    def save(self):
        if not self._settings.check_csv_settings():
            messagebox.showwarning(
                "Settings incomplete",
                "Please complete the settings needed for csv generation before saving.",
            )
            return

        for pdf, ledger in self.pdf_path_list.items():
            if ledger is None:
                messagebox.showwarning(
                    "Missing XML data",
                    f"The PDF {pdf.name} has no imported XML data. Please import XML data for all PDFs before saving.",
                )
                return

        pdf_path_list: dict[Path, LedgerImportWMetadataUUID] = {
            key: (value[0], value[1], uuid4())
            for key, value in cast(
                dict[Path, LedgerImportWMetadata], self.pdf_path_list
            ).items()
        }

        if len(pdf_path_list) == 0:
            messagebox.showwarning(
                "No data",
                "No PDFs to save. Please import PDFs before saving.",
            )
            return
        try:
            build_archive_and_save(pdf_path_list)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving: {e}")
            return
        messagebox.showinfo("Success", "Archive saved successfully.")

    def inspect(self):
        if len(self.tree.selection()) > 1:
            messagebox.showwarning(
                "Multiple selection",
                "Please select only one PDF to inspect.",
            )
            return
        if len(self.tree.selection()) == 0:
            messagebox.showwarning(
                "No selection",
                "Please select a PDF to inspect.",
            )
            return

        selected_pdf = Path(self.tree.selection()[0])
        selected_data = self.pdf_path_list[selected_pdf]

        if selected_data is None:
            messagebox.showwarning(
                "No XML data",
                "The selected PDF has no imported XML data to inspect.",
            )
            return

        inspector = XmlInspector(selected_pdf, selected_data)
        inspector.run()

    def update_treeview(self, delete: bool = True):
        if delete:
            self.tree.delete(*self.tree.get_children())
        for pdf, ledger in self.pdf_path_list.items():
            values = ("missing", "", "")
            if ledger is not None:
                account_number_attr = "no"
                curr_ledger = ledger[0].consolidate.ledgers[0]
                if (
                    isinstance(curr_ledger, AccountsReceivableLedger)
                    and curr_ledger.base1.base.account_no
                ):
                    account_number_attr = "yes"

                values = (
                    "Imported",
                    f"{ledger[1][0]}/{ledger[1][1]}",
                    account_number_attr,
                )

            self.tree.insert(
                "",
                END,
                iid=str(pdf),
                text=str(pdf),
                values=values,
            )

    def run(self):
        self.main_window.mainloop()

    def import_xmls_from_database(self) -> None:
        selected_rgs: list[str] = []
        for item in self.tree.selection():
            selected_rgs.append(Path(item).with_suffix("").name.removesuffix("_rg"))

        if len(selected_rgs) == 0:
            messagebox.showwarning(
                "No selection",
                "Please select at least one PDF to import the XML for.",
            )
            return

        placeholders = ", ".join(["%s"] * len(selected_rgs))
        sql = f"""
        SELECT k.DatevKtrNr, k.KdNme1, k.KdOrt, k.KdNr, r.RgNr, r.RgDat, r.RgBrutto, r.Par13
        FROM Rechnungen r
        JOIN Kunden k on r.Kdidx = k.KdIdx
        WHERE r.RgNr IN ({placeholders})
        """  # noqa: S608  # nosec
        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute(sql, tuple(selected_rgs))
        results = mycursor.fetchall()
        if not isinstance(results, list) or len(results) == 0:
            messagebox.showinfo(
                "No data",
                "No XML data found in database for the selected PDFs.",
            )
            return
        seller_tax_id = "DE163738087"
        for row in results:
            if not isinstance(row, dict) or len(row) < 7:
                messagebox.showwarning(
                    "Data error",
                    f"Unexpected data format from database: {row}",
                )
                continue
            issue_date_time = str(row["RgDat"])
            item_amount = str(row["RgBrutto"])
            buyer_id = str(row["KdNr"])
            invoice_id = str(row["RgNr"])
            if str(row["Par13"]) == "0":
                tax_rate = "19.00"
                bu_code = "3"
            else:
                tax_rate = "0.00"
                bu_code = "200"
            account_no_retrieval = get_datev_account_no
            ship_from_country = "DE"
            ship_to_country = "DE"
            due_date = None
            delivery_date = None
            order_id = None
            information_text = f"Ausgangsrechnung {invoice_id}"
            buyer_name: str = cast(str, row["KdNme1"])
            booking_text = buyer_name
            buyer_city = cast(str, row["KdOrt"])

            ledger_import_xml = LedgerImport(
                generator_info="Bombelczyk Aufzüge",
                xml_data=LEDGER_XML_DATA,
                consolidate=Consolidate(
                    # find document reference in /home/silas/Documents/coding/python/datev/.venv/lib/python3.13/site-packages/drafthorse/models/*
                    consolidated_amount=str(item_amount),
                    #             ExchangedDocument
                    # IssueDateTime
                    # DateTimeString
                    consolidated_date=issue_date_time,
                    consolidated_currency_code="EUR",
                    ledgers=[
                        create_ledgger(
                            issue_date_time=issue_date_time,
                            currency_code="EUR",
                            buyer_name=buyer_name,
                            buyer_city=buyer_city,
                            bp_account_no_retrieval=account_no_retrieval,
                            item_amount=item_amount,
                            buyer_id=buyer_id,
                            invoice_id=invoice_id,
                            bu_code=bu_code,
                            tax_rate=tax_rate,
                            seller_tax_id=seller_tax_id,
                            ship_from_country=ship_from_country,
                            buyer_tax_id=None,
                            ship_to_country=ship_to_country,
                            due_date=due_date,
                            delivery_date=delivery_date,
                            order_id=order_id,
                            information_text=information_text,
                            booking_text=booking_text,
                        )
                    ],
                    consolidated_invoice_id=invoice_id,
                    consolidated_delivery_date=None,
                    consolidated_order_id=None,
                ),
                generating_system=SOFTWARE_NAME,
            )
            saved = False
            for item in self.tree.selection():
                pdf_path = Path(item)
                rg_nr = pdf_path.with_suffix("").name.removesuffix("_rg")
                if rg_nr == str(row["RgNr"]):
                    self.pdf_path_list[pdf_path] = (
                        ledger_import_xml,
                        datetime.strptime(issue_date_time, "%Y-%m-%d").timetuple()[0:2],
                    )
                    saved = True
                    break
            if not saved:
                messagebox.showwarning(
                    "Could not save",
                    "Could not save document: " + str(row["RgNr"]),
                )
                continue
        self.update_treeview()

    @staticmethod
    def extract_xml_from_pdf(pdf: Path) -> Path | None:
        file_name = pdf.name
        # pdf = Path(file_name)
        reader = PdfReader(pdf)
        attachments = {}

        catalog = reader.trailer["/Root"]
        print(catalog)
        if "/Names" in catalog and "/EmbeddedFiles" in catalog["/Names"]:
            fileNames = catalog["/Names"]["/EmbeddedFiles"]["/Names"]
            for f in fileNames:
                print(f)
                if isinstance(f, str) and f == "factur-x.xml":
                    name = f
                    dataIndex = fileNames.index(f) + 1
                    fDict = fileNames[dataIndex].get_object()
                    fData = fDict["/EF"]["/F"].get_data()
                    attachments[name] = fData

                    tempdir_path = Path(tempfile.gettempdir()) / (file_name + ".xml")
                    with open(tempdir_path, "wb") as xml_file:
                        xml_file.write(fData)
                    return tempdir_path
        return None

    @staticmethod
    def import_x_rechnung(pdf: Path) -> LedgerImportWMetadata | None:
        print(f"Importing {pdf}")
        if not pdf.exists() or not pdf.is_file():
            messagebox.showerror(
                "File Error", f"The file {pdf} does not exist or is not a file."
            )
            return None

        xml_path = App.extract_xml_from_pdf(pdf)
        print(f"Extracted XML path: {xml_path}")
        if xml_path is not None and xml_path.exists():
            return zugfert_to_ledger_import(xml_path, get_datev_account_no)

        return None

    def import_pdfs(self) -> None:
        pdf_paths = askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=self._settings.pdf_path,
            # initialdir=Path.home(),
        )

        if len(pdf_paths) == 0:
            messagebox.showinfo("No files selected", "No PDF files were selected.")
            return
        # imported_pdfs: dict[Path, LedgerImportWMetadata | None] = {}
        for pdf in pdf_paths:
            pdf_path = Path(pdf)
            if pdf_path in self.pdf_path_list:
                messagebox.showwarning(
                    "Duplicate file",
                    f"The file {pdf_path.name} has already been imported. Skipping.",
                )
                continue
            # process the PDF file (placeholder for actual processing logic)
            self.pdf_path_list[pdf_path] = self.import_x_rechnung(pdf_path)

        self.update_treeview()

    def import_single_xml(self) -> None:
        if len(self.tree.selection()) > 1:
            messagebox.showwarning(
                "Multiple selection",
                "Please select only one PDF to import the XML for.",
            )
            return
        if len(self.tree.selection()) == 0:
            messagebox.showwarning(
                "No selection",
                "Please select a PDF to import the XML for.",
            )
            return

        selected_pdf = Path(self.tree.selection()[0])

        xml_file = askopenfilename(
            title="Select XML file",
            filetypes=[("XML files", "*.xml")],
            initialdir=self._settings.xml_folder,
            # initialdir=Path.home(),
        )
        if not xml_file:
            messagebox.showinfo("No file selected", "No XML file was selected.")
            return

        xml_path = Path(xml_file)
        if not xml_path.exists() or not xml_path.is_file():
            messagebox.showerror(
                "File Error", f"The file {xml_path} does not exist or is not a file."
            )
            return

        self.pdf_path_list[selected_pdf] = zugfert_to_ledger_import(
            xml_path, get_datev_account_no
        )
        self.update_treeview()

    def import_xmls(self) -> None:
        missing_xml: list[Path] = []
        for pdf in self.pdf_path_list:
            if self.pdf_path_list[pdf] is None:
                missing_xml.append(pdf)
        if len(missing_xml) == 0:
            messagebox.showinfo(
                "All files imported", "All PDFs have XML data. import not needed."
            )
            return

        xml_folder = Path(
            askdirectory(
                title="Select XML folder",
                initialdir=self._settings.xml_folder,
            )
            or ""
        )

        if not xml_folder.exists() or not xml_folder.is_dir():
            messagebox.showerror(
                "Directory Error", f"The directory {xml_folder} does not exist."
            )
            return

        missing_xmls = []

        for pdf in missing_xml:
            xml_file = xml_folder / (pdf.stem + ".xml")
            if not xml_file.exists():
                xml_file = xml_folder / (pdf.stem + "_rg" + ".xml")

            if not xml_file.exists() or not xml_file.is_file():
                missing_xmls.append(pdf.stem)
                continue
            self.pdf_path_list[pdf] = zugfert_to_ledger_import(
                xml_file, get_datev_account_no
            )

        if len(missing_xmls) > 0:
            file_str = ", ".join(f"({f}.xml {f}_rg.xml)" for f in missing_xmls)
            messagebox.showwarning(
                "Missing XML files",
                f"The following XML files were not found in the selected directory: {file_str}",
            )

        self.update_treeview(delete=True)
