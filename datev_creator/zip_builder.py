import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

from datev_creator.archive import Archive
from datev_creator.ledger_import import LedgerImport
from datev_creator.xml_validator import validate_xml


def build_zip(
    archive: Archive,
    documents: Iterable[tuple[str, LedgerImport]],
    out_path: str | Path,
    other_files: Iterable[str | Path] = [],
):
    """Builds zip file containing Datev Archive XML and LedgerImport XML files.

    Args:
        archive (Archive): _description_
        documents (Iterable[tuple[str, LedgerImport]]): _description_
        out_path (str | Path): _description_
        other_files (Iterable[str  |  Path], optional): _description_. Defaults to [].

    Raises:
        FileNotFoundError: if files not found
        e: if xml validation fails

    """
    if isinstance(out_path, str):
        out_path = Path(out_path)

    with tempfile.TemporaryDirectory() as d:
        temp_dir = Path(d)
        for file in other_files:
            if isinstance(file, str):
                file = Path(file)
            if not file.exists():
                raise FileNotFoundError(f"File does not exist: {file}")

        archive_xml_path = temp_dir / "document.xml"

        archive_xml_etree = archive.xml
        try:
            validate_xml(archive_xml_etree.getroot())
        except Exception as e:
            raise e

        archive_xml_etree.write(
            archive_xml_path, pretty_print=True, xml_declaration=True, encoding="utf-8"
        )

        datev_xml_files: list[Path] = []
        for file_name, ledger in documents:
            file = temp_dir / file_name
            datev_xml_files.append(file)
            ledger_xml_etree = ledger.xml
            try:
                validate_xml(ledger_xml_etree.getroot())
            except Exception as e:
                raise e
            ledger_xml_etree.write(
                file, pretty_print=True, xml_declaration=True, encoding="utf-8"
            )

        zip_content_paths = [
            *[Path(f) for f in other_files],
            archive_xml_path,
            *datev_xml_files,
        ]

        with zipfile.ZipFile(out_path, "w") as zipf:
            for file in zip_content_paths:
                zipf.write(file, file.name)
