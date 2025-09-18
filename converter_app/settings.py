import json
from dataclasses import dataclass
from pathlib import Path
from tkinter import Button, Entry, Label, Tk, filedialog
from typing import Optional

settings_file = Path(__file__).parent.parent / "settings.json"


settings_instance: Optional["Settings"] = None


@dataclass
class Settings:
    pdf_path: Path = settings_file.parent
    xml_folder: Path = settings_file.parent
    beraternummer: int = 0
    mandantennummer: int = 0
    sachkontenlaenge = 4
    buchungskonto = 0

    def check_csv_settings(self) -> bool:
        if self.beraternummer <= 0:
            return False
        if self.mandantennummer <= 0:
            return False
        if self.sachkontenlaenge <= 0:
            return False
        if self.buchungskonto <= 0:
            return False
        return True

    @staticmethod
    def getinstance() -> "Settings":
        global settings_instance
        if settings_instance is None:
            settings_instance = Settings()
        return settings_instance

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
                    case "beraternummer":
                        self.beraternummer = int(value)
                    case "mandantennummer":
                        self.mandantennummer = int(value)
                    case "sachkontenlaenge":
                        self.sachkontenlaenge = int(value)
                    case "buchungskonto":
                        self.buchungskonto = int(value)

    def __init__(self):
        super().__init__()
        self.load_json()

    def save(self):
        with open(settings_file, "w", encoding="utf-8") as f:
            to_save = {
                "pdf_path": str(self.pdf_path),
                "xml_folder": str(self.xml_folder),
                "beraternummer": self.beraternummer,
                "mandantennummer": self.mandantennummer,
                "sachkontenlaenge": self.sachkontenlaenge,
                "buchungskonto": self.buchungskonto,
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

        # sachkontenlaenge selector 4,5,6,7,8
        label3 = Label(window, text=f"Sachkontenlänge: {self.sachkontenlaenge}")
        label3.pack()

        def increase_sachkontenlaenge():
            if self.sachkontenlaenge < 8:
                self.sachkontenlaenge += 1
                label3.config(text=f"Sachkontenlänge: {self.sachkontenlaenge}")
                self.save()

        def decrease_sachkontenlaenge():
            if self.sachkontenlaenge > 4:
                self.sachkontenlaenge -= 1
                label3.config(text=f"Sachkontenlänge: {self.sachkontenlaenge}")
                self.save()

        button3 = Button(window, text="+", command=increase_sachkontenlaenge)
        button3.pack()
        button4 = Button(window, text="-", command=decrease_sachkontenlaenge)
        button4.pack()
        # end sachkontenlaenge selector

        # number input for beraternummer, mandantennummer, buchungskonto
        def create_number_input(label_text: str, attr_name: str):
            # actual input field
            label = Label(window, text=f"{label_text}: {getattr(self, attr_name)}")
            label.pack()
            entry = Entry(window)

            # entry.insert(0, str(getattr(self, attr_name)))
            entry.pack()

            def save_number():
                try:
                    value = int(entry.get())
                    setattr(self, attr_name, value)
                    label.config(text=f"{label_text}: {value}")
                    self.save()
                except ValueError:
                    pass

            button = Button(window, text="Save", command=save_number)
            button.pack()
            return label, entry, button

        create_number_input("Beraternummer", "beraternummer")
        create_number_input("Mandantennummer", "mandantennummer")
        create_number_input("Buchungskonto", "buchungskonto")

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
