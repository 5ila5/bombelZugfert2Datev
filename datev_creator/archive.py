from dataclasses import dataclass
import enum
from typing import Literal, TypeAlias
from lxml import etree


DatafileOrName: TypeAlias = Literal["datafile", "name"]
oneToThree: TypeAlias = Literal["1", "2", "3"]


class XSI_Type(enum.Enum):
    accountsPayableLedger = "accountsPayableLedger"
    accountsReceivableLedger = "accountsReceivableLedger"
    cashLedger = "cashLedger"
    File = "File"
    Invoice = "Invoice"
    SEPAFile = "SEPAFile"

    @property
    def attribute(self) -> DatafileOrName:
        if self in (XSI_Type.File, XSI_Type.SEPAFile):
            return "datafile"
        else:
            return "name"


class ArchiveDocumentExtensionPropertyKey(enum.Enum):
    INVOICE_MONTH_FORMAT = "1"  # Rechnungsmonat Format "JJJJ-MM" z.B. "2020-02"
    CACHE_REGISTER_ACCOUNT_NUMBER = (
        "2"  #  Cache Legdger ONLY Kassenkontonummer z. B. „1000“1
    )
    INVOICE_FOLDER = "3"  # accounts (Payable/Receivable) Ledger: Bezeichnung des Rechnungsordners Default: Eingangsrechnungen1 / Cache Ledger: Kassenbezeichnung z. B. „Kasse Nürnberg Goho“ Default: Kasse1


@dataclass
class ArchiveDocumentExtensionProperty:
    """Die Propertys enthalten zusätzliche Metainformationen in Abhängigkeit vom xsi:type.

    | Bezeichnung | Typ      | Beschreibung                                         | Kardinalität |
    |-------------|----------|------------------------------------------------------|--------------|
    | key         | Enum     | Definiert eine bestimmte Inhaltsart                  | 1...1        |
    | value       | Attribut | Der konkrete Inhalt korrespondierend zum Attribut key | 1...1        |

    In der nachfolgenden Tabelle ist aufgelistet, welcher Wert im Attribut value für den jeweiligen key (1-3) in Abhängigkeit vom xsi:type erwartet wird.

    | Ausprägung                  | key="1"                          | key="2"                        | key="3"                                         |
    |-----------------------------|-----------------------------------|-------------------------------|--------------------------------------------------|
    | accountsPayableLedger       | Rechnungsmonat Format "JJJJ-MM"   | nicht verfügbar         | Bezeichnung des Rechnungsordners<br>Default: Eingangsrechnungen<sup>1</sup> |
    | accountsReceivableLedger    | Rechnungsmonat Format "JJJJ-MM"   | nicht verfügbar         | Bezeichnung des Rechnungsordners<br>Default: Ausgangsrechnungen<sup>1</sup> |
    | cashLedger<sup>2</sup>      | Transaktionsmonat Format "JJJJ-MM" | Kassenkontonummer<br>z. B. „1000“<sup>1</sup> | Kassenbezeichnung<br>z. B. „Kasse Nürnberg Goho“<br>Default: Kasse<sup>1</sup> |

    <sup>1</sup>Rechnungsordner, Kassenkontonummer und Kassenbezeichnung sind Werte, die der Kunde jeweils individuell in der jeweiligen DATEV App (Belege online/Kassenbuch online) konfigurieren kann. Bieten sie dem Kunden hier möglichst ein Eingabeparameter bei den Schnittstelleneinstellungen an.
    <sup>2</sup>Beim cashLedger darf nur key="2" oder key="3" verwendet werden.
    """

    key: ArchiveDocumentExtensionPropertyKey
    value: str


@dataclass
class ArchiveDocumentRepository:
    """Dieses Element definiert ein 3-stufiges Ablageverzeichnis und wird für Dateien vom Typ "File"/"SEPAFile" angewendet. Wird das Repository nicht explizit angegeben, dann werden die Dateien automatisch gemäß einer Default-Ablagestruktur abgelegt. Wird das Repository angegeben, werden die entsprechenden Verzeichnisse - sofern nicht schon vorhanden - zur Laufzeit in Belege online erzeugt.

    | Bezeichnung | Typ      | Beschreibung                                         | Kardinalität |
    |-------------|----------|------------------------------------------------------|--------------|
    | id          | Attribut | Ebene im Ablageverzeichnis                            | 3...3        |
    | name        | Attribut | Bezeichnung des Verzeichnisses                        |  3...3        |

    Das Attribut "id" lässt folgende Eingaben zu:

        "1" = entspricht dem Level "Kategorie" in Belege online
        "2" = entspricht dem Level "Ordner" in Belege online
        "3" = entspricht dem Level "Register" in Belege online

    Die Bezeichnung für das Attribut "name" ist frei wählbar. Wir empfehlen auf Level 1 nur eine konstante Bezeichnung pro generatingSystem (Softwarename) zu verwenden. Bei Level 2 und 3 können durchaus mehrere Begriffe verwendet werden. Die Default-Ablagestruktur sieht wie folgt aus:
    |Ausprägung|Kategorie|Ordner|Register|
    |---|---|---|---|
    |accountsPayableLedger |Buchführung |IMPORT JJJJ RE |MM Monatsname|
    |accountsReceivableLedger |Buchführung |IMPORT JJJJ RA |MM Monatsname|
    |cashLedger |Buchführung |IMPORT JJJJ KASSE |MM Monatsname|
    |invoice |Buchführung |IMPORT JJJJ |MM Monatsname|
    """

    id: tuple[oneToThree, oneToThree, oneToThree]  # 3..3
    name: tuple[str, str, str]  # 3..3


@dataclass
class ArchiveHeader:
    """
    | Bezeichnung       | Typ      | Beschreibung                                         | Kardinalität |
    |-------------------|----------|------------------------------------------------------|--------------|
    | date              | Element  | Erstellungsdatum der Datei                            | 1...1        |
    | description       | Element  | Freitext 255                                         | 0...1        |
    | consultantNumber  | Element  | Beraternummer | Verwendung nicht empfehlenswert         | 0...1        |
    | clientNumber      | Element  | Mandantennummer | Verwendung nicht empfehlenswert | 0...1        |
    | clientName       | Element  | Mandantenname | Verwendung nicht empfehlenswert     | 0...1        |
    """

    date: str
    description: str | None = None  # 255 chars
    consultantNumber: str | None = (
        None  # Beraternummer | Verwendung nicht empfehlenswert
    )
    clientNumber: str | None = None  # Mandantennummer | Verwendung nicht empfehlenswert
    clientName: str | None = None  # Mandantenname | Verwendung nicht empfehlenswert


@dataclass
class ArchiveDocumentExtension:
    """
    | Bezeichnung       | Typ      | Beschreibung                                         | Kardinalität |
    |-------------------|----------|------------------------------------------------------|--------------|
    | xsi:type          | Attribut | Definiert den Dateityp                                | 1...1        |
    | datafile or name  | Attribut | Abhängig vom xsi:type. Referenziert über den Dateinamen auf die Datei | 1...1        |
    | property          | Element  | Abhängig vom xsi:type                                | 0...2        |

    Der Attribut xsi:type kann verschiedene Ausprägungen annehmen. Abhängig davon muss entweder das Attribut datafile oder name übergeben werden. Desweiteren unterschieden sich auch die Inhalte des Elements property.

    | Ausprägung                  | Beschreibung                                           | Attribut |
    |-----------------------------|-------------------------------------------------------|----------|
    | accountsPayableLedger       | XML-Datei für Daten einer Eingangsrechnung             | datafile  |
    | accountsReceivableLedger    | XML-Datei für Daten einer Ausgangsrechnung            | datafile  |
    | cashLedger                  | XML-Datei für Daten einer Kasse                     | datafile  |
    | File                        | Datei, z.B. der Beleg<br>Zulässige Dateitypen: PDF, XML, TIF, TIFF, BMP, CSV, DOC, DOCX, GIF, JPEG, JPG, ODS, ODT, PKCS7, PNG, RTF, TXT, XLS, XLSX | name     |
    | Invoice                     | Eingangs-/Ausgangsrechnung                          | datafile  |
    | SEPAFile                    | SEPA/DTAUS-Dateien                                  | name     |
    """

    xsi_type: XSI_Type

    @property
    def datafile_or_name(self) -> DatafileOrName:
        return self.xsi_type.attribute

    property: (
        None
        | ArchiveDocumentExtensionProperty
        | tuple[ArchiveDocumentExtensionProperty]
        | tuple[ArchiveDocumentExtensionProperty, ArchiveDocumentExtensionProperty]
    ) = None  # 0..2


@dataclass
class ArchiveDocument:
    """
    | Bezeichnung       | Typ      | Beschreibung                                         | Kardinalität |
    |-------------------|----------|------------------------------------------------------|--------------|
    | extension         | Element  | Definiert den Typ der Datei                           | 1...50 |
    | repository        | Element  | Definiert ein Ablageverzeichnis für die Dateien des Elements | 0...1 |
    | guid              | Attribut | GUID/UUID gem. RFC 4122 | GUID wird verwendet um den Beleg mit dieser ID im DATEV Rechenzentrum abzulegen | Kann dazu verwendet werden, um Belegverlinkungen über DATEV Rechnungswesen aufzubauen | extension vom Typ "File" erforderlich | 0...1 |
    | type              | Attribut | Belegkreis Eingangsrechnung/Ausgangsrechnung | 0...1 |
    | processID         | Attribut | Verarbeitungskennzeichen | 1 = Belege im Posteingang ablegen, Repository wird ignoriert, nur möglich wenn keine Daten-XML enthalten ist | 2 = Belege in Ablageverzeichnis/Repository einsteuern | 0...1 |
    | description       | Element  | Beschreibung des Dokuments                           | 0...1 |
    | keywords          | Element  | Schlüsselwörter zum Dokument | Notiz              | 0...1
    """

    extension: list[ArchiveDocumentExtension]  # 1..50
    repository: ArchiveDocumentRepository | None = None
    guid: str | None = None
    type: str | None = None
    processID: str | None = None
    description: str | None = None
    keywords: str | None = None


@dataclass
class ArchiveContent:
    """| Bezeichnung       | Typ      | Beschreibung                                         | Kardinalität |
    |-------------------|----------|------------------------------------------------------|--------------|
    |document| 	Element| 	Die Entität für ein Dokument (z.B. eine Rechnung).| 	1...5000|"""

    document: list[ArchiveDocument]


@dataclass
class Archive:
    header: ArchiveHeader
    content: ArchiveContent
    xmlns: str = "http://xml.datev.de/bedi/tps/document/v06.0"
    xmlns_xsi: Literal["http://www.w3.org/2001/XMLSchema-instance"] = (
        "http://www.w3.org/2001/XMLSchema-instance"
    )
    xsi_schemaLocation: str = (
        "http://xml.datev.de/bedi/tps/document/v06.0 Document_v060.xsd"
    )
    version: str = "6.0"
    generatingSystem: str | None = None


def build_archive_header_xml(header: ArchiveHeader) -> etree._Element:
    xml: etree._Element = etree.Element("header", None, None)
    etree.SubElement(xml, "date", None, None).text = header.date

    if header.description is not None:
        etree.SubElement(xml, "description", None, None).text = header.description[:255]
    if header.consultantNumber is not None:
        etree.SubElement(
            xml, "consultantNumber", None, None
        ).text = header.consultantNumber
    if header.clientNumber is not None:
        etree.SubElement(xml, "clientNumber", None, None).text = header.clientNumber
    if header.clientName is not None:
        etree.SubElement(xml, "clientName", None, None).text = header.clientName

    return xml


def build_archive_content_document_extension_xml(extension: ArchiveDocumentExtension):
    attributes: dict[str, str] = {
        "xsi:type": extension.xsi_type.value,
        extension.xsi_type.attribute: extension.datafile_or_name,
    }

    xml: etree._Element = etree.Element(
        "document",
        attrib=attributes,
        nsmap=None,
    )

    props: list[ArchiveDocumentExtensionProperty] = []
    if isinstance(extension.property, ArchiveDocumentExtensionProperty):
        props = [extension.property]
    elif isinstance(extension.property, tuple):
        props = list(extension.property)

    for prop in props:
        etree.SubElement(
            xml,
            "property",
            attrib={"value": prop.value, "key": prop.key.value},
            nsmap=None,
        )

    return xml


def build_archive_content_document_xml(document: ArchiveDocument) -> etree._Element:
    attributes: dict[str, str] = {}

    if document.guid is not None:
        attributes["guid"] = document.guid
    if document.type is not None:
        attributes["type"] = document.type
    if document.processID is not None:
        attributes["processID"] = document.processID
    if document.description is not None:
        attributes["description"] = document.description
    if document.keywords is not None:
        attributes["keywords"] = document.keywords

    xml: etree._Element = etree.Element(
        "document",
        attrib=attributes,
        nsmap=None,
    )
    for ext in document.extension:
        xml.append(build_archive_content_document_extension_xml(ext))

    if document.repository is not None:
        repository_xml = etree.SubElement(xml, "repository", None, None)
        for i in range(3):
            etree.SubElement(
                repository_xml,
                "level",
                attrib={
                    "id": document.repository.id[i],
                    "name": document.repository.name[i],
                },
                nsmap=None,
            )

    return xml


def build_archive_content_xml(content: ArchiveContent) -> etree._Element:
    xml: etree._Element = etree.Element("content", attrib=None, nsmap=None)
    for doc in content.document:
        xml.append(build_archive_content_document_xml(doc))

    return xml


def build_archive_xml(archive: Archive) -> etree._Element:
    xml: etree._Element = etree.Element(
        "archive",
        attrib={
            "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": "http://xml.datev.de/bedi/tps/document/v06.0 Document_v060.xsd",
            "version": "6.0",
        },
        nsmap={
            None: "http://xml.datev.de/bedi/tps/document/v06.0",  # Default namespace
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        },
    )
    # Set the xsi:schemaLocation attribute (must use full QName)
    xml.append(build_archive_header_xml(archive.header))
    xml.append(build_archive_content_xml(archive.content))
    # Set version attribute
    return xml
