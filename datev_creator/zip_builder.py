import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

from datev_creator.archive import Archive
from datev_creator.ledger_import import LedgerImport


def build_zip(
    archive: Archive,
    documents: Iterable[tuple[str, LedgerImport]],
    out_path: str | Path,
    other_files: Iterable[str | Path] = [],
):
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

        archive.xml.write(
            archive_xml_path, pretty_print=True, xml_declaration=True, encoding="utf-8"
        )

        datev_xml_files: list[Path] = []
        for file_name, ledger in documents:
            file = temp_dir / file_name
            datev_xml_files.append(file)
            ledger.xml.write(
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
