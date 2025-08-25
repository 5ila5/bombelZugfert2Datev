from pathlib import Path
from tkinter import Tk
from tkinter.ttk import Treeview

from datev_creator.ledger_import import (
    AccountsPayableLedger,
    AccountsReceivableLedger,
    CashLedger,
    LedgerImport,
)

LedgerImportWMetadata = tuple[LedgerImport, tuple[int, int]]


class XmlInspector:
    @staticmethod
    def tree_view_add_attr(tree_view: Treeview, parent: str, obj, attribute: str):
        attr = str(getattr(obj, attribute))
        tree_view.insert(
            parent,
            "end",
            text=attribute,
            values=(attr,),
        )

    def __init__(self, pdf_path: Path, data: LedgerImportWMetadata):
        self.pdf_path = pdf_path
        self.data = data

        ledger: LedgerImport = data[0]

        # new Tkinter window
        self.window = Tk()
        self.window.title(f"Inspecting1 {pdf_path.name}")
        self.window.geometry("400x300")

        tree_view = Treeview(
            self.window,
            columns=("value",),
        )

        tree_view.column(
            "#0",
            width=150,
            minwidth=150,
        )
        tree_view.column("value", width=300, minwidth=300)

        tree_view.heading("#0", text="Field", anchor="w")
        tree_view.heading("value", text="Value", anchor="w")

        tree_view.tag_configure("expandable", background="#919191")  # pale yellow

        tree_view.insert("", "end", text="PDF Path", values=(str(pdf_path),))
        tree_view.insert(
            "", "end", text="Year/Month", values=(f"{data[1][0]}/{data[1][1]}",)
        )

        tree_view.insert(
            "", "end", text="generator_info", values=(str(ledger.generator_info),)
        )
        tree_view.insert("", "end", text="xml_data", values=(str(ledger.xml_data),))

        # consolidate
        consolidate = tree_view.insert(
            "", "end", text="consolidate", values=("",), tags=("expandable",)
        )

        for attr in [
            "consolidated_amount",
            "consolidated_date",
            "consolidated_currency_code",
        ]:
            self.tree_view_add_attr(tree_view, consolidate, ledger.consolidate, attr)

        # ledgers
        ledgers = tree_view.insert(
            consolidate,
            "end",
            text="ledgers",
            values=("",),
            tags=("expandable",),
        )

        for ledger_item in ledger.consolidate.ledgers:
            if isinstance(ledger_item, AccountsPayableLedger):
                ledger_item_id = tree_view.insert(
                    ledgers,
                    "end",
                    text="AccountsPayableLedger",
                    values=("",),
                    tags=("expandable",),
                )
                # Not handled further for now
            elif isinstance(ledger_item, AccountsReceivableLedger):
                ledger_item_id = tree_view.insert(
                    ledgers,
                    "end",
                    text="LedgerImport",
                    values=("",),
                    tags=("expandable",),
                )

                # base1
                base1 = tree_view.insert(
                    ledger_item_id,
                    "end",
                    text="base1",
                    values=("",),
                    tags=("expandable",),
                )

                # base

                base = tree_view.insert(
                    base1,
                    "end",
                    text="base",
                    values=("",),
                    tags=("expandable",),
                )

                base_children = [
                    "date",
                    "amount",
                    "discount_amount",
                    "account_no",
                    "bu_code",
                    "cost_amount",
                    "cost_category_id",
                    "cost_category_id2",
                    "tax",
                    "information",
                ]
                for attr in base_children:
                    self.tree_view_add_attr(
                        tree_view, base, ledger_item.base1.base, attr
                    )

                # end base

                base1_children = [
                    "currency_code",
                    "invoice_id",
                    "booking_text",
                    "type_of_receivable",
                    "own_vat_id",
                    "ship_from_country",
                    "party_id",
                    "paid_at",
                    "internal_invoice_id",
                    "vat_id",
                    "ship_to_country",
                    "exchange_rate",
                    "bank_code",
                    "bank_account",
                    "bank_country",
                    "iban",
                    "swift_code",
                    "account_name",
                    "payment_conditions_id",
                    "payment_order",
                    "discount_percentage",
                    "discount_payment_date",
                    "discount_amount2",
                    "discount_percentage2",
                    "discount_payment_date2",
                    "due_date",
                    "bp_account_no",
                    "delivery_date",
                    "order_id",
                ]
                for attr in base1_children:
                    self.tree_view_add_attr(tree_view, base1, ledger_item.base1, attr)

                # end base1
                for attr in ["customer_name", "customer_city"]:
                    self.tree_view_add_attr(
                        tree_view, ledger_item_id, ledger_item, attr
                    )

            elif isinstance(ledger_item, CashLedger):
                ledger_item_id = tree_view.insert(
                    ledgers,
                    "end",
                    text="CashLedger",
                    values=("",),
                    tags=("expandable",),
                )
                # not handled further for now

        #

        for attr in [
            "consolidated_invoice_id",
            "consolidated_delivery_date",
            "consolidated_order_id",
        ]:
            self.tree_view_add_attr(tree_view, consolidate, ledger.consolidate, attr)

        # end consolidate

        for attr in [
            "xmlns",
            "xmlns_xsi",
            "xsi_schema_location",
            "version",
            "generating_system",
        ]:
            self.tree_view_add_attr(tree_view, "", ledger, attr)

        tree_view.pack(side="top", fill="both", expand=True)

    def run(self):
        self.window.mainloop()
