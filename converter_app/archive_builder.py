from datetime import datetime
from pathlib import Path
from tkinter.filedialog import asksaveasfilename
from typing import Mapping

from datev_creator.archive import (
    Archive,
    ArchiveContent,
    ArchiveDocument,
    ArchiveDocumentExtension,
    ArchiveDocumentExtensionProperty,
    ArchiveDocumentExtensionPropertyKey,
    ArchiveHeader,
    XsiType,
)
from datev_creator.csv_builder import build_csv
from datev_creator.ledger_import import LedgerImportWMetadata
from datev_creator.utils import SOFTWARE_NAME
from datev_creator.zip_builder import build_zip


def build_archive_and_save(data: Mapping[Path, LedgerImportWMetadata]):
    documents: list[ArchiveDocument] = []

    for pdf_file, (_, (year, month)) in data.items():
        ledger_file_name = pdf_file.with_suffix(".xml").name
        documents.append(
            ArchiveDocument(
                extension=[
                    ArchiveDocumentExtension(
                        xsi_type=XsiType.ACCOUNTS_RECEIVABLE_LEDGER,
                        property_=(
                            ArchiveDocumentExtensionProperty(
                                ArchiveDocumentExtensionPropertyKey.INVOICE_MONTH_FORMAT,
                                f"{year:04d}-{month:02d}",
                            ),
                            ArchiveDocumentExtensionProperty(
                                ArchiveDocumentExtensionPropertyKey.INVOICE_FOLDER,
                                "Kundenrechnungen",
                            ),
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

    csv_path_suggestion = zip_path.with_suffix(".csv")
    csv_path = Path(
        asksaveasfilename(
            title="Save CSV file",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=csv_path_suggestion.name,
            initialdir=csv_path_suggestion.parent,
        )
    )
    if not csv_path:
        print("No CSV file selected.")
        return

    build_csv(data, csv_path)

    try:
        build_zip(
            archive=archive_xml,
            documents=[
                (pdf.with_suffix(".xml").name, ledger[0])
                for pdf, ledger in data.items()
            ],
            out_path=zip_path,
            other_files=data.keys(),
        )
    except Exception as e:
        raise e
