from pathlib import Path
from typing import Callable

from drafthorse.models.document import Document
from drafthorse.models.party import TaxRegistration
from drafthorse.models.payment import PaymentTerms
from drafthorse.models.tradelines import LineItem, LineSettlement, LineSummation

from datev_creator.ledger_import import (
    AccountsReceivableLedger,
    Base,
    Base1,
    Consolidate,
    LedgerImport,
)
from datev_creator.utils import SOFTWARE_NAME

LEDGER_XML_DATA = "Kopie nur zur Verbuchung berechtigt nicht zum Vorsteuerabzug"


def import_zugfert(xml_path: Path) -> Document:
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    with open(xml_path, "rb") as f:
        xml = f.read()

    return Document.parse(xml)


def retrieve_ledgers(
    document: Document,
    account_no_retrieval: Callable[[str | None, str], str | None],
) -> list[AccountsReceivableLedger]:
    """Retrieve ledgers from FractureX xml document.

    Args:
        document (Document): The drafthorse Document object.
        account_no_retrieval (Callable[[str | None, str], str | None]): function retrieveing account_no given a [customer_number] and invoice ID.

    Raises:
        ValueError: when tax rate is not 0% or 19%

    Returns:
        list[AccountsReceivableLedger]: The list of ledgers.

    """
    ledgers: list[AccountsReceivableLedger] = []
    item: LineItem
    settlement: LineSettlement
    monetary_summation: LineSummation
    for item in document.trade.items.children:
        # Get item amount - try different price sources
        item_amount = ""
        if (
            hasattr(item, "settlement")
            and (settlement := item.settlement)
            and hasattr(settlement, "monetary_summation")
            and (monetary_summation := settlement.monetary_summation)
        ):
            item_amount = str(monetary_summation.total_amount.__str__())
        elif (
            hasattr(item, "agreement")
            and item.agreement
            and hasattr(item.agreement, "gross")
            and item.agreement.gross
        ):
            item_amount = str(item.agreement.gross.amount)
        elif (
            hasattr(item, "agreement")
            and item.agreement
            and hasattr(item.agreement, "net")
            and item.agreement.net
        ):
            item_amount = str(item.agreement.net.amount)

        # Get tax rate from settlement.trade_tax
        tax_rate: str | None = None
        tax_rate_float: float | None = None
        if (
            hasattr(item, "settlement")
            and item.settlement
            and hasattr(item.settlement, "trade_tax")
            and item.settlement.trade_tax
            and hasattr(item.settlement.trade_tax, "rate_applicable_percent")
        ):
            tax_rate_float = float(
                str(item.settlement.trade_tax.rate_applicable_percent.__str__())
            )
            tax_rate = f"{tax_rate_float:.2f}"

        # Get seller tax ID
        tax_registrations: list[TaxRegistration]
        seller_tax_id = None
        if (
            hasattr(document.trade.agreement.seller, "tax_registrations")
            and (document.trade.agreement.seller.tax_registrations)
            and (
                tax_registrations
                := document.trade.agreement.seller.tax_registrations.children
            )
            and len(tax_registrations) > 0
        ):
            seller_tax_id = (
                str(tax_registrations[0].id).strip().removesuffix("(VA)").strip()
            )

        # Get buyer tax ID
        buyer_tax_id = None
        if (
            hasattr(document.trade.agreement.buyer, "tax_registrations")
            and document.trade.agreement.buyer.tax_registrations
            and (
                tax_registrations
                := document.trade.agreement.buyer.tax_registrations.children
            )
            and len(tax_registrations) > 0
        ):
            buyer_tax_id = str(tax_registrations[0].id)

        # Get country codes
        ship_from_country = None
        if (
            hasattr(document.trade.agreement.seller, "address")
            and document.trade.agreement.seller.address
            and hasattr(document.trade.agreement.seller.address, "country_id")
        ):
            ship_from_country = str(document.trade.agreement.seller.address.country_id)

        ship_to_country = None
        if (
            hasattr(document.trade.agreement.buyer, "address")
            and document.trade.agreement.buyer.address
            and hasattr(document.trade.agreement.buyer.address, "country_id")
        ):
            ship_to_country = str(document.trade.agreement.buyer.address.country_id)

        # Get due date from settlement terms
        terms: list[PaymentTerms]
        due_date = None
        if (
            hasattr(document.trade.settlement, "terms")
            and document.trade.settlement.terms
            and (terms := document.trade.settlement.terms.children)
            and hasattr(terms, "due")
        ):
            due_date = str(terms[0].due)

        # Get delivery date from delivery event occurrence
        delivery_date = None
        if (
            hasattr(document.trade.delivery, "event")
            and document.trade.delivery.event
            and hasattr(document.trade.delivery.event, "occurrence")
        ):
            delivery_date = str(document.trade.delivery.event.occurrence)

        # Get buyer order reference - correct attribute name is buyer_order
        order_id = None
        if (
            hasattr(document.trade.agreement, "buyer_order")
            and document.trade.agreement.buyer_order
            and hasattr(document.trade.agreement.buyer_order, "issuer_assigned_id")
            and document.trade.agreement.buyer_order.issuer_assigned_id._data
        ):
            print(document.trade.agreement.buyer_order.issuer_assigned_id)
            order_id = str(document.trade.agreement.buyer_order.issuer_assigned_id)

        # BU CODE only works for our use case where only two BU Codes are used (19% or 0%) (where 0% is 200)
        bu_code: str
        if tax_rate_float == 19.0:
            bu_code = "3"
        elif tax_rate_float == 0.0:
            bu_code = "200"
        else:
            raise ValueError(f"Unexpected tax rate: {tax_rate_float}")

        buyer_id = (
            str(document.trade.agreement.buyer.id)
            if hasattr(document.trade.agreement.buyer, "id")
            else None
        )
        if document.header.id:
            invoice_id = str(document.header.id)
        else:
            raise ValueError("Invoice needs to have an ID, but it does not.")

        ledgers.append(
            AccountsReceivableLedger(
                base1=Base1(
                    base=Base(
                        date=str(document.header.issue_date_time)
                        if document.header.issue_date_time
                        else "",
                        amount=item_amount,
                        discount_amount=None,
                        account_no=account_no_retrieval(buyer_id, invoice_id),
                        bu_code=bu_code,
                        cost_amount=None,
                        cost_category_id=None,
                        cost_category_id2=None,
                        tax=tax_rate,
                        information=str(item.product.name)[:120]
                        if item.product and item.product.name
                        else None,
                    ),
                    currency_code=str(document.trade.settlement.currency_code)
                    if document.trade.settlement.currency_code
                    else "EUR",
                    invoice_id=invoice_id,
                    booking_text=str(item.product.name)[:30]
                    if item.product and item.product.name
                    else None,
                    type_of_receivable=None,
                    own_vat_id=seller_tax_id,
                    ship_from_country=ship_from_country,
                    party_id=buyer_id,
                    paid_at=None,
                    internal_invoice_id=None,
                    vat_id=buyer_tax_id,
                    ship_to_country=ship_to_country,
                    exchange_rate=None,
                    bank_code=None,
                    bank_account=None,
                    bank_country=None,
                    iban=None,
                    swift_code=None,
                    account_name=None,
                    payment_conditions_id=None,
                    payment_order=None,
                    discount_percentage=None,
                    discount_payment_date=None,
                    discount_amount2=None,
                    discount_percentage2=None,
                    discount_payment_date2=None,
                    due_date=due_date,
                    bp_account_no=None,
                    delivery_date=delivery_date,
                    order_id=order_id,
                ),
                customer_name=str(document.trade.agreement.buyer.name),
                customer_city=str(document.trade.agreement.buyer.address.city_name)
                if document.trade.agreement.buyer.address
                else None,
            )
        )

    return ledgers


def zugfert_to_ledger_import(
    xml_path: Path,
    account_no_retrieval: Callable[
        [str | None, str], str | None
    ] = lambda customer_number, invoice_id: None,
) -> tuple[LedgerImport, tuple[int, int]]:
    """Convert a Zugferd XML file to a LedgerImport XML string.

    xml_path (Path): Path to the Zugferd XML file.
    account_no_retrieval (Callable[[str | None, str], str | None]): function retrieveing account_no given a [customer_number] and invoice ID.

    Returns:
        tuple: (etree._ElementTree, year, month)

    """
    document = import_zugfert(xml_path)
    ledgers = retrieve_ledgers(document, account_no_retrieval)

    print(
        f"{document.trade.settlement.monetary_summation.grand_total=}, {type(document.trade.settlement.monetary_summation.grand_total)=}"
    )

    ledger_import_xml = LedgerImport(
        generator_info=str(document.trade.agreement.seller.name),
        xml_data=LEDGER_XML_DATA,
        consolidate=Consolidate(
            # find document reference in /home/silas/Documents/coding/python/datev/.venv/lib/python3.13/site-packages/drafthorse/models/*
            consolidated_amount=str(
                document.trade.settlement.monetary_summation.grand_total._amount
            ),
            #             ExchangedDocument
            # IssueDateTime
            # DateTimeString
            consolidated_date=str(document.header.issue_date_time),
            consolidated_currency_code=str(document.trade.settlement.currency_code),
            ledgers=ledgers,
            consolidated_invoice_id=str(document.header.id),
            consolidated_delivery_date=str(document.trade.delivery.event.occurrence),
            consolidated_order_id=None,
        ),
        generating_system=SOFTWARE_NAME,
    )
    split_date = str(document.header.issue_date_time).split("-")
    return ledger_import_xml, (
        int(split_date[0]),
        int(split_date[1]),
    )
