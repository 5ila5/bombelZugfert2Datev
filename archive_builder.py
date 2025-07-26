from dataclasses import dataclass
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import (
    askopenfilenames,
    askdirectory,
    asksaveasfilename,
)
import tempfile
from datetime import datetime
from datev_creator import (
    Archive,
    ArchiveContent,
    ArchiveDocument,
    ArchiveDocumentExtension,
    ArchiveDocumentExtensionProperty,
    ArchiveDocumentExtensionPropertyKey,
    ArchiveHeader,
    XSI_Type,
    SOFTWARE_NAME,
    zugfert_to_ledger_import,
)

import zipfile
import sys


@dataclass
class ZipContents:
    """Class to hold the contents of a ZIP file."""

    pdf_paths: list[Path]
    xml_paths: list[Path]

    def __post_init__(self):
        """Ensure that the lists are initialized."""
        if not isinstance(self.pdf_paths, list) or not isinstance(self.xml_paths, list):
            raise TypeError("pdf_paths and xml_paths must be lists.")
        if len(self.pdf_paths) != len(self.xml_paths):
            raise ValueError("pdf_paths and xml_paths must have the same length.")


def main() -> None:
    # first arg = --debug
    debug = len(sys.argv) > 1 and sys.argv[1] == "--debug"

    # request user to select pdfs
    # open file dialog to select multiple PDF files

    Tk().withdraw()  # Hide the root window
    if debug:
        pdf_paths = ["testing/factur-x_rg.pdf"]
    else:
        pdf_paths = askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=Path.home(),
        )

    if len(pdf_paths) == 0:
        print("No PDF files selected.")
        return

    # ask user to select xml folder
    if debug:
        xml_folder = Path("testing/")
    else:
        xml_folder = Path(
            askdirectory(
                title="Select XML folder",
                initialdir=Path(pdf_paths[0]).parent,
            )
        )

    zugfert_xml_files: list[Path] = []
    datev_xml_files: list[tuple[Path, tuple[int, int]]] = []  # Path, year, month
    error = False

    for pdf in pdf_paths:
        # replace .pdf with .xml
        xml_file = xml_folder / Path(pdf).with_suffix(".xml").name
        if not xml_file.exists():
            print(f"XML file for {pdf} does not exist: {xml_file}")
            error = True
            continue
        zugfert_xml_files.append(xml_file)

    if error:
        return

    temp_dir = Path(tempfile.gettempdir())
    # pdf to temp dir
    temp_pdf_paths: list[Path] = []
    for pdf in pdf_paths:
        temp_pdf_path = temp_dir / Path(pdf).name
        temp_pdf_paths.append(temp_pdf_path)
        temp_pdf_path.write_bytes(Path(pdf).read_bytes())

    for xml_file in zugfert_xml_files:
        zugfert_xml, (year, month) = zugfert_to_ledger_import(xml_file)

        # Write the converted XML to a temporary file
        datev_xml_files.append((temp_dir / xml_file.name, (year, month)))
        zugfert_xml.write(
            temp_dir / xml_file.name,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

    documents: list[ArchiveDocument] = []

    for (xml_file, (year, month)), pdf_file in zip(datev_xml_files, temp_pdf_paths):
        documents.append(
            ArchiveDocument(
                extension=[
                    ArchiveDocumentExtension(
                        xsi_type=XSI_Type.accountsReceivableLedger,
                        property_=ArchiveDocumentExtensionProperty(
                            ArchiveDocumentExtensionPropertyKey.INVOICE_MONTH_FORMAT,
                            f"{year:04d}-{month:02d}",
                        ),
                        filename=xml_file.name,
                    ),
                    ArchiveDocumentExtension(
                        xsi_type=XSI_Type.File,
                        property_=None,
                        filename=pdf_file.name,
                    ),
                ],
                repository=None,
                guid=None,
                type=None,
                processID=None,
                description=None,
                keywords=None,
            )
        )

    archive_xml = Archive(
        header=ArchiveHeader(
            date=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            description=None,
            consultantNumber=None,
            clientNumber=None,
            clientName=None,
        ),
        content=ArchiveContent(documents),
        generatingSystem=SOFTWARE_NAME,
    )

    archive_xml_path = temp_dir / "document.xml"
    archive_xml.xml.write(
        archive_xml_path, pretty_print=True, xml_declaration=True, encoding="utf-8"
    )

    # ask zip save location
    if debug:
        zip_path = Path("testing/out/archive.zip")
    else:
        zip_path = Path(
            asksaveasfilename(
                title="Save ZIP file",
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip")],
                initialfile=f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            )
        )
    if not zip_path:
        print("No ZIP file selected.")
        return

    zip_content_paths: list[Path] = [
        archive_xml_path,
        *[a[0] for a in datev_xml_files],
        *temp_pdf_paths,
    ]

    # zip temp directory

    print(f"Creating ZIP file at {zip_path} for {zip_content_paths}")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in zip_content_paths:
            zipf.write(file, file.name)


if __name__ == "__main__":
    main()
