import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import (
    askdirectory,
    askopenfilenames,
    asksaveasfilename,
)
from typing import Literal

from datev_creator import (
    SOFTWARE_NAME,
    Archive,
    ArchiveContent,
    ArchiveDocument,
    ArchiveDocumentExtension,
    ArchiveDocumentExtensionProperty,
    ArchiveDocumentExtensionPropertyKey,
    ArchiveHeader,
    XsiType,
    zugfert_to_ledger_import,
)
from datev_creator.ledger_import import LedgerImport
from datev_creator.zip_builder import build_zip


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
        pdf_paths: tuple[str, ...] | Literal[""] = ("testing/factur-x_rg.pdf",)
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
    ledger_imports: list[
        tuple[tuple[str, LedgerImport], tuple[int, int]]
    ] = []  # file_name, LedgerImport, year, month
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
        ledger_imports.append(((xml_file.name, zugfert_xml), (year, month)))

    documents: list[ArchiveDocument] = []

    for ((ledger_file_name, _), (year, month)), pdf_file in zip(
        ledger_imports, temp_pdf_paths
    ):
        documents.append(
            ArchiveDocument(
                extension=[
                    ArchiveDocumentExtension(
                        xsi_type=XsiType.ACCOUNTS_RECEIVABLE_LEDGER,
                        property_=ArchiveDocumentExtensionProperty(
                            ArchiveDocumentExtensionPropertyKey.INVOICE_MONTH_FORMAT,
                            f"{year:04d}-{month:02d}",
                        ),
                        filename=ledger_file_name,
                    ),
                    ArchiveDocumentExtension(
                        xsi_type=XsiType.FILE,
                        property_=None,
                        filename=pdf_file.name,
                    ),
                ],
                repository=None,
                guid=None,
                type=None,
                process_id=None,
                description=None,
                keywords=None,
            )
        )

    archive_xml = Archive(
        header=ArchiveHeader(
            date=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            description=None,
            consultant_number=None,
            client_number=None,
            client_name=None,
        ),
        content=ArchiveContent(documents),
        generating_system=SOFTWARE_NAME,
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

    build_zip(
        archive=archive_xml,
        documents=[item[0] for item in ledger_imports],
        out_path=zip_path,
        other_files=temp_pdf_paths,
    )


if __name__ == "__main__":
    main()
