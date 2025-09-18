import csv
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import IntEnum
from io import StringIO
from pathlib import Path
from typing import Literal, Mapping

from converter_app.settings import Settings
from datev_creator.ledger_import import (
    AccountsReceivableLedger,
    LedgerImport,
    LedgerImportWMetadata,
)


class Buchungstyp(IntEnum):
    FINANZBUCHFUEHRUNG = 1
    JAHRESABSCHLUSS = 2

    def __str__(self):
        return f"{self.value} - {self.name}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


class Rechnungslegungszweck(IntEnum):
    UNABHAENGIG = 0
    STEUERRECHT = 30
    KALKULATORIK = 40
    HANDELSRECHT = 50
    IFRS = 64

    def __str__(self):
        return f"{self.value} - {self.name}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


class FormatCategory(IntEnum):
    r"""The FormatCategory enum represents the different format categories for DATEV CSV files."""

    # 16 = Debitoren/Kreditoren
    # 20 = Sachkontenbeschriftungen
    # 21 = Buchungsstapel
    # 46 = Zahlungsbedingungen
    # 48 = Diverse Adressen
    # 65 = Wiederkehrende Buchungen
    DEBITORS_CREDITORS = 16
    ACCOUNT_DESCRIPTIONS = 20
    BOOKING_BATCH = 21
    PAYMENT_TERMS = 46
    MISC_ADDRESSES = 48
    RECURRING_BOOKINGS = 65

    def get_name(self):
        """Returns the name of the category.

        ^["](Buchungsstapel|Wiederkehrende Buchungen|Debitoren/Kreditoren|Kontenbeschriftungen|Zahlungsbedingungen|Diverse Adressen)["]$
        """
        match self:
            case FormatCategory.DEBITORS_CREDITORS:
                return "Debitoren/Kreditoren"
            case FormatCategory.ACCOUNT_DESCRIPTIONS:
                return "Kontenbeschriftungen"
            case FormatCategory.BOOKING_BATCH:
                return "Buchungsstapel"
            case FormatCategory.PAYMENT_TERMS:
                return "Zahlungsbedingungen"
            case FormatCategory.MISC_ADDRESSES:
                return "Diverse Adressen"
            case FormatCategory.RECURRING_BOOKINGS:
                return "Wiederkehrende Buchungen"
            case _:
                raise ValueError(f"Unknown FormatCategory: {self}")

    def get_format_version(self):
        """Returns the format version the category.

        5 = Debitoren-/Kreditoren
        3 = Sachkontenbeschriftungen
        13 = Buchungsstapel
        2 = Zahlungsbedingungen
        4 = Wiederkehrende Buchungen
        2 = Diverse Adressen
        """
        match self:
            case FormatCategory.DEBITORS_CREDITORS:
                return 5
            case FormatCategory.ACCOUNT_DESCRIPTIONS:
                return 3
            case FormatCategory.BOOKING_BATCH:
                return 13
            case FormatCategory.PAYMENT_TERMS:
                return 2
            case FormatCategory.MISC_ADDRESSES:
                return 2
            case FormatCategory.RECURRING_BOOKINGS:
                return 4
            case _:
                raise ValueError(f"Unknown FormatCategory: {self}")

    def __str__(self):
        return f"{self.value} - {self.get_name()}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


@dataclass
class Header:
    """Header information."""

    herkunft: str
    exportiert_von: str
    importiert_von: str
    berater_nummer: int
    mandant_nummer: int
    wj_beginn: date
    sachkontenlaenge: int  # 4-8
    datum_von: date
    datum_bis: date
    bezeichnung: str
    erzeugt_am: date
    buchungstyp: Buchungstyp  # 1 = Finanzbuchführung (default), 2 = Jahresabschluss
    rechnungslegungszweck: Rechnungslegungszweck
    kennzeichen: Literal["EXTF", "DTVF"] = "EXTF"  # Third party
    """
    EXTF = Export aus 3rd-Party App
    DTVF = Export aus DATEV App
    """

    version: str = "700"
    format_kategory: FormatCategory = FormatCategory.BOOKING_BATCH
    formatname: str = FormatCategory.get_name(FormatCategory.BOOKING_BATCH)
    formatversion: int = FormatCategory.get_format_version(FormatCategory.BOOKING_BATCH)
    imported: None = None  # always None
    diktatkuerzel: str | None = None  # max 2 uppercase letters
    festschreibung: Literal[0, 1] = (
        1  # 0 = keine Festschreibung, 1 = Festschreibung (default)
    )
    wkz: str = "EUR"  # ISO-Code der Währung, "EUR" = default
    reserviert_1: None = None  # always None
    derivatskennzeichen: None = None  # always None
    reserviert_2: None = None  # always None
    reserviert_3: None = None  # always None
    sachkontenrahmen: str | None = (
        None  # Sachkontenrahmen, der für die Bewegungsdaten verwendet wurde
    )
    id_der_branchenloesung: str | None = (
        None  # Falls eine spezielle DATEV Branchenlösung genutzt wird
    )
    reserviert_4: None = None  # always None
    reserviert_5: None = None  # always None
    anwendungsinformation: str | None = (
        None  # Verarbeitungskennzeichen der abgebenden Anwendung, z.B. 02/2024
    )

    def to_csv_herder(self) -> str:
        data_list = [
            f'"{self.kennzeichen}"',
            self.version,
            str(self.format_kategory.value),
            f'"{self.formatname}"',
            str(self.formatversion),
            self.erzeugt_am.strftime("%Y%m%d%H%M%S000"),
            "",
            f'"{self.herkunft}"',
            f'"{self.exportiert_von}"',
            f'"{self.importiert_von}"',
            str(self.berater_nummer),
            str(self.mandant_nummer),
            self.wj_beginn.strftime("%Y%m%d"),
            str(self.sachkontenlaenge),
            self.datum_von.strftime("%Y%m%d"),
            self.datum_bis.strftime("%Y%m%d"),
            f'"{self.bezeichnung}"',
            f'"{self.diktatkuerzel or ""}"',
            str(self.buchungstyp.value),
            str(self.rechnungslegungszweck.value),
            str(self.festschreibung),
            f'"{self.wkz}"',
            "",
            '""'
            if self.derivatskennzeichen is None
            else f'"{self.derivatskennzeichen}"',
            "",
            "",
            f'"{self.sachkontenrahmen or ""}"',
            self.id_der_branchenloesung or "",
            "",
            '""' if self.reserviert_5 is None else f'"{self.reserviert_5}"',
            f'"{self.anwendungsinformation or ""}"',
        ]

        return ";".join(data_list)

    @staticmethod
    def from_csv_header(data: str):
        split_data = data.split(";")

        if len(split_data) > 31:
            if any(d.strip() != "" for d in split_data[31:]):
                raise ValueError(f"Invalid header length: {len(split_data)}")
            split_data = split_data[:31]

        if len(split_data) != 31:
            raise ValueError(f"Invalid header length: {len(split_data)}")

        kennzeichen = split_data[0].strip('"')
        if kennzeichen not in ("EXTF", "DTVF"):
            raise ValueError(f"Invalid kennzeichen: {kennzeichen}")

        festschreibung = int(split_data[20])
        if festschreibung not in (0, 1):
            raise ValueError(f"Invalid festschreibung: {festschreibung}")

        # check if None arguments are actually empty strings
        for i in [6, 22, 23, 24, 25, 28, 29]:
            if split_data[i] != "":
                # raise ValueError(
                #     f"Invalid value for reserved field at position {i + 1}: {split_data[i]}"
                # )
                print(f"Warning: Reserved field at position {i + 1} is not empty.")

        return Header(
            kennzeichen="EXTF" if kennzeichen == "EXTF" else "DTVF",
            version=split_data[1],
            format_kategory=FormatCategory(int(split_data[2])),
            formatname=split_data[3].strip('"'),
            formatversion=int(split_data[4]),
            # erzeugt_am=datetime.strptime(split_data[5], "%Y%m%d%H%M%S000").date(),
            erzeugt_am=datetime.strptime(split_data[5], "%Y%m%d%H%M%S%f").date(),
            imported=None,
            herkunft=split_data[7].strip('"'),
            exportiert_von=split_data[8].strip('"'),
            importiert_von=split_data[9].strip('"'),
            berater_nummer=int(split_data[10]),
            mandant_nummer=int(split_data[11]),
            wj_beginn=datetime.strptime(split_data[12], "%Y%m%d").date(),
            sachkontenlaenge=int(split_data[13]),
            datum_von=datetime.strptime(split_data[14], "%Y%m%d").date(),
            datum_bis=datetime.strptime(split_data[15], "%Y%m%d").date(),
            bezeichnung=split_data[16].strip('"'),
            diktatkuerzel=split_data[17].strip('"') or None,
            buchungstyp=Buchungstyp(int(split_data[18])),
            rechnungslegungszweck=Rechnungslegungszweck(int(split_data[19])),
            festschreibung=0 if festschreibung == 0 else 1,
            wkz=split_data[21].strip('"'),
            reserviert_1=None,
            derivatskennzeichen=None,
            reserviert_2=None,
            reserviert_3=None,
            sachkontenrahmen=split_data[26].strip('"') or None,
            id_der_branchenloesung=split_data[27] or None,
            reserviert_4=None,
            reserviert_5=None,
            anwendungsinformation=split_data[30].strip('"') or None,
        )

    def __repr__(self) -> str:
        return f"Header(kennzeichen={self.kennzeichen!r}, version={self.version!r}, format_kategory={self.format_kategory!r}, formatname={self.formatname!r}, formatversion={self.formatversion!r}, erzeugt_am={self.erzeugt_am!r}, imported={self.imported!r}, herkunft={self.herkunft!r}, exportiert_von={self.exportiert_von!r}, importiert_von={self.importiert_von!r}, berater_nummer={self.berater_nummer!r}, mandant_nummer={self.mandant_nummer!r}, wj_beginn={self.wj_beginn!r}, sachkontenlaenge={self.sachkontenlaenge!r}, datum_von={self.datum_von!r}, datum_bis={self.datum_bis!r}, bezeichnung={self.bezeichnung!r}, diktatkuerzel={self.diktatkuerzel!r}, buchungstyp={self.buchungstyp!r}, rechnungslegungszweck={self.rechnungslegungszweck!r}, festschreibung={self.festschreibung!r}, wkz={self.wkz!r}, reserviert_1={self.reserviert_1!r}, derivatskennzeichen={self.derivatskennzeichen!r}, reserviert_2={self.reserviert_2!r}, reserviert_3={self.reserviert_3!r}, sachkontenrahmen={self.sachkontenrahmen!r}, id_der_branchenloesung={self.id_der_branchenloesung!r}, reserviert_4={self.reserviert_4!r}, reserviert_5={self.reserviert_5!r}, anwendungsinformation={self.anwendungsinformation})"


@dataclass
class BuchungsstapelItem:
    r"""BuchungsstapelItem represents a single line in the CSV file after the headers.

    |#|Überschrift|Ausdruck|Beschreibung|
    |-|-|-|-|
    |1|Umsatz|^(?!0{1,10}\,00)\d{1,10}\,\d{2}$|Umsatz/Betrag für den Datensatz.Betrag muss positiv und darf nicht 0,00 sein.Beispiel: 1234567890,12|
    |2|Soll-/Haben-Kennzeichen|^["](S|H)["]$|Soll-/Haben-Kennzeichnungbezieht sich auf das Feld #7KontoS = SOLL (default)H = HABEN|
    |3|WKZ Umsatz|^["]([A-Z]{3})["]$|ISO-Code der Währung#22 aus Header = defaultListe der ISO-Codes|
    |4|Kurs|^([1-9]\d{0,3}[,]\d{2,6})$|Wenn ein Umsatz in der Fremdwährung bei #1 angegeben wird, sind #4, #5 und #6 zu übergeben.Der Fremdwährungskurs (WKZ-Umsatz : WKZ-Basisumsatz) bestimmt, wie der angegebene Umsatz, der in Fremdwährung übergeben wird, in die Basiswährung umzurechnen ist, wenn es sich um ein Nicht-EWU-Land handelt.Beispiel: 1234,123456Achtung: Der Wert 0 ist unzulässig.|
    |5|Basisumsatz|^(?!0{1,10}\,00)\d{1,10}\,\d{2}$|Wenn das Feld Basisumsatz verwendet wird, muss auch das Feld WKZ Basisumsatz gefüllt werden.Beispiel: 1123123123,12|
    |6|WKZ Basisumsatz||Währungskennzeichen der hinterlegten Basiswährung. Wenn das Feld WKZ Basisumsatz verwendet wird, muss auch das Feld Basisumsatz verwendet werden.ISO-Code beachten (siehe Dok.-Nr.1080170)|
    |7|Konto|^(?!0{1,9}$)(\d{1,9})$|Sach- oder PersonenkontoBeispiel: 4400Darf max. 8- bzw. max. 9-stellig sein (abhängig von der im Bestand genutzten Sachkontonummernlänge).Die Personenkontenlänge darf nur 1 Stelle länger sein als die definierte Sachkontennummernlänge.|
    |8|Gegenkonto (ohne BU-Schlüssel)|^(?!0{1,9}$)(\d{1,9})$|Sach- oder PersonenkontoBeispiel: 70000Darf max. 8- bzw. max. 9-stellig sein (abhängig von der im Bestand genutzten Sachkontonummernlänge).Die Personenkontenlänge darf nur 1 Stelle länger sein als die definierte Sachkontennummernlänge.|
    |9|BU-Schlüssel|^(["]\d{4}["])$|Steuerungskennzeichen zur Abbildung verschiedener Funktionen/SachverhalteWeitere Details|
    |10|Belegdatum|^(\d{4})$|Format: TTMMBeispiel: 0105Das Jahr wird immer ausdem Feld #13 desHeadersermittelt.|
    |11|Belegfeld 1|^(["][\w$%\-\/]{0,36}["])$|Rechnungs-/BelegnummerWird als "Schlüssel" für den Ausgleich offener Rechnungen genutzt.Beispiel: Rg32029/2024Sonderzeichen: $ & % * + - /Andere Zeichen sind unzulässig (insbesondere Leerzeichen,Umlaute, Punkt, Komma, Semikolon und Doppelpunkt).|
    |12|Belegfeld 2|^(["][\w$%\-\/]{0,12}["])$|Belegnummer oder OPOS-Verarbeitungsinformationen wie FälligkeitsdatumFormat: TTMMJJ(siehe Dok.-Nr.9211385)|
    |13|Skonto|^([1-9]\d{0,7}[,]\d{2})$|Skonto-Betrag/-AbzugNur bei Zahlungen zulässig.Beispiel: 12123123,12Achtung: Der Wert 0 ist unzulässig.|
    |14|Buchungstext|^(["].{0,60}["])$|0-60 Zeichen|
    |15|Postensperre|^(0|1)$|Mahn- oder Zahlsperre0 = keine Sperre (default)1 = SperreDie Rechnung kann aus dem Mahnwesen / Zahlungsvorschlagausgeschlossen werden.|
    |16|Diverse Adressnummer|^(["]\w{0,9}["])$|Nur in Verbindung mit OPOS relevant.Adressnummer einer diversen Adresse.|
    |17|Geschäftspartnerbank|^(\d{3})$|Nur in Verbindung mit OPOS relevant.Wenn für eine Lastschrift oder Überweisung eine bestimmte Bank des Geschäftspartners genutzt werden soll. Beim Import der Geschäftspartnerbank muss immer auch das Feld SEPA-Mandatsreferenz (Feld-Nr. 105) gefüllt sein|
    |18|Sachverhalt|^(\d{2})$|Nur in Verbindung mit OPOS relevant.Kennzeichen für einen Mahnzins/Mahngebühr-Datensatz31 = Mahnzins40 = Mahngebühr|
    |19|Zinssperre|^(0|1)$|Nur in Verbindung mit OPOS relevant.Sperre für Mahnzinsen0 = keine Sperre (default)1 = Sperre|
    |20|Beleglink|Generell:^(["].{0,210}["])$Konkret für Link in eine DATEV App:^["](BEDI|DDMS|DORG)[ ]["]["][<GUID>]["]["]["]$|Link auf den Buchungsbeleg, der digital in einem Dokumenten-Management-System (z. B. Dokumentenablage, DATEV DMS) abgelegt wurde.BEDI = Unternehmen onlineDer Beleglink besteht aus einem Programmkürzel und der GUID.Da das Feld Beleglink ein Textfeld ist, müssen in der Schnittstellendatei die Anführungszeichen verdoppelt werden.Beispiel: "BEDI ""E0A08953-FBAA-4054-AF36-993D5D68F040""\"|
    |21|Beleginfo-Art 1|^(["].{0,20}["])$|Bei einem DATEV-Format, das aus einem DATEV-Rechnungswesen-Programm erstellt wurde, können diese Felder Informationen aus einem Beleg (z. B. einem elektronischen Kontoumsatz) enthalten. Wenn die Feldlänge eines Beleginfo-Inhalts-Feldes überschritten wird, wird die Information im nächsten Beleginfo-Feld weitergeführt.Wichtiger Hinweis:Eine Beleginfo besteht immer aus den Bestandteilen Beleginfo-Art und Beleginfo-Inhalt. Wenn Sie die Beleginfo nutzen möchten, befüllen Sie bitte immer beide Felder.Beispiel:Beleginfo-Art:Kontoumsätze der jeweiligen BankBeleginfo-Inhalt:Buchungsspezifische Inhalte zu den oben genannten Informationsarten|
    |22|Beleginfo-Inhalt 1|^(["].{0,210}["])$|siehe #21|
    |23|Beleginfo-Art 2|^(["].{0,20}["])$|siehe #21|
    |24|Beleginfo-Inhalt 2|^(["].{0,210}["])$|siehe #21|
    |25|Beleginfo-Art 3|^(["].{0,20}["])$|siehe #21|
    |26|Beleginfo-Inhalt 3|^(["].{0,210}["])$|siehe #21|
    |27|Beleginfo-Art 4|^(["].{0,20}["])$|siehe #21|
    |28|Beleginfo-Inhalt 4|^(["].{0,210}["])$|siehe #21|
    |29|Beleginfo-Art 5|^(["].{0,20}["])$|siehe #21|
    |30|Beleginfo-Inhalt 5|^(["].{0,210}["])$|siehe #21|
    |31|Beleginfo-Art 6|^(["].{0,20}["])$|siehe #21|
    |32|Beleginfo-Inhalt 6|^(["].{0,210}["])$|siehe #21|
    |33|Beleginfo-Art 7|^(["].{0,20}["])$|siehe #21|
    |34|Beleginfo-Inhalt 7|^(["].{0,210}["])$|siehe #21|
    |35|Beleginfo-Art 8|^(["].{0,20}["])$|siehe #21|
    |36|Beleginfo-Inhalt 8|^(["].{0,210}["])$|siehe #21|
    |37|KOST1-Kostenstelle|^(["][\w ]{0,36}["])$|Über KOST1 erfolgt die Zuordnung des Geschäftsvorfalls für die anschließende Kostenrechnung. Die benutzte Länge muss vorher in den Stammdaten vom KOST-Programm eingestellt werden.|
    |38|KOST2-Kostenstelle|^(["][\w ]{0,36}["])$|Über KOST2 erfolgt die Zuordnung des Geschäftsvorfalls für die anschließende Kostenrechnung. Die benutzte Länge muss vorher in den Stammdaten vom KOST-Programm eingestellt werden.|
    |39|KOST-Menge|^\d{12}[,]\d{4}$|Im KOST-Mengenfeld wird die Wertgabe zu einer bestimmten Bezugsgröße für eine Kostenstelle erfasst. Diese Bezugsgröße kann z. B. kg, g, cm, m, % sein. Die Bezugsgröße ist definiert in den Kostenrechnungs-Stammdaten.Beispiel: 123123123,1234|
    |40|EU-Mitgliedstaat u. UStID (Bestimmung)|^(["].{0,15}["])$|Die USt-IdNr. besteht aus2-stelligen Länderkürzel (siehe Dok.-Nr.1080169)Ausnahmen:Griechenland = ELNordirland = XImax. 13-stelliger USt-IdNr.Beispiel: DE133546770Die USt-IdNr. kann auch Buchstaben haben, z.B. bei Österreich.Detaillierte Informationen zur Erfassung von EU-Informationen im Buchungssatz siehe Dok.-Nr.9211462.|
    |41|EU-Steuersatz (Bestimmung)|^\d{2}[,]\d{2}$|Nur für entsprechende EU-Buchungen:Der im EU-Bestimmungsland gültige Steuersatz.Beispiel: 12,12|
    |42|Abw. Versteuerungsart|^(["](I|K|P|S)["])$|Für Buchungen, die in einer von der Mandantenstammdaten-Schlüsselung abweichenden Umsatzsteuerart verarbeitet werden sollen,kann die abweichende Versteuerungsart im Buchungssatz übergeben werden:I = Ist-VersteuerungK = keine UmsatzsteuerrechnungP = Pauschalierung (z. B. für Land- und Forstwirtschaft)S = Soll-Versteuerung|
    |43|Sachverhalt L+L|^(\d{1,3})$|Sachverhalte gem. § 13b Abs. 1 und 2 UStGAchtung: Der Wert 0 ist unzulässig.Wenn erforderlich, Feld 119 zusätzlich verwenden.(siehe Kapitel 6 in Dok.-Nr.1034915und1003613)|
    |44|Funktionsergänzung L+L|^\d{0,3}$|Nur bei SKR07 Österreich:Steuersatz / Funktion zum L+L-SachverhaltAchtung: Der Wert 0 ist unzulässig.Beispiel: Wert 130 für 13%|
    |45|BU 49 Hauptfunktiontyp|^\d$|Bei Verwendung des BU-Schlüssels 49 für „andere Steuersätze“ muss der steuerliche Sachverhalt mitgegeben werden.|
    |46|BU 49 Hauptfunktionsnummer|^\d{0,2}$|siehe #45|
    |47|BU 49 Funktionsergänzung|^\d{0,3}$|siehe #45|
    |48|Zusatzinformation – Art 1|^(["].{0,20}["])$|Zusatzinformationen, die zu Buchungssätzen erfasst werden können. Diese Zusatzinformationen besitzen den Charakter eines Notizzettels und können frei erfasst werden.Wichtiger Hinweis:Eine Zusatzinformation besteht immer aus den Bestandteilen Informationsart und Informationsinhalt. Wenn Sie die Zusatzinformation nutzen möchten, füllen Sie bitte immer beide Felder.Beispiel:Informationsart: Filiale oder Mengengrößen (qm)Informationsinhalt: buchungsspezifische Inhalte zu den oben genannten Informationsarten.|
    |49|Zusatzinformation – Inhalt 1|^(["].{0,210}["])$|siehe #48|
    |50|Zusatzinformation – Art 2|^(["].{0,20}["])$|siehe #48|
    |51|Zusatzinformation – Inhalt 2|^(["].{0,210}["])$|siehe #48|
    |52|Zusatzinformation – Art 3|^(["].{0,20}["])$|siehe #48|
    |53|Zusatzinformation – Inhalt 3|^(["].{0,210}["])$|siehe #48|
    |54|Zusatzinformation – Art 4|^(["].{0,20}["])$|siehe #48|
    |55|Zusatzinformation – Inhalt 4|^(["].{0,210}["])$|siehe #48|
    |56|Zusatzinformation – Art 5|^(["].{0,20}["])$|siehe #48|
    |57|Zusatzinformation – Inhalt 5|^(["].{0,210}["])$|siehe #48|
    |58|Zusatzinformation – Art 6|^(["].{0,20}["])$|siehe #48|
    |59|Zusatzinformation – Inhalt 6|^(["].{0,210}["])$|siehe #48|
    |60|Zusatzinformation – Art 7|^(["].{0,20}["])$|siehe #48|
    |61|Zusatzinformation – Inhalt 7|^(["].{0,210}["])$|siehe #48|
    |62|Zusatzinformation – Art 8|^(["].{0,20}["])$|siehe #48|
    |63|Zusatzinformation – Inhalt 8|^(["].{0,210}["])$|siehe #48|
    |64|Zusatzinformation – Art 9|^(["].{0,20}["])$|siehe #48|
    |65|Zusatzinformation – Inhalt 9|^(["].{0,210}["])$|siehe #48|
    |66|Zusatzinformation – Art 10|^(["].{0,20}["])$|siehe #48|
    |67|Zusatzinformation – Inhalt 10|^(["].{0,210}["])$|siehe #48|
    |68|Zusatzinformation – Art 11|^(["].{0,20}["])$|siehe #48|
    |69|Zusatzinformation – Inhalt 11|^(["].{0,210}["])$|siehe #48|
    |70|Zusatzinformation – Art 12|^(["].{0,20}["])$|siehe #48|
    |71|Zusatzinformation – Inhalt 12|^(["].{0,210}["])$|siehe #48|
    |72|Zusatzinformation – Art 13|^(["].{0,20}["])$|siehe #48|
    |73|Zusatzinformation – Inhalt 13|^(["].{0,210}["])$|siehe #48|
    |74|Zusatzinformation – Art 14|^(["].{0,20}["])$|siehe #48|
    |75|Zusatzinformation – Inhalt 14|^(["].{0,210}["])$|siehe #48|
    |76|Zusatzinformation – Art 15|^(["].{0,20}["])$|siehe #48|
    |77|Zusatzinformation – Inhalt 15|^(["].{0,210}["])$|siehe #48|
    |78|Zusatzinformation – Art 16|^(["].{0,20}["])$|siehe #48|
    |79|Zusatzinformation – Inhalt 16|^(["].{0,210}["])$|siehe #48|
    |80|Zusatzinformation – Art 17|^(["].{0,20}["])$|siehe #48|
    |81|Zusatzinformation – Inhalt 17|^(["].{0,210}["])$|siehe #48|
    |82|Zusatzinformation – Art 18|^(["].{0,20}["])$|siehe #48|
    |83|Zusatzinformation – Inhalt 18|^(["].{0,210}["])$|siehe #48|
    |84|Zusatzinformation – Art 19|^(["].{0,20}["])$|siehe #48|
    |85|Zusatzinformation – Inhalt 19|^(["].{0,210}["])$|siehe #48|
    |86|Zusatzinformation – Art 20|^(["].{0,20}["])$|siehe #48|
    |87|Zusatzinformation – Inhalt 20|^(["].{0,210}["])$|siehe #48|
    |88|Stück|^\d{0,8}$|Wirkt sich nur bei Sachverhalt mit SKR 14 Land- und Forstwirtschaft aus, für andere SKR werden die Felder beim Import / Export überlesen bzw. leer exportiert.|
    |89|Gewicht|^(\d{1,8}[,]\d{2})$|siehe #88|
    |90|Zahlweise|^\d{0,2}$|OPOS-Informationen kommunal1 = Lastschrift2 = Mahnung3 = Zahlung|
    |91|Forderungsart|^(["]\w{0,10}["])$|OPOS-Informationen kommunal|
    |92|Veranlagungsjahr|^(([2])([0])([0-9]{2}))$|OPOS-Informationen kommunalFormat: JJJJ|
    |93|Zugeordnete Fälligkeit|^((0[1-9]|[1-2][0-9]|3[0-1])(0[1-9]|1[0-2])([2])([0])([0-9]{2}))$|OPOS-Informationen kommunalFormat: TTMMJJJJ|
    |94|Skontotyp|^\d$|1 = Einkauf von Waren2 = Erwerb von Roh-Hilfs- und Betriebsstoffen|
    |95|Auftragsnummer|^(["].{0,30}["])$|Allgemeine Bezeichnung des Auftrags / Projekts.Nur in Verbindung mit Anzahlungen muss auch der Buchungstyp (#96) angegeben werden.Bei Rechnungen zu PayPal-Zahlungen: Order-ID oder Transaktions-ID(siehe Dok.-Nr.1002651)|
    |96|Buchungstyp|^(["][A-Z]{2}["])$|AA = Angeforderte Anzahlung / AbschlagsrechnungAG = Erhaltene Anzahlung (Geldeingang)AV = Erhaltene Anzahlung (Verbindlichkeit)SR = SchlussrechnungSU = Schlussrechnung (Umbuchung)SG = Schlussrechnung (Geldeingang)SO = Sonstige|
    |97|USt-Schlüssel (Anzahlungen)|^\d{0,4}$|USt-Schlüssel der späteren Schlussrechnung|
    |98|EU-Mitgliedstaat (Anzahlungen)|^(["][A-Z]{2}["])$|EU-Mitgliedstaat der späteren Schlussrechnung(siehe Dok.-Nr.1080169)Ausnahmen:Griechenland=ELNordirland=XI|
    |99|Sachverhalt L+L (Anzahlungen)|^\d{0,3}$|L+L-Sachverhalt der späteren Schlussrechnung Sachverhalte gem. § 13b Abs. 1 und 2 UStG.Achtung:Der Wert 0 ist unzulässig.(siehe Dok.-Nr.1034915und1003613)|
    |100|EU-Steuersatz (Anzahlungen)|^(\d{1,2}[,]\d{2})$|EU-Steuersatz der späteren SchlussrechnungNur für entsprechende EU-Buchungen:Der im EU-Bestimmungsland gültige Steuersatz.Beispiel: 12,12|
    |101|Erlöskonto (Anzahlungen)|^(\d{4,8})$|Erlöskonto der späteren Schlussrechnung|
    |102|Herkunft-Kz|^(["][A-Z]{2}["])$|Wird beim Import durch SV (Stapelverarbeitung) ersetzt.|
    |103|Leerfeld|^(["].{0,36}["])$|Wird von DATEV verwendet|
    |104|KOST-Datum|^((0[1-9]|[1-2]\d|3[0-1])(0[1-9]|1[0-2])([2])([0])(\d{2}))$|Format: TTMMJJJJ|
    |105|SEPA-Mandatsreferenz|^(["].{0,35}["])$|Vom Zahlungsempfänger individuell vergebenes Kennzeichen eines Mandats (z.B. Rechnungs- oder Kundennummer). Beim Import der SEPA-Mandatsreferenz muss auch das Feld Geschäftspartnerbank (#17) gefüllt sein.|
    |106|Skontosperre|^[0|1]$|1 = Skontosperre0 = keine SkontosperreDieses Feld ermöglicht, einzelne Positionen zu übergeben, für die eine Zahlung mit Skonto nicht zulässig ist (z.B. Liefer- und Versandkosten).Bei Verbuchung der Zahlung ist die Sperre nur im Modus „Zahlungen buchen“ wirksam. Bei „Zahlungsvorschläge erzeugen“ wird die Sperre nicht berücksichtigt.|
    |107|Gesellschaftername|^(["].{0,76}["])$|Muss mit dem zugeordneten Gesellschafter in den zentralen Stammdaten übereinstimmen.|
    |108|Beteiligtennummer|^(\d{4})$|Muss-Feld für die Zuordnung von Gesellschaftern zum Buchungssatz.Die Beteiligtennummer muss der amtlichen Nummer aus der Feststellungserklärung entsprechen, diese darf nicht beliebig vergeben werden.Die Pflege der Gesellschafterdaten und das Anlegen von Sonderbilanzsachverhalten ist nur in Absprache mit der Steuerkanzlei möglich. Betrifft #107-110.|
    |109|Identifikationsnummer|^(["].{0,11}["])$||
    |110|Zeichnernummer|^(["].{0,20}["])$||
    |111|Postensperre bis|^((0[1-9]|[1-2]\d|3[0-1])(0[1-9]|1[0-2])([2])([0])(\d{2}))$|Format: TTMMJJJJ|
    |112|Bezeichnung SoBil-Sachverhalt|^(["].{0,30}["])$||
    |113|Kennzeichen SoBil-Buchung|^(\d{1,2})$|1 = SoBil-Buchung erzeugt0 = SoBil-Buchung nicht erzeugt (default)|
    |114|Festschreibung|^(0|1)$|leer = nicht definiert; wird automatisch festgeschrieben0 = keine Festschreibung1 = FestschreibungHat ein Buchungssatz in diesem Feld den Inhalt 1, so wird dergesamte Stapel nach dem Import festgeschrieben.|
    |115|Leistungsdatum|^((0[1-9]|[1-2]\d|3[0-1])(0[1-9]|1[0-2])([2])([0])(\d{2}))$|Format: TTMMJJJJ(siehe Dok.-Nr.9211426)Beim Import des Leistungsdatums muss das Feld „116 Datum Zuord. Steuerperiode“ gefüllt sein. Der Einsatz des Leistungsdatums muss in Absprache mit dem Steuerberater erfolgen.|
    |116|Datum Zuord. Steuerperiode|^((0[1-9]|[1-2]\d|3[0-1])(0[1-9]|1[0-2])([2])([0])(\d{2}))$|Format: TTMMJJJJ|
    |117|Fälligkeit|^((0[1-9]|[1-2]\d|3[0-1])(0[1-9]|1[0-2])([2])([0])(\d{2}))$|Nur in Verbindung mit OPOS relevant.Format: TTMMJJJJOPOS-Verarbeitungsinformationen über Belegfeld 2 (Feldnummer 12) sind in diesem Fall nicht nutzbar.|
    |118|Generalumkehr|^(["](0|1)["])$|G oder 1 = Generalumkehr0 = keine Generalumkehr|
    |119|Steuersatz|^(\d{1,2}[,]\d{2})$|Nur bei Verwendung von Steuerschlüsseln mit Steuersatzwahl (z.B. 100, 400)(siehe Dok.-Nr.9231348)Wenn erforderlich, zusammen mit Feld 120 (Land) erfassen.|
    |120|Land|^(["][A-Z]{2}["])$|ISO-Code beachten (siehe Dok.-Nr.1080169)Beispiel: DE für DeutschlandWenn erforderlich, zusammen mit Feld 119 (Steuersatz) erfassen.|
    |121|Abrechnungsreferenz|^(["].{0,50}["])$|Die Abrechnungsreferenz stellt eine Klammer über alle Transaktionen des Zahlungsdienstleisters und die dazu gehörige Auszahlung dar. Sie wird über den Zahlungsdatenservice bereitgestellt und bei der Erzeugung von Buchungsvorschläge berücksichtigt.|
    |122|BVV-Position (Betriebsvermögensvergleich)|^([1|2|3|4|5])$|Details zum Feld siehe Dok.-Nr.10186491 = Kapitalanpassung2 = Entnahme / Ausschüttung lfd. WJ3 = Einlage / Kapitalzuführung lfd. WJ4 = Übertragung § 6b Rücklage5 = Umbuchung (keine Zuordnung)|
    |123|EU-Mitgliedstaat u. UStID (Ursprung)|^(["].{0,15}["])$|Die USt-IdNr. besteht aus:2-stelligen Länderkürzel (siehe Dok.-Nr.1080169)Ausnahmen:Griechenland = ELNordirland = XImax. 13-stelliger USt-IdNr.Beispiel: DE133546770Die USt-IdNr. kann auch Buchstaben haben, z.B. bei Österreich.Detaillierte Informationen zur Erfassung von EU-Informationen im Buchungssatz: Dok.-Nr.9211462.|
    |124|EU-Steuersatz (Ursprung)|^\d{2}[,]\d{2}$|Nur für entsprechende EU-Buchungen:Der im EU-Ursprungsland gültige Steuersatz.Beispiel: 12,12|
    |125|Abw. Skontokonto|^(\d{1,9})$|Zulässig sind hier, bei Zahlungsbuchungen mit Skontoabzug, Konten mit dem Kontenzweck „sonstige betriebliche Aufwendungen“. Eine Eingabe in diesem Feld bedeutet, dass der Skontobetrag auf dieses Aufwandskonto gebucht wird.Wenn in der Importdatei keine Angaben zum Skontokonto enthalten sind, wird der Skontobetrag auf das entsprechende Skontosammelkonto gebucht.Detaillierte Informationen zur Nutzung der Funktion: Dok.-Nr.1036387|
    """

    Umsatz: str  # 1
    SollHabenKennzeichen: str  # 2
    WKZ_Umsatz: str  # 3
    Kurs: str  # 4
    BasisUmsatz: str  # 5
    WKZ_BasisUmsatz: str  # 6
    Konto: str  # 7
    Gegenkonto: str  # 8
    BU_Schluessel: str  # 9
    Belegdatum: str  # 10
    Belegfeld_1: str  # 11
    Belegfeld_2: str  # 12
    Skonto: str  # 13
    Buchungstext: str  # 14
    Postensperre: str  # 15
    Diverse_Adressnummer: str  # 16
    Geschaeftspartnerbank: str  # 17
    Sachverhalt: str  # 18
    Zinssperre: str  # 19
    Beleglink: str  # 20
    Beleginfo_Art_1: str  # 21
    Beleginfo_Inhalt_1: str  # 22
    Beleginfo_Art_2: str  # 23
    Beleginfo_Inhalt_2: str  # 24
    Beleginfo_Art_3: str  # 25
    Beleginfo_Inhalt_3: str  # 26
    Beleginfo_Art_4: str  # 27
    Beleginfo_Inhalt_4: str  # 28
    Beleginfo_Art_5: str  # 29
    Beleginfo_Inhalt_5: str  # 30
    Beleginfo_Art_6: str  # 31
    Beleginfo_Inhalt_6: str  # 32
    Beleginfo_Art_7: str  # 33
    Beleginfo_Inhalt_7: str  # 34
    Beleginfo_Art_8: str  # 35
    Beleginfo_Inhalt_8: str  # 36
    KOST1_Kostenstelle: str  # 37
    KOST2_Kostenstelle: str  # 38
    KOST_Menge: str  # 39
    EU_Mitgliedstaat_u_UStID_Bestimmung: str  # 40
    EU_Steuersatz_Bestimmung: str  # 41
    Abw_Versteuerungsart: str  # 42
    Sachverhalt_L_L: str  # 43
    Funktionsergaenzung_L_L: str  # 44
    BU_49_Hauptfunktiontyp: str  # 45
    BU_49_Hauptfunktionsnummer: str  # 46
    BU_49_Funktionsergaenzung: str  # 47
    Zusatzinformation_Art_1: str  # 48
    Zusatzinformation_Inhalt_1: str  # 49
    Zusatzinformation_Art_2: str  # 50
    Zusatzinformation_Inhalt_2: str  # 51
    Zusatzinformation_Art_3: str  # 52
    Zusatzinformation_Inhalt_3: str  # 53
    Zusatzinformation_Art_4: str  # 54
    Zusatzinformation_Inhalt_4: str  # 55
    Zusatzinformation_Art_5: str  # 56
    Zusatzinformation_Inhalt_5: str  # 57
    Zusatzinformation_Art_6: str  # 58
    Zusatzinformation_Inhalt_6: str  # 59
    Zusatzinformation_Art_7: str  # 60
    Zusatzinformation_Inhalt_7: str  # 61
    Zusatzinformation_Art_8: str  # 62
    Zusatzinformation_Inhalt_8: str  # 63
    Zusatzinformation_Art_9: str  # 64
    Zusatzinformation_Inhalt_9: str  # 65
    Zusatzinformation_Art_10: str  # 66
    Zusatzinformation_Inhalt_10: str  # 67
    Zusatzinformation_Art_11: str  # 68
    Zusatzinformation_Inhalt_11: str  # 69
    Zusatzinformation_Art_12: str  # 70
    Zusatzinformation_Inhalt_12: str  # 71
    Zusatzinformation_Art_13: str  # 72
    Zusatzinformation_Inhalt_13: str  # 73
    Zusatzinformation_Art_14: str  # 74
    Zusatzinformation_Inhalt_14: str  # 75
    Zusatzinformation_Art_15: str  # 76
    Zusatzinformation_Inhalt_15: str  # 77
    Zusatzinformation_Art_16: str  # 78
    Zusatzinformation_Inhalt_16: str  # 79
    Zusatzinformation_Art_17: str  # 80
    Zusatzinformation_Inhalt_17: str  # 81
    Zusatzinformation_Art_18: str  # 82
    Zusatzinformation_Inhalt_18: str  # 83
    Zusatzinformation_Art_19: str  # 84
    Zusatzinformation_Inhalt_19: str  # 85
    Zusatzinformation_Art_20: str  # 86
    Zusatzinformation_Inhalt_20: str  # 87
    Stueck: str  # 88
    Gewicht: str  # 89
    Zahlweise: str  # 90
    Forderungsart: str  # 91
    Veranlagungsjahr: str  # 92
    Zugeordnete_Faelligkeit: str  # 93
    Skontotyp: str  # 94
    Auftragsnummer: str  # 95
    Buchungstyp: str  # 96
    USt_Schluessel_Anzahlungen: str  # 97
    EU_Mitgliedstaat_Anzahlungen: str  # 98
    Sachverhalt_L_L_Anzahlungen: str  # 99
    EU_Steuersatz_Anzahlungen: str  # 100
    Erloeskonto_Anzahlungen: str  # 101
    Herkunft_Kz: str  # 102
    Leerfeld: str  # 103
    KOST_Datum: str  # 104
    SEPA_Mandatsreferenz: str  # 105
    Skontosperre: str  # 106
    Gesellschaftername: str  # 107
    Beteiligtennummer: str  # 108
    Identifikationsnummer: str  # 109
    Zeichnernummer: str  # 110
    Postensperre_bis: str  # 111
    Bezeichnung_SoBil_Sachverhalt: str  # 112
    Kennzeichen_SoBil_Buchung: str  # 113
    Festschreibung: str  # 114
    Leistungsdatum: str  # 115
    Datum_Zuord_Steuerperiode: str  # 116
    Faelligkeit: str  # 117
    Generalumkehr: str  # 118
    Steuersatz: str  # 119
    Land: str  # 120
    Abrechnungsreferenz: str  # 121
    BVV_Position_Betriebsvermoegensvergleich: str  # 122
    EU_Mitgliedstaat_u_UStID_Ursprung: str  # 123
    EU_Steuersatz_Ursprung: str  # 124
    Abw_Skontokonto: str  # 125

    def to_csv_line(self) -> str:
        """Convert the BuchungsstapelItem to a CSV line."""
        output = StringIO()
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_ALL)
        writer.writerow(asdict(self).values())
        return output.getvalue().strip()

    @staticmethod
    def from_csv_line(data: str) -> "BuchungsstapelItem":
        f = StringIO(data)
        reader = csv.reader(f, delimiter=";")
        row = next(reader)
        if len(row) != 125:
            raise ValueError(f"Expected 125 fields, got {len(row)}")
        return BuchungsstapelItem(*row)

    @staticmethod
    def from_ledger_import(ledger: LedgerImport) -> "BuchungsstapelItem":
        settings = Settings.getinstance()
        createion_date = datetime.strptime(
            ledger.consolidate.consolidated_date, "%Y-%m-%d"
        )
        rg_nr = ledger.consolidate.consolidated_invoice_id
        if not rg_nr:
            raise ValueError("LedgerImport must have an invoice ID")

        payable_ledger = ledger.consolidate.ledgers[0]
        if not isinstance(payable_ledger, AccountsReceivableLedger):
            raise ValueError(
                "The ledger consolidate.ledgers[0] must be an AccountsPayableLedger"
            )
        booking_text = payable_ledger.base1.booking_text
        if not booking_text:
            raise ValueError("The ledger must have a booking text")

        return BuchungsstapelItem(
            Umsatz=ledger.consolidate.consolidated_amount.replace(".", ","),
            SollHabenKennzeichen="H",
            WKZ_Umsatz="",
            Kurs="",
            BasisUmsatz="",
            WKZ_BasisUmsatz="",
            Konto=str(settings.buchungskonto),
            Gegenkonto=str(settings.gegenkonto),
            BU_Schluessel="",
            Belegdatum=createion_date.strftime("%d%m"),
            Belegfeld_1=rg_nr,
            Belegfeld_2="",
            Skonto="",
            Buchungstext=booking_text,
            Postensperre="",
            Diverse_Adressnummer="",
            Geschaeftspartnerbank="",
            Sachverhalt="",
            Zinssperre="",
            Beleglink="",
            Beleginfo_Art_1="",
            Beleginfo_Inhalt_1="",
            Beleginfo_Art_2="",
            Beleginfo_Inhalt_2="",
            Beleginfo_Art_3="",
            Beleginfo_Inhalt_3="",
            Beleginfo_Art_4="",
            Beleginfo_Inhalt_4="",
            Beleginfo_Art_5="",
            Beleginfo_Inhalt_5="",
            Beleginfo_Art_6="",
            Beleginfo_Inhalt_6="",
            Beleginfo_Art_7="",
            Beleginfo_Inhalt_7="",
            Beleginfo_Art_8="",
            Beleginfo_Inhalt_8="",
            KOST1_Kostenstelle="",
            KOST2_Kostenstelle="",
            KOST_Menge="",
            EU_Mitgliedstaat_u_UStID_Bestimmung="",
            EU_Steuersatz_Bestimmung="",
            Abw_Versteuerungsart="",
            Sachverhalt_L_L="",
            Funktionsergaenzung_L_L="",
            BU_49_Hauptfunktiontyp="",
            BU_49_Hauptfunktionsnummer="",
            BU_49_Funktionsergaenzung="",
            Zusatzinformation_Art_1="",
            Zusatzinformation_Inhalt_1="",
            Zusatzinformation_Art_2="",
            Zusatzinformation_Inhalt_2="",
            Zusatzinformation_Art_3="",
            Zusatzinformation_Inhalt_3="",
            Zusatzinformation_Art_4="",
            Zusatzinformation_Inhalt_4="",
            Zusatzinformation_Art_5="",
            Zusatzinformation_Inhalt_5="",
            Zusatzinformation_Art_6="",
            Zusatzinformation_Inhalt_6="",
            Zusatzinformation_Art_7="",
            Zusatzinformation_Inhalt_7="",
            Zusatzinformation_Art_8="",
            Zusatzinformation_Inhalt_8="",
            Zusatzinformation_Art_9="",
            Zusatzinformation_Inhalt_9="",
            Zusatzinformation_Art_10="",
            Zusatzinformation_Inhalt_10="",
            Zusatzinformation_Art_11="",
            Zusatzinformation_Inhalt_11="",
            Zusatzinformation_Art_12="",
            Zusatzinformation_Inhalt_12="",
            Zusatzinformation_Art_13="",
            Zusatzinformation_Inhalt_13="",
            Zusatzinformation_Art_14="",
            Zusatzinformation_Inhalt_14="",
            Zusatzinformation_Art_15="",
            Zusatzinformation_Inhalt_15="",
            Zusatzinformation_Art_16="",
            Zusatzinformation_Inhalt_16="",
            Zusatzinformation_Art_17="",
            Zusatzinformation_Inhalt_17="",
            Zusatzinformation_Art_18="",
            Zusatzinformation_Inhalt_18="",
            Zusatzinformation_Art_19="",
            Zusatzinformation_Inhalt_19="",
            Zusatzinformation_Art_20="",
            Zusatzinformation_Inhalt_20="",
            Stueck="",
            Gewicht="",
            Zahlweise="",
            Forderungsart="",
            Veranlagungsjahr="",
            Zugeordnete_Faelligkeit="",
            Skontotyp="",
            Auftragsnummer="",
            Buchungstyp="",
            USt_Schluessel_Anzahlungen="0",
            EU_Mitgliedstaat_Anzahlungen="",
            Sachverhalt_L_L_Anzahlungen="",
            EU_Steuersatz_Anzahlungen="",
            Erloeskonto_Anzahlungen="0",
            Herkunft_Kz="RE",
            Leerfeld="",
            KOST_Datum="",
            SEPA_Mandatsreferenz="",
            Skontosperre="0",
            Gesellschaftername="",
            Beteiligtennummer="",
            Identifikationsnummer="",
            Zeichnernummer="",
            Postensperre_bis="",
            Bezeichnung_SoBil_Sachverhalt="",
            Kennzeichen_SoBil_Buchung="",
            Festschreibung="1",
            Leistungsdatum="",
            Datum_Zuord_Steuerperiode="",
            Faelligkeit="",
            Generalumkehr="0",
            Steuersatz="",
            Land="",
            Abrechnungsreferenz="",
            BVV_Position_Betriebsvermoegensvergleich="0",
            EU_Mitgliedstaat_u_UStID_Ursprung="",
            EU_Steuersatz_Ursprung="",
            Abw_Skontokonto="",
        )


DATA_DESCRIPTION_HEAD = "Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Kurs;Basis-Umsatz;WKZ Basis-Umsatz;Konto;Gegenkonto (ohne BU-Schlüssel);BU-Schlüssel;Belegdatum;Belegfeld 1;Belegfeld 2;Skonto;Buchungstext;Postensperre;Diverse Adressnummer;Geschäftspartnerbank;Sachverhalt;Zinssperre;Beleglink;Beleginfo-Art 1;Beleginfo-Inhalt 1;Beleginfo-Art 2;Beleginfo-Inhalt 2;Beleginfo-Art 3;Beleginfo-Inhalt 3;Beleginfo-Art 4;Beleginfo-Inhalt 4;Beleginfo-Art 5;Beleginfo-Inhalt 5;Beleginfo-Art 6;Beleginfo-Inhalt 6;Beleginfo-Art 7;Beleginfo-Inhalt 7;Beleginfo-Art 8;Beleginfo-Inhalt 8;KOST1-Kostenstelle;KOST2-Kostenstelle;KOST-Menge;EU-Mitgliedstaat u. UStID (Bestimmung);EU-Steuersatz (Bestimmung);Abw. Versteuerungsart;Sachverhalt L+L;Funktionsergänzung L+L;BU 49 Hauptfunktiontyp;BU 49 Hauptfunktionsnummer;BU 49 Funktionsergänzung;Zusatzinformation – Art 1;Zusatzinformation – Inhalt 1;Zusatzinformation – Art 2;Zusatzinformation – Inhalt 2;Zusatzinformation – Art 3;Zusatzinformation – Inhalt 3;Zusatzinformation – Art 4;Zusatzinformation – Inhalt 4;Zusatzinformation – Art 5;Zusatzinformation – Inhalt 5;Zusatzinformation – Art 6;Zusatzinformation – Inhalt 6;Zusatzinformation – Art 7;Zusatzinformation – Inhalt 7;Zusatzinformation – Art 8;Zusatzinformation – Inhalt 8;Zusatzinformation – Art 9;Zusatzinformation – Inhalt 9;Zusatzinformation – Art 10;Zusatzinformation – Inhalt 10;Zusatzinformation – Art 11;Zusatzinformation – Inhalt 11;Zusatzinformation – Art 12;Zusatzinformation – Inhalt 12;Zusatzinformation – Art 13;Zusatzinformation – Inhalt 13;Zusatzinformation – Art 14;Zusatzinformation – Inhalt 14;Zusatzinformation – Art 15;Zusatzinformation – Inhalt 15;Zusatzinformation – Art 16;Zusatzinformation – Inhalt 16;Zusatzinformation – Art 17;Zusatzinformation – Inhalt 17;Zusatzinformation – Art 18;Zusatzinformation – Inhalt 18;Zusatzinformation – Art 19;Zusatzinformation – Inhalt 19;Zusatzinformation – Art 20;Zusatzinformation – Inhalt 20;Stück;Gewicht;Zahlweise;Forderungsart;Veranlagungsjahr;Zugeordnete Fälligkeit;Skontotyp;Auftragsnummer;Buchungstyp;USt-Schlüssel (Anzahlungen);EU-Mitgliedstaat (Anzahlungen);Sachverhalt L+L (Anzahlungen);EU-Steuersatz (Anzahlungen);Erlöskonto (Anzahlungen);Herkunft-Kz;Leerfeld;KOST-Datum;SEPA-Mandatsreferenz;Skontosperre;Gesellschaftername;Beteiligtennummer;Identifikationsnummer;Zeichnernummer;Postensperre bis;Bezeichnung SoBil-Sachverhalt;Kennzeichen SoBil-Buchung;Festschreibung;Leistungsdatum;Datum Zuord. Steuerperiode;Fälligkeit;Generalumkehr;Steuersatz;Land;Abrechnungsreferenz;BVV-Position (Betriebsvermögensvergleich);EU-Mitgliedstaat u. UStID (Ursprung);EU-Steuersatz (Ursprung);Abw. Skontokonto"


def ledger_get_date(ledger: LedgerImport) -> date:
    try:
        return datetime.strptime(
            ledger.consolidate.consolidated_date, "%Y-%m-%d"
        ).date()
    except ValueError as e:
        raise ValueError(
            f"Invalid date format in ledger: {ledger.consolidate.consolidated_date}"
        ) from e


@dataclass
class Buchungsstapel:
    header: Header
    items: list[BuchungsstapelItem]

    @staticmethod
    def from_ledger_import_w_metadata(
        data: list[LedgerImportWMetadata],
    ) -> "Buchungsstapel":
        oldest = min(data, key=lambda x: ledger_get_date(x[0]))
        newest = max(data, key=lambda x: ledger_get_date(x[0]))

        header = Header(
            kennzeichen="DTVF",
            version="700",
            format_kategory=FormatCategory.BOOKING_BATCH,
            formatname="Buchungsstapel",
            formatversion=13,
            erzeugt_am=datetime.now().date(),
            imported=None,
            herkunft="RE",
            exportiert_von="1001919U00113",
            importiert_von="",
            berater_nummer=12191,
            mandant_nummer=45061,
            wj_beginn=date(oldest[1][0], 1, 1),
            sachkontenlaenge=4,
            datum_von=ledger_get_date(oldest[0]),
            datum_bis=ledger_get_date(newest[0]),
            bezeichnung=f"Fibu {ledger_get_date(newest[0]).month}.{ledger_get_date(newest[0]).year}",
            diktatkuerzel="SG",
            buchungstyp=Buchungstyp.FINANZBUCHFUEHRUNG,
            rechnungslegungszweck=Rechnungslegungszweck.UNABHAENGIG,
            festschreibung=1,
            wkz="EUR",
            reserviert_1=None,
            derivatskennzeichen=None,
            reserviert_2=None,
            reserviert_3=None,
            sachkontenrahmen="3",
            id_der_branchenloesung=None,
            reserviert_4=None,
            reserviert_5=None,
            anwendungsinformation=None,
        )

        items = [
            BuchungsstapelItem.from_ledger_import(ledger)
            for ledger, _ in data
            if isinstance(ledger, LedgerImport)
        ]
        return Buchungsstapel(header=header, items=items)

    def to_csv(self) -> str:
        """Convert the entire Buchungsstapel to a CSV string."""
        lines = [
            self.header.to_csv_herder(),
            DATA_DESCRIPTION_HEAD,
        ]
        for item in self.items:
            lines.append(item.to_csv_line())
        return "\n".join(lines)


def build_csv(data: Mapping[Path, LedgerImportWMetadata], path: Path) -> None:
    buchungsstapel = Buchungsstapel.from_ledger_import_w_metadata(list(data.values()))
    csv_content = buchungsstapel.to_csv()
    with open(path, "w", encoding="utf-8") as f:
        f.write(csv_content)


if __name__ == "__main__":
    header = Header.from_csv_header(
        "DTVF;700;21;Buchungsstapel;13;20250918140440439;;RE;1001919U00113;;12191;45061;20250101;4;20250601;20250630;Fibu 6.2025;SG;1;0;1;EUR;;KP;;29367;3;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;"
    )
    print(header)
    print(header.__repr__())

    LINE = """380,8;H;;;;;8400;10006;;506;25450;;;AST Aufzüge Thieme GmbH;;;;;;"BEDI ""0A3C0BEE-AA04-11CA-C094-37B4C6C25031"\"";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;0;;;;0;RE;76867cbb-9113-4cb6-ad3a-a3104dea8db4;;;0;;;;;;;;1;;;;0;;;;0;;;"""

    line1 = BuchungsstapelItem.from_csv_line(LINE)
    print(line1)
    new_line_str = line1.to_csv_line()
    print(new_line_str)
    print(f"{LINE == new_line_str=}")
