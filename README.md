# BombelZugfert2Datev

Create Datev archive from zugfert/X-Rechnung files.

This is a script specifically designed for our use case and probably won't work for you without modifications.

## Instalation

```sh
git clone https://github.com/5ila5/bombelZugfert2Datev
cd bombelZugfert2Datev
```

## Usage

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run the script:

```sh
python archive_builder.py
```

You will then be prompted to select pdf files. After this you'll be prompted to select a directory where the X-Rechnung xml files are located. They need to have the same name as the pdf files, but with `.xml` instad of `.pdf` extension. Then you'll be prompted to select a zip output file. The script will create a Datev archive as the selected zip file.
