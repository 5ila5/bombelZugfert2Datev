from pathlib import Path


def validate_database_information_exists():
    # check if this script directory has a subdirectory called database
    script_dir = Path(__file__).parent
    database_dir = script_dir / "database"
    if not database_dir.exists():
        # create database directory
        database_dir.mkdir()

    # check if credentials.py exists in database directory
    credentials_file = database_dir / "credentials.py"
    if not credentials_file.exists():
        with open(credentials_file, "w", encoding="utf-8") as f:
            f.write("""import mysql.connector

mydb = mysql.connector.connect(
    host="", user="", password="", database=""
)""")


try:
    from .database.credentials import mydb
except ImportError:
    validate_database_information_exists()
    raise


def get_datev_account_no(customer_number: str | None, invoice_id: str) -> str | None:
    if customer_number is not None:
        SQL = "SELECT DatevKtrNr FROM Kunden WHERE KdNr = %s"
        mycursor = mydb.cursor()
        mycursor.execute(SQL, (customer_number,))
        result = mycursor.fetchone()
        if (
            result
            and isinstance(result, tuple)
            and (isinstance(result[0], str) or isinstance(result[0], int))
            and result[0]
        ):
            return str(result[0])
    SQL = """SELECT DatevKtrNr FROM Rechnungen
    JOIN Kunden ON Rechnungen.Kdidx = Kunden.KdIdx
    WHERE RgNr = %s"""

    mycursor = mydb.cursor()
    mycursor.execute(SQL, (invoice_id,))
    result = mycursor.fetchone()
    if (
        result
        and isinstance(result, tuple)
        and (isinstance(result[0], str) or isinstance(result[0], int))
        and result[0]
    ):
        return str(result[0])
    return None
