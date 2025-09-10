import json
from dataclasses import dataclass
from pathlib import Path
from tkinter import Button, Label, Tk, filedialog

settings_file = Path(__file__).parent.parent / "settings.json"


@dataclass
class Settings:
    pdf_path: Path = settings_file.parent
    xml_folder: Path = settings_file.parent

    def load_json(self):
        if not settings_file.exists():
            self.save()
        with open(settings_file, encoding="utf-8") as f:
            data = json.load(f)
            for key, value in data.items():
                match key:
                    case "pdf_path":
                        self.pdf_path = Path(value)
                    case "xml_folder":
                        self.xml_folder = Path(value)

    def __init__(self):
        super().__init__()
        self.load_json()

    def save(self):
        with open(settings_file, "w", encoding="utf-8") as f:
            to_save = {
                "pdf_path": str(self.pdf_path),
                "xml_folder": str(self.xml_folder),
            }
            json.dump(to_save, f, indent=4)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        self.save()

    def open_tk_settings_dialoge(self):
        window = Tk()
        window.title("Settings")
        window.geometry("300x200")

        # label + button to change pdf_path
        label = Label(window, text=f"PDF Path: {self.pdf_path}")
        label.pack()
        button = Button(
            window,
            text="Change PDF Path",
            command=lambda: self.change_pdf_path(label),
        )
        button.pack()

        # label + button to change xml_folder
        label2 = Label(window, text=f"XML Folder: {self.xml_folder}")
        label2.pack()
        button2 = Button(
            window,
            text="Change XML Folder",
            command=lambda: self.change_xml_folder(label2),
        )
        button2.pack()

        window.mainloop()

    def change_pdf_path(self, label: Label):
        new_path = filedialog.askdirectory()
        if new_path:
            self.pdf_path = Path(new_path)
            label.config(text=f"PDF Path: {self.pdf_path}")
            self.save()

    def change_xml_folder(self, label: Label):
        new_path = filedialog.askdirectory()
        if new_path:
            self.xml_folder = Path(new_path)
            label.config(text=f"XML Folder: {self.xml_folder}")
            self.save()
