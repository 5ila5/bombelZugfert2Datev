from pathlib import Path
from tkinter import messagebox
from tkinter.filedialog import askdirectory, askopenfilenames

from pypdf import PdfReader


def main():
    pdf_paths = askopenfilenames(
        title="Select PDF files",
        filetypes=[("PDF files", "*.pdf")],
        initialdir=Path(__file__).parent,
        # initialdir=Path.home(),
    )

    if len(pdf_paths) == 0:
        messagebox.showinfo("No files selected", "No PDF files were selected.")
        return

    xml_dir = askdirectory(
        title="Select Directory to Save XML Files",
        initialdir=Path(__file__).parent,
        # initialdir=Path.home(),
    )
    if not xml_dir:
        messagebox.showinfo("No directory selected", "No directory was selected.")
        return
    xml_folder = Path(xml_dir)

    for pdf in pdf_paths:
        pdf = Path(pdf)
        if not pdf.exists() or not pdf.is_file():
            messagebox.showerror(
                "File Error", f"The file {pdf} does not exist or is not a file."
            )
            return None

        extract_xml_from_pdf(pdf, xml_folder)


def extract_xml_from_pdf(pdf: Path, xml_folder: Path) -> Path | None:
    file_name = pdf.name
    # pdf = Path(file_name)
    reader = PdfReader(pdf)
    attachments = {}

    catalog = reader.trailer["/Root"]
    print(catalog)
    if "/Names" in catalog and "/EmbeddedFiles" in catalog["/Names"]:
        fileNames = catalog["/Names"]["/EmbeddedFiles"]["/Names"]
        for f in fileNames:
            print(f)
            if isinstance(f, str) and f == "factur-x.xml":
                name = f
                dataIndex = fileNames.index(f) + 1
                fDict = fileNames[dataIndex].get_object()
                fData = fDict["/EF"]["/F"].get_data()
                attachments[name] = fData

                tempdir_path = xml_folder / (file_name + ".xml")
                with open(tempdir_path, "wb") as xml_file:
                    xml_file.write(fData)
                return tempdir_path
    return None


if __name__ == "__main__":
    main()
