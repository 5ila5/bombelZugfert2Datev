import argparse
import csv
from pathlib import Path

# from database_kunden_csv_generator import CSV_HEADER_LIST
from converter_app.database_retrieve_account_no import mydb

KDR_NR = "Kundennummer"
KONTO_NR = "Konto"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a CSV file for customer accounts from the database."
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to the output CSV file.",
        nargs="?",
        default="",
    )
    args = parser.parse_args()
    input_file = args.file
    if not input_file:
        input_file = input("Enter the path to the input CSV file: ").strip()

    input_file_path = Path(input_file)
    if not input_file_path.is_file():
        print(f"The file {input_file} does not exist.")
        exit(1)

    with open(input_file_path, encoding="latin-1") as f:
        csv_reader = csv.DictReader(f.readlines()[1:], delimiter=";")

        csv_data: dict[str, str] = {
            str(k[KDR_NR]): str(k[KONTO_NR])
            for k in csv_reader
            if k[KDR_NR].strip() and k[KONTO_NR].strip()
        }

    cursor = mydb.cursor(dictionary=True)
    sql = f"SELECT KdNr, DatevKtrNr FROM Kunden WHERE KdNr in ({', '.join(['%s'] * len(csv_data))})"  # noqa: S608 # nosec
    cursor.execute(sql, [s for s in csv_data])
    results = cursor.fetchall()

    database_data = dict[str, str]()

    for row in results:
        database_data[str(row["KdNr"])] = str(row["DatevKtrNr"])

    merged_data = {
        kdnr: (csv_data[kdnr], database_data.get(kdnr)) for kdnr in csv_data.keys()
    }

    print(
        f"found {len(csv_data)} complete (kdnr + kontoNR) entries in the CSV file. {len(database_data)} entries found in the database.\n"
    )

    missing_data = []
    found_conflicts = 0
    for kdr, (konto_nr_csv, konto_nr_db) in merged_data.items():
        if konto_nr_csv == konto_nr_db:
            continue
        if konto_nr_db is None:
            print(f"Kunde {kdr} is not in database but has a konto nr in the CSV.")
            found_conflicts += 1
            continue
        if not konto_nr_db.strip("0"):
            print(
                f"Missing account number for customer number {kdr} in database. CSV Konto Nr: {konto_nr_csv}"
            )
            found_conflicts += 1
            missing_data.append((kdr, konto_nr_csv))
            continue

        print(
            f"Kundennummer: {kdr}, Konto Nr differ: Konto Nr CSV: {konto_nr_csv}, Konto Nr DB: {konto_nr_db}"
        )
        found_conflicts += 1

    if missing_data:
        print("\nYou need to fix missing KtrNr in database with:")

        for kd_nr, konto_nr in missing_data:
            print(f"UPDATE Kunden SET DatevKtrNr = {konto_nr} WHERE KdNr = {kd_nr};")  # noqa: S608 # nosec

    if not found_conflicts:
        print("No conflicts found. Database is up to date.")
