# xsd zips

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import requests
from lxml import etree  # nosec B410

xsd_zip = "https://developer.datev.de/assets/XSD_3c866dbe96.zip"
# check if xsd folder exists
xsd_folder = Path(__file__).parent / "xsd"
if not xsd_folder.exists():
    xsd_folder.mkdir(parents=True, exist_ok=True)
    # download and unzip
    try:
        response = requests.get(xsd_zip, timeout=10)
        with ZipFile(BytesIO(response.content)) as thezip:
            thezip.extractall(xsd_folder)
    except Exception as e:
        xsd_folder.rmdir()
        raise e
    print(f"Downloaded and extracted XSD files to {xsd_folder}")


def validate_xml(xml_elem: etree._Element) -> bool:
    # xml_elem already contains information like "xsi:schemaLocation="http://xml.datev.de/bedi/tps/ledger/v060 Belegverwaltung_online_ledger_import_v060.xsd"" now load the xsd from the xsd folder
    schema_location = xml_elem.attrib.get(
        "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
    )
    if not schema_location:
        raise ValueError("No schemaLocation found in XML")
    # schema_location is a string with two parts, the second part is the xsd file name
    parts = schema_location.split()
    if len(parts) != 2:
        raise ValueError("Invalid schemaLocation format")
    xsd_file_name = parts[1]
    xsd_file_path = xsd_folder / xsd_file_name
    if not xsd_file_path.exists():
        raise FileNotFoundError(f"XSD file {xsd_file_path} not found")
    with open(xsd_file_path, "rb") as f:
        xsd_doc = etree.parse(f)  # noqa: S320 # nosec B320
        xmlschema = etree.XMLSchema(xsd_doc)
        is_valid = xmlschema.validate(xml_elem)
        if not is_valid:
            log = xmlschema.error_log
            raise ValueError(f"XML validation error: {log.last_error}")
        return True
