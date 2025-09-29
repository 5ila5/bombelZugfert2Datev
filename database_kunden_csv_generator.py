import csv
from datetime import datetime
from io import StringIO
from tkinter.filedialog import asksaveasfilename
from typing import Iterable, TypedDict

from converter_app.database_retrieve_account_no import mydb

now = datetime.now()
# YYYYMMDDHHMMSSFFF
timestamp = now.strftime("%Y%m%d%H%M%S%f")[:-3]
start_of_year = now.replace(
    month=1, day=1, hour=0, minute=0, second=0, microsecond=0
).strftime("%Y%m%d")

HEADER_LINE = f'"EXTF";700;16;"Debitoren/Kreditoren";4;{timestamp};;;;;12191;45061;{start_of_year};4;;;"";"";;;;"";;;;0;'


class DBData(TypedDict):
    konto_nr: int | None
    name: str
    kundennr: str
    street: str
    postal_code: str
    city: str
    country: str


DEFAULT_KTR = {
    "A Diverse Debitoren": 10000,
    "B Diverse Debitoren": 12000,
    "C Diverse Debitoren": 14000,
    "D Diverse Debitoren": 16000,
    "E Diverse Debitoren": 18000,
    "F Diverse Debitoren": 20000,
    "G Diverse Debitoren": 22000,
    "H Diverse Debitoren": 24000,
    "I Diverse Debitoren": 26000,
    "J Diverse Debitoren": 28000,
    "K Diverse Debitoren": 30000,
    "l Diverse Debitoren": 32000,
    "M Diverse Debitoren": 34000,
    "N Diverse Debitoren": 36000,
    "O Diverse Debitoren": 37000,  # Wrong but used like this
    "P Diverse Debitoren": 40000,
    "Q Diverse Debitoren": 42000,
    "R Diverse Debitoren": 44000,
    "S Diverse Debitoren": 46000,
    "SCH Diverse Debitoren": 48000,
    "ST Diverse Debitoren": 50000,
    "T Diverse Debitoren": 52000,
    "U Diverse Debitoren": 54000,
    "V Diverse Debitoren": 56000,
    "W Diverse Debitoren": 58000,
    "Z Diverse Debitoren": 64000,
}

DEFAULT_KTR_DB_DATA: list[DBData] = [
    {
        "konto_nr": val,
        "name": key,
        "kundennr": "",
        "street": "",
        "postal_code": "",
        "city": "",
        "country": "DE",
    }
    for key, val in DEFAULT_KTR.items()
]


CSV_HEADER_LIST = [
    "Konto",
    "Name (Adressattyp Unternehmen)",
    "Unternehmensgegenstand",
    "Name (Adressattyp natürl. Person)",
    "Vorname (Adressattyp natürl. Person)",
    "Name (Adressattyp keine Angabe)",
    "Adressattyp",
    "Kurzbezeichnung",
    "EU-Land",
    "EU-UStID",
    "Anrede",
    "Titel/Akad. Grad",
    "Adelstitel",
    "Namensvorsatz",
    "Adressart",
    "Straße",
    "Postfach",
    "Postleitzahl",
    "Ort",
    "Land",
    "Versandzusatz",
    "Adresszusatz",
    "Abweichende Anrede",
    "Abw. Zustellbezeichnung 1",
    "Abw. Zustellbezeichnung 2",
    "Kennz. Korrespondenzadresse",
    "Adresse Gültig von",
    "Adresse Gültig bis",
    "Telefon",
    "Bemerkung (Telefon)",
    "Telefon GL",
    "Bemerkung (Telefon GL)",
    "E-Mail",
    "Bemerkung (E-Mail)",
    "Internet",
    "Bemerkung (Internet)",
    "Fax",
    "Bemerkung (Fax)",
    "Sonstige",
    "Bemerkung (Sonstige)",
    "Bankleitzahl 1",
    "Bankbezeichnung 1",
    "Bank-Kontonummer 1",
    "Länderkennzeichen 1",
    "IBAN-Nr. 1",
    "Leerfeld",
    "SWIFT-Code 1",
    "Abw. Kontoinhaber 1",
    "Kennz. Hauptbankverb. 1",
    "Bankverb 1 Gültig von",
    "Bankverb 1 Gültig bis",
    "Bankleitzahl 2",
    "Bankbezeichnung 2",
    "Bank-Kontonummer 2",
    "Länderkennzeichen 2",
    "IBAN-Nr. 2",
    "Leerfeld",
    "SWIFT-Code 2",
    "Abw. Kontoinhaber 2",
    "Kennz. Hauptbankverb. 2",
    "Bankverb 2 Gültig von",
    "Bankverb 2 Gültig bis",
    "Bankleitzahl 3",
    "Bankbezeichnung 3",
    "Bank-Kontonummer 3",
    "Länderkennzeichen 3",
    "IBAN-Nr. 3",
    "Leerfeld",
    "SWIFT-Code 3",
    "Abw. Kontoinhaber 3",
    "Kennz. Hauptbankverb. 3",
    "Bankverb 3 Gültig von",
    "Bankverb 3 Gültig bis",
    "Bankleitzahl 4",
    "Bankbezeichnung 4",
    "Bank-Kontonummer 4",
    "Länderkennzeichen 4",
    "IBAN-Nr. 4",
    "Leerfeld",
    "SWIFT-Code 4",
    "Abw. Kontoinhaber 4",
    "Kennz. Hauptbankverb. 4",
    "Bankverb 4 Gültig von",
    "Bankverb 4 Gültig bis",
    "Bankleitzahl 5",
    "Bankbezeichnung 5",
    "Bank-Kontonummer 5",
    "Länderkennzeichen 5",
    "IBAN-Nr. 5",
    "Leerfeld",
    "SWIFT-Code 5",
    "Abw. Kontoinhaber 5",
    "Kennz. Hauptbankverb. 5",
    "Bankverb 5 Gültig von",
    "Bankverb 5 Gültig bis",
    "Leerfeld",
    "Briefanrede",
    "Grußformel",
    "Kunden-/Lief.-Nr.",
    "Steuernummer",
    "Sprache",
    "Ansprechpartner",
    "Vertreter",
    "Sachbearbeiter",
    "Diverse-Konto",
    "Ausgabeziel",
    "Währungssteuerung",
    "Kreditlimit (Debitor)",
    "Zahlungsbedingung",
    "Fälligkeit in Tagen (Debitor)",
    "Skonto in Prozent (Debitor)",
    "Kreditoren-Ziel 1 Tg.",
    "Kreditoren-Skonto 1 %",
    "Kreditoren-Ziel 2 Tg.",
    "Kreditoren-Skonto 2 %",
    "Kreditoren-Ziel 3 Brutto Tg.",
    "Kreditoren-Ziel 4 Tg.",
    "Kreditoren-Skonto 4 %",
    "Kreditoren-Ziel 5 Tg.",
    "Kreditoren-Skonto 5 %",
    "Mahnung",
    "Kontoauszug",
    "Mahntext 1",
    "Mahntext 2",
    "Mahntext 3",
    "Kontoauszugstext",
    "Mahnlimit Betrag",
    "Mahnlimit %",
    "Zinsberechnung",
    "Mahnzinssatz 1",
    "Mahnzinssatz 2",
    "Mahnzinssatz 3",
    "Lastschrift",
    "Leerfeld",
    "Mandantenbank",
    "Zahlungsträger",
    "Indiv. Feld 1",
    "Indiv. Feld 2",
    "Indiv. Feld 3",
    "Indiv. Feld 4",
    "Indiv. Feld 5",
    "Indiv. Feld 6",
    "Indiv. Feld 7",
    "Indiv. Feld 8",
    "Indiv. Feld 9",
    "Indiv. Feld 10",
]


def build_csv_data(data: Iterable[DBData]) -> str:
    csv_buffer = StringIO()
    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=CSV_HEADER_LIST,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_NONNUMERIC,
        lineterminator="\r\n",
    )
    writer.writeheader()

    for entry in data:
        konto_nr = entry.get("konto_nr", "")
        name = entry.get("name", "")
        kurzbezeichnung = name[:15]
        kundennr = entry.get("kundennr", "")
        street = entry.get("street", "")
        postal_code = entry.get("postal_code", "")
        city = entry.get("city", "")
        country = "DE"

        csv_dict: dict[str, str | int | None] = {val: "" for val in CSV_HEADER_LIST}
        csv_dict["Konto"] = konto_nr
        csv_dict["Name (Adressattyp Unternehmen)"] = name
        csv_dict["Kurzbezeichnung"] = kurzbezeichnung
        csv_dict["Kunden-/Lief.-Nr."] = kundennr
        csv_dict["Straße"] = street
        csv_dict["Postleitzahl"] = postal_code
        csv_dict["Ort"] = city
        csv_dict["Land"] = country

        writer.writerow(csv_dict)

    return csv_buffer.getvalue()


def database_get_entries() -> list[DBData]:
    cursor = mydb.cursor(dictionary=True)
    cursor.execute(
        "SELECT KdNr, KdNme1, KdNme2, KdStr, KdPlz, KdOrt, DatevKtrNr FROM Kunden"
    )
    results = cursor.fetchall()
    data_list: list[DBData] = []
    for row in results:
        kundennr = str(row["KdNr"])
        name1 = str(row["KdNme1"])
        name2 = str(row["KdNme2"])
        name = name1
        if name2:
            name += " " + name2

        name = name[:50]

        street = str(row["KdStr"]) or ""
        postal_code = str(row["KdPlz"]) or ""
        city = str(row["KdOrt"]) or ""
        konto_nr = int(row["DatevKtrNr"])

        data_list.append(
            {
                "konto_nr": konto_nr or None,
                "name": name,
                "kundennr": kundennr,
                "street": street,
                "postal_code": postal_code,
                "city": city,
                "country": "DE",
            }
        )
    return data_list


def build_csv(file_path: str) -> None:
    data = database_get_entries() + DEFAULT_KTR_DB_DATA
    # Western-1 encoding
    with open(file_path, "w", encoding="iso-8859-1", newline="") as f:
        f.write(HEADER_LINE + "\r\n")

        data_str = build_csv_data(data)
        # get chars not encodable in iso-8859-1
        try:
            data_str.encode("iso-8859-1")
        except UnicodeEncodeError as e:
            print(
                f"Warning: Some characters could not be encoded in ISO-8859-1: {e}. They will be replaced with '?'."
            )

            for idx, char in enumerate(data_str):
                try:
                    char.encode("iso-8859-1")
                except UnicodeEncodeError:
                    print(f" - Position {idx}: '{char}' (U+{ord(char):04X})")
                    print(data_str[max(0, idx - 20) : idx + 20])

        f.write(data_str)


if __name__ == "__main__":
    filename = asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        title="Save CSV file",
        initialfile=f"kunden_{timestamp}.csv",
    )

    if filename:
        build_csv(filename)
