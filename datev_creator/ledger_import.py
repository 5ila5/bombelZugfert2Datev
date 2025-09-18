from dataclasses import dataclass
from typing import Literal, Sequence, TypeAlias, Union

from lxml import etree  # nosec B410

from datev_creator.utils import XmlBuilder

LedgerType: TypeAlias = Literal[
    "accountsPayableLedger", "accountsReceivableLedger", "cashLedger"
]


NAME_SPACE = "http://xml.datev.de/bedi/tps/ledger/v060"


def qn(tag: str) -> str:
    return f"{{{NAME_SPACE}}}{tag}"


@dataclass
class Base(XmlBuilder):
    """Element <base> (xsd:extension).

    Dieses Element enthält folgende Basisinformationen für den Datensatz:

    | Bezeichnung | Typ | Beschreibung | Kardinalität |
    |-------------|-----|--------------|--------------|
    | date | Element | Belegdatum | 1...1 |
    | amount | Element | Betrag (Brutto empfohlen) | 1...1 |
    | discountAmount | Element | Skontobetrag (Skontobetrag1) | 0...1 |
    | accountNo | Element | Sachkonto (Konto) 4-8 stellig (abhängig von Einstellungen) | 0...1 |
    | buCode | Element | Buchungsschlüssel | 0...1 |
    | costAmount | Element | Information für Kostenrechnung (KOST-Menge) | 0...1 |
    | costCategoryId | Element | Information für Kostenrechnung (KOST1) | 0...1 |
    | costCategoryId2 | Element | Information für Kostenrechnung (KOST2) | 0...1 |
    | tax | Element | Steuersatz (Steuer%) | 0...1 |
    | information | Element | Freitext 120 (Nachricht) | 0...1 |
    """

    date: str  # Belegdatum
    amount: str  # Betrag (Brutto empfohlen)
    discount_amount: str | None = None  # Skontobetrag (Skontobetrag1)
    account_no: str | None = None  # Sachkonto (Konto) 4-8 stellig
    bu_code: str | None = None  # Buchungsschlüssel
    cost_amount: str | None = None  # Information für Kostenrechnung (KOST-Menge)
    cost_category_id: str | None = None  # Information für Kostenrechnung (KOST1)
    cost_category_id2: str | None = None  # Information für Kostenrechnung (KOST2)
    tax: str | None = None  # Steuersatz (Steuer%)
    information: str | None = None  # Freitext 120 (Nachricht)

    @property
    def xml(self) -> etree._Element:
        base: etree._Element = etree.Element(qn("base"))

        etree.SubElement(base, qn("date")).text = self.date
        etree.SubElement(base, qn("amount")).text = self.amount

        if self.discount_amount is not None:
            etree.SubElement(base, qn("discountAmount")).text = self.discount_amount
        if self.account_no is not None:
            etree.SubElement(base, qn("accountNo")).text = self.account_no
        if self.bu_code is not None:
            etree.SubElement(base, qn("buCode")).text = self.bu_code
        if self.cost_amount is not None:
            etree.SubElement(base, qn("costAmount")).text = self.cost_amount
        if self.cost_category_id is not None:
            etree.SubElement(base, qn("costCategoryId")).text = self.cost_category_id
        if self.cost_category_id2 is not None:
            etree.SubElement(base, qn("costCategoryId2")).text = self.cost_category_id2
        if self.tax is not None:
            etree.SubElement(base, qn("tax")).text = self.tax
        if self.information is not None:
            etree.SubElement(base, qn("information")).text = self.information[:120]

        return base


@dataclass
class Base1(XmlBuilder):
    """Element <base1> (xsd:extension).

    Dieses Element enthält weitere Basisinformationen für den Datensatz:

    | Bezeichnung | Typ | Beschreibung | Kardinalität |
    |-------------|-----|--------------|--------------|
    | base | Element (xsd:extension) | Basisinformationen | 1...1 |
    | currencyCode | Element | 3-stelliges Währungskürzel gem. ISO 4217 | 1...1 |
    | invoiceId | Element | Rechnungsnummer | 1...1 |
    | bookingText | Element | Buchungstext (30 Zeichen) | 0...1 |
    | typeOfReceivable | Element | Forderungsart (OPOS-Informationen kommunal) | 0...1 |
    | ownVatId | Element | Eigene Umsatzsteuer-ID (insb. für OSS-Verfahren) | 0...1 |
    | shipFromCountry | Element | Nationalitätskennzeichen, 2 stellig gem. ISO3166 (insb. für OSS-Verfahren) | 0...1 |
    | partyId | Element | Kundennummer für Beleg | 0...1 |
    | paidAt | Element | Zahlungsdatum (Gezahlt am) Beleg erhält Stempel "bezahlt". | 0...1 |
    | internalInvoiceId | Element | interne Rechnungsnummer | 0...1 |
    | vatId | Element | Umsatzsteuer-ID des Geschäftspartners (insb. für OSS-Verfahren) | 0...1 |
    | shipToCountry | Element | Nationalitätskennzeichen, 2 stellig gem. ISO3166 (insb. für OSS-Verfahren) | 0...1 |
    | exchangeRate | Element | Umrechnungskurs | 0...1 |
    | bankCode | Element | Bankleitzahl | 0...1 |
    | bankAccount | Element | Bankkontonummer | 0...1 |
    | bankCountry | Element | Nationalitätskennzeichen, 2 stellig gem. ISO3166 | 0...1 |
    | iban | Element | IBAN | 0...1 |
    | swiftCode | Element | SWIFT/BIC-Code | 0...1 |
    | accountName | Element | Bezeichnung des Sachkontos | 0...1 |
    | paymentConditionsId | Element | Zahlungsbedingungsnummer | 0...1 |
    | paymentOrder | Element | Lastschrift/Überweisung erstellen angehakt | 0...1 |
    | discountPercentage | Element | Prozentsatz des Skontos (Skonto1 in %) | 0...1 |
    | discountPaymentDate | Element | Fälligkeitsdatum (Fällig (m. Skto. 1)) | 0...1 |
    | discountAmount2 | Element | Skontoinformation (Skontobetrag2) | 0...1 |
    | discountPercentage2 | Element | Prozentsatz des Skontos (Skonto2 in %) | 0...1 |
    | discountPaymentDate2 | Element | Fälligkeitsdatum (Fällig (m. Skto. 2)) | 0...1 |
    | dueDate | Element | Fälligkeitsdatum (Fällig (o. Skto.)) | 0...1 |
    | bpAccountNo | Element | Personenkonto | 0...1 |
    | deliveryDate | Element | Leistungsdatum | 0...1 |
    | orderId | Element | Auftragsnummer, z.B. von PayPal | 0...1 |
    """

    base: Base
    currency_code: str  # 3-stelliges Währungskürzel gem. ISO 4217
    invoice_id: str  # Rechnungsnummer
    booking_text: str | None = None  # Buchungstext (30 Zeichen)
    type_of_receivable: str | None = None  # Forderungsart (OPOS-Informationen kommunal)
    own_vat_id: str | None = None  # Eigene Umsatzsteuer-ID (insb. für OSS-Verfahren)
    ship_from_country: str | None = (
        None  # Nationalitätskennzeichen, 2 stellig gem. ISO3166
    )
    party_id: str | None = None  # Kundennummer für Beleg
    paid_at: str | None = None  # Zahlungsdatum (Gezahlt am)
    internal_invoice_id: str | None = None  # interne Rechnungsnummer
    vat_id: str | None = None  # Umsatzsteuer-ID des Geschäftspartners
    ship_to_country: str | None = (
        None  # Nationalitätskennzeichen, 2 stellig gem. ISO3166
    )
    exchange_rate: str | None = None  # Umrechnungskurs
    bank_code: str | None = None  # Bankleitzahl
    bank_account: str | None = None  # Bankkontonummer
    bank_country: str | None = None  # Nationalitätskennzeichen, 2 stellig gem. ISO3166
    iban: str | None = None  # IBAN
    swift_code: str | None = None  # SWIFT/BIC-Code
    account_name: str | None = None  # Bezeichnung des Sachkontos
    payment_conditions_id: str | None = None  # Zahlungsbedingungsnummer
    payment_order: str | None = None  # Lastschrift/Überweisung erstellen angehakt
    discount_percentage: str | None = None  # Prozentsatz des Skontos (Skonto1 in %)
    discount_payment_date: str | None = None  # Fälligkeitsdatum (Fällig (m. Skto. 1))
    discount_amount2: str | None = None  # Skontoinformation (Skontobetrag2)
    discount_percentage2: str | None = None  # Prozentsatz des Skontos (Skonto2 in %)
    discount_payment_date2: str | None = None  # Fälligkeitsdatum (Fällig (m. Skto. 2))
    due_date: str | None = None  # Fälligkeitsdatum (Fällig (o. Skto.))
    bp_account_no: str | None = None  # Personenkonto
    delivery_date: str | None = None  # Leistungsdatum
    order_id: str | None = None  # Auftragsnummer, z.B. von PayPal

    @property
    def xml(self) -> etree._Element:
        base1: etree._Element = etree.Element(qn("base1"))

        # Add the base elements as children as base is an xsd:extension
        for child in self.base.xml:
            base1.append(child)

        # Add required elements
        etree.SubElement(base1, qn("currencyCode")).text = self.currency_code
        etree.SubElement(base1, qn("invoiceId")).text = self.invoice_id

        # Add optional elements
        if self.booking_text is not None:
            etree.SubElement(base1, qn("bookingText")).text = self.booking_text[:30]
        if self.type_of_receivable is not None:
            etree.SubElement(
                base1, qn("typeOfReceivable")
            ).text = self.type_of_receivable
        if self.own_vat_id is not None:
            etree.SubElement(base1, qn("ownVatId")).text = self.own_vat_id
        if self.ship_from_country is not None:
            etree.SubElement(base1, qn("shipFromCountry")).text = self.ship_from_country
        if self.party_id is not None:
            etree.SubElement(base1, qn("partyId")).text = self.party_id
        if self.paid_at is not None:
            etree.SubElement(base1, qn("paidAt")).text = self.paid_at
        if self.internal_invoice_id is not None:
            etree.SubElement(
                base1, qn("internalInvoiceId")
            ).text = self.internal_invoice_id
        if self.vat_id is not None:
            etree.SubElement(base1, qn("vatId")).text = self.vat_id
        if self.ship_to_country is not None:
            etree.SubElement(base1, qn("shipToCountry")).text = self.ship_to_country
        if self.exchange_rate is not None:
            etree.SubElement(base1, qn("exchangeRate")).text = self.exchange_rate
        if self.bank_code is not None:
            etree.SubElement(base1, qn("bankCode")).text = self.bank_code
        if self.bank_account is not None:
            etree.SubElement(base1, qn("bankAccount")).text = self.bank_account
        if self.bank_country is not None:
            etree.SubElement(base1, qn("bankCountry")).text = self.bank_country
        if self.iban is not None:
            etree.SubElement(base1, qn("iban")).text = self.iban
        if self.swift_code is not None:
            etree.SubElement(base1, qn("swiftCode")).text = self.swift_code
        if self.account_name is not None:
            etree.SubElement(base1, qn("accountName")).text = self.account_name
        if self.payment_conditions_id is not None:
            etree.SubElement(
                base1, "paymentConditionsId"
            ).text = self.payment_conditions_id
        if self.payment_order is not None:
            etree.SubElement(base1, qn("paymentOrder")).text = self.payment_order
        if self.discount_percentage is not None:
            etree.SubElement(
                base1, "discountPercentage"
            ).text = self.discount_percentage
        if self.discount_payment_date is not None:
            etree.SubElement(
                base1, "discountPaymentDate"
            ).text = self.discount_payment_date
        if self.discount_amount2 is not None:
            etree.SubElement(base1, qn("discountAmount2")).text = self.discount_amount2
        if self.discount_percentage2 is not None:
            etree.SubElement(
                base1, "discountPercentage2"
            ).text = self.discount_percentage2
        if self.discount_payment_date2 is not None:
            etree.SubElement(
                base1, "discountPaymentDate2"
            ).text = self.discount_payment_date2
        if self.due_date is not None:
            etree.SubElement(base1, qn("dueDate")).text = self.due_date
        if self.bp_account_no is not None:
            etree.SubElement(base1, qn("bpAccountNo")).text = self.bp_account_no
        if self.delivery_date is not None:
            etree.SubElement(base1, qn("deliveryDate")).text = self.delivery_date
        if self.order_id is not None:
            etree.SubElement(base1, qn("orderId")).text = self.order_id

        return base1


@dataclass
class AccountsPayableLedger(XmlBuilder):
    """Element LedgerImport/consolidate/<accountsPayableLedger>.

    Dieses Element kann zur Abbildung verschiedener fachlicher Szenarien für eine
    Eingangsrechnung genutzt werden. Beim Import in die DATEV App wird dieses Element
    in einen Datensatz überführt.

    | Bezeichnung | Typ | Beschreibung | Kardinalität |
    |-------------|-----|--------------|--------------|
    | base1 | Element (xsd:extension) | Enthält diverse Datenfelder | 1...1 |
    | supplierName | Element | Name des Lieferanten | 0...1 |
    | supplierCity | Element | Standort des Lieferanten | 0...1 |
    """

    base1: Base1
    supplier_name: str | None = None  # Name des Lieferanten
    supplier_city: str | None = None  # Standort des Lieferanten

    @property
    def xml(self) -> etree._Element:
        ledger: etree._Element = etree.Element(qn("accountsPayableLedger"))

        # Add the base1 element's children directly to this element
        base1_xml = self.base1.xml
        for child in base1_xml:
            ledger.append(child)

        # Add optional elements
        if self.supplier_name is not None:
            etree.SubElement(ledger, qn("supplierName")).text = self.supplier_name
        if self.supplier_city is not None:
            etree.SubElement(ledger, qn("supplierCity")).text = self.supplier_city

        return ledger


@dataclass
class AccountsReceivableLedger(XmlBuilder):
    """Element LedgerImport/consolidate/<accountsReceivableLedger>.

    Dieses Element kann zur Abbildung verschiedener fachlicher Szenarien für eine
    Ausgangsrechnung genutzt werden. Beim Import in die DATEV App wird dieses Element
    in einen Datensatz überführt.

    | Bezeichnung | Typ | Beschreibung | Kardinalität |
    |-------------|-----|--------------|--------------|
    | base1 | Element (xsd:extension) | Enthält diverse Datenfelder | 1...1 |
    | customerName | Element | Name des Kunden | 0...1 |
    | customerCity | Element | Standort des Kunden | 0...1 |
    """

    base1: Base1
    customer_name: str | None = None  # Name des Kunden
    customer_city: str | None = None  # Standort des Kunden

    @property
    def xml(self) -> etree._Element:
        ledger: etree._Element = etree.Element(qn("accountsReceivableLedger"))

        # Add the base1 element's children directly to this element
        base1_xml = self.base1.xml
        for child in base1_xml:
            ledger.append(child)

        # Add optional elements
        if self.customer_name is not None:
            etree.SubElement(ledger, qn("customerName")).text = self.customer_name
        if self.customer_city is not None:
            etree.SubElement(ledger, qn("customerCity")).text = self.customer_city

        return ledger


@dataclass
class CashLedger(XmlBuilder):
    """Element LedgerImport/consolidate/<cashLedger>.

    Dieses Element kann zur Abbildung verschiedener fachlicher Szenarien für eine
    Kasse genutzt werden. Beim Import in die DATEV App wird dieses Element in einen
    Datensatz überführt.

    | Bezeichnung | Typ | Beschreibung | Kardinalität |
    |-------------|-----|--------------|--------------|
    | base | Element (xsd:extension) | Enthält diverse Datenfelder | 1...1 |
    | currencyCode | Element | Währungscode, für Kassendaten nur "EUR" zulässig | 1...1 |
    | invoiceId | Element | ID der Transaktion | 0...1 |
    | bookingText | Element | Buchungstext | 1...1 |
    """

    base: Base
    currency_code: str  # Währungscode, für Kassendaten nur "EUR" zulässig
    booking_text: str  # Buchungstext
    invoice_id: str | None = None  # ID der Transaktion

    @property
    def xml(self) -> etree._Element:
        ledger: etree._Element = etree.Element(qn("cashLedger"))

        # Add the base element's children directly to this element
        base_xml = self.base.xml
        for child in base_xml:
            ledger.append(child)

        # Add required elements
        etree.SubElement(ledger, qn("currencyCode")).text = self.currency_code
        etree.SubElement(ledger, qn("bookingText")).text = self.booking_text

        # Add optional elements
        if self.invoice_id is not None:
            etree.SubElement(ledger, qn("invoiceId")).text = self.invoice_id

        return ledger


@dataclass
class Consolidate(XmlBuilder):
    """Element LedgerImport/<consolidate>.

    Dieses Element bildet die äußerste Klammer für die konkreten Daten einer Rechnung/Kasse.

    | Bezeichnung | Typ | Beschreibung | Kardinalität |
    |-------------|-----|--------------|--------------|
    | consolidatedAmount | Attribut | Summe der einzelnen Positionsbeträge | 1...1 |
    | consolidatedDate | Attribut | Datum der Rechnung/Kassentransaktion | 1...1 |
    | consolidatedInvoiceId | Attribut | ID der Rechnung/Kassentransaktion | 0...1 |
    | consolidatedDeliveryDate | Attribut | Leistungsdatum. Pflicht, wenn in base1 verwendet | 0...1 |
    | consolidatedOrderId | Attribut | Transaktions-ID für Zahlungsreferenz. Pflicht, wenn in base1 verwendet | 0...1 |
    | consolidatedCurrencyCode | Attribut | 3-stelliges Währungskürzel gem. ISO 4217 | 1...1 |
    | ledgers | Element (xsd:choice) | Daten für Eingangs-/Ausgangsrechnung/Kasse | 1...5000 |
    """

    consolidated_amount: str  # Summe der einzelnen Positionsbeträge
    consolidated_date: str  # Datum der Rechnung/Kassentransaktion
    consolidated_currency_code: str  # 3-stelliges Währungskürzel gem. ISO 4217
    ledgers: Sequence[
        Union[AccountsPayableLedger, AccountsReceivableLedger, CashLedger]
    ]  # 1...5000
    consolidated_invoice_id: str | None = None  # ID der Rechnung/Kassentransaktion
    consolidated_delivery_date: str | None = None  # Leistungsdatum
    consolidated_order_id: str | None = None  # Transaktions-ID für Zahlungsreferenz

    @property
    def xml(self) -> etree._Element:
        attributes: dict[str, str] = {
            "consolidatedAmount": self.consolidated_amount,
            "consolidatedDate": self.consolidated_date,
            "consolidatedCurrencyCode": self.consolidated_currency_code,
        }

        if self.consolidated_invoice_id is not None:
            attributes["consolidatedInvoiceId"] = self.consolidated_invoice_id
        if self.consolidated_delivery_date is not None:
            attributes["consolidatedDeliveryDate"] = self.consolidated_delivery_date
        if self.consolidated_order_id is not None:
            attributes["consolidatedOrderId"] = self.consolidated_order_id

        consolidate: etree._Element = etree.Element(
            qn("consolidate"),
            attrib=attributes,
            nsmap=None,
        )

        for ledger in self.ledgers:
            consolidate.append(ledger.xml)

        return consolidate


@dataclass
class LedgerImport(XmlBuilder):
    """Das Rootelement LedgerImport.

    | Bezeichnung | Typ | Beschreibung | Kardinalität |
    |-------------|-----|--------------|--------------|
    | xmlns | Attribut | verwendete XSD-Version, aktuell: "http://xml.datev.de/bedi/tps/ledger/v060" | 1...1 |
    | xmlns:xsi | Attribut | fester Inhalt "http://www.w3.org/2001/XMLSchema-instance" | 1...1 |
    | xsi:schemaLocation | Attribut | verwendete XSD-Version, aktuell: "http://xml.datev.de/bedi/tps/ledger/v060 Belegverwaltung_online_ledger_import_v060.xsd" | 1...1 |
    | generator_info | Attribut | Unternehmen, welches die XML-Datei erzeugt hat | 1...1 |
    | version | Attribut | verwendete XSD-Version, aktuell: "6.0" | 1...1 |
    | xml_data | Attribut | fester Hinweis zum Vorsteuerabzug | 1...1 |
    | generating_system | Attribut | Software, welche die XML-Datei erzeugt hat | 0...1 |
    | consolidate | Element | Beinhaltet die konkreten Daten einer Rechnung/Kasse | 1...1 |
    """

    generator_info: str  # Unternehmen, welches die XML-Datei erzeugt hat
    xml_data: str  # fester Hinweis zum Vorsteuerabzug
    consolidate: Consolidate
    xmlns: str = NAME_SPACE
    xmlns_xsi: Literal["http://www.w3.org/2001/XMLSchema-instance"] = (
        "http://www.w3.org/2001/XMLSchema-instance"
    )
    xsi_schema_location: str = (
        f"{NAME_SPACE} Belegverwaltung_online_ledger_import_v060.xsd"
    )
    version: str = "6.0"
    generating_system: str | None = None  # Software, welche die XML-Datei erzeugt hat

    @property
    def xml(self) -> etree._ElementTree:
        attributes: dict[str, str] = {
            "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": self.xsi_schema_location,
            "version": self.version,
            "generator_info": self.generator_info,
            "xml_data": self.xml_data,
        }
        print(attributes)
        if self.generating_system is not None:
            attributes["generating_system"] = self.generating_system

        xml: etree._Element = etree.Element(
            qn("LedgerImport"),
            attrib=attributes,
            nsmap={
                None: self.xmlns,
                "xsi": self.xmlns_xsi,
            },
        )

        xml.append(self.consolidate.xml)

        return etree.ElementTree(xml)
