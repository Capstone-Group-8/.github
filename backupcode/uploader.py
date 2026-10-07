"""
Capstone Group 8 - Invoice Processing System
Integrates business logic, OCR module, and frontend. Business logic controller.
Author: @slittle95
@sethzacharyroth-a11y contribution: Integrated PDF upload processing with OCR, validation,
and the human-in-the-loop invoice review workflow.
"""

import validation

import invoice_extraction.backend.parser_main as parser_main
from dateutil.parser import parse

from schemas import (
    InvoiceCreate,
    InvoiceLineItemCreate,
)


def upload(target_path):
    """
    Process an uploaded invoice through OCR and validation.

    Validation errors do not stop the upload because imperfect OCR
    results are expected to be reviewed and corrected in the UI.
    str => tuple[InvoiceCreate, list[InvoiceLineItemCreate], list[list[float, float]]]
    """
    metadata, lineitems, confidences = use_ocr(target_path)

    result = validation.validate(metadata, lineitems)

    if result != "200":
        print("\nInvoice requires human review:")
        print(result)

    return metadata, lineitems, confidences


def use_ocr(filepath): 
    """
    Convert OCR/parser output into application schema objects.
    str => tuple[InvoiceCreate, list[InvoiceLineItemCreate], list[list[float, float]]]
    """

    payload = parser_main.receive_file(filepath)
    #parser returns JSON object containing Invoice and InvoiceLineItems

    if not isinstance(payload, dict):
        raise ValueError("OCR parser did not return the expected invoice data.")

    metadata = payload.get("Invoice", {})
    parsed_lineitems = payload.get("InvoiceLineItems", [])

    invoice_number = metadata.get("InvoiceNumber", "")

    if not invoice_number:
        raise ValueError("OCR could not determine the invoice number.")

    if not metadata.get("OrderDate"):
        raise ValueError("OCR could not determine the order date.")

    if not metadata.get("ShipDate"):
        raise ValueError("OCR could not determine the ship date.")

    if not metadata.get("DueDate"):
        raise ValueError("OCR could not determine the due date.")

    shipping_handling = metadata.get("ShippingHandling", 0)

    if shipping_handling is None or shipping_handling < 0:
        shipping_handling = 0.0

    total_amt = metadata.get("TotalAmt", 0)

    if total_amt is None or total_amt < 0:
        total_amt = 0.0

    invoice = InvoiceCreate(
        InvoiceNumber=invoice_number,
        OrderDate=parse(metadata["OrderDate"]).date(),
        ShipDate=parse(metadata["ShipDate"]).date(),
        DueDate=parse(metadata["DueDate"]).date(),
        SalesOrderNo=metadata.get("SalesOrderNo", ""),
        ShippingHandling=float(shipping_handling),
        TotalAmt=float(total_amt),
        Supplier=metadata.get("Supplier", ""),
    )
    new_invoice_line_items = []
    confidence_intervals = []

    for item in parsed_lineitems:
        quantity = item.get("Quantity")

        if quantity is None:
            quantity = -1

        rate = item.get("Rate")

        # A missing OCR value must still be numeric for the
        # application/database. Zero flags it for human review.
        if rate is None:
            rate = 0.0

        amount = item.get("Amount")

        if amount is None:
            amount = 0.0

        new_item = InvoiceLineItemCreate(
            InvoiceNumber=invoice_number,
            Quantity=int(quantity),
            SuppliersID=item.get("SuppliersID", ""),
            SuppliersDesc=item.get("Description", ""),
            Rate=float(rate),
            Amount=float(amount),
            LineCount=item.get("LineCount"),
        )
        new_invoice_line_items.append(new_item)

        confidence_intervals.append(
            [
                float(item.get("OCRConfidence", 0) or 0),
                float(item.get("Confidence", 0) or 0),
            ]
        )

    return (
        invoice,
        new_invoice_line_items,
        confidence_intervals,

    )
def update(invoice, line_items):
    """
    Runs validation again when user edits.
    InvoiceCreate, list[InvoiceLineItemCreate] => str
    """
    result = validation.validate(invoice, line_items)
    if result == "200":
        return result
    else:
        pass #parse errors and pass all back to front end
