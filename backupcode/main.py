"""
Capstone Group 8 - Invoice Processing System
Defines the FastAPI application for the invoice processing system. It includes endpoints for managing invoices, line items, inventory, suppliers, and change logs. 
The application uses SQLAlchemy for database interactions and Pydantic for data validation.
Author: @slittle95
"""
import os
import aiofiles
import datetime

from fastapi import Depends, FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session 
#from pathlib import Path

import crud
import models

from invoice_extraction.backend.parser_main import process_file, BASE_DIR, DROPBOX
import uploader
import inventory_updater
from database import SessionLocal, engine
from schemas import (
    Inventory,
    InventoryCreate,
    InventoryUpdate,
    Invoice,
    InvoiceCreate,
    InvoiceLineItem,
    InvoiceLineItemCreate,
    InvoiceLineItemUpdate,
    InvoiceUpdate,
    Supplier,
    ChangeLog,
    ChangeLogCreate,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Invoice Processing System API", version="0.1.0-alpha")

origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# GET
""" @app.get("/health")
def health():
    return {"status": "ok"} """

@app.get("/invoices/all", response_model=list[Invoice])
def read_invoices(db: Session = Depends(get_db)):
    return crud.get_invoices(db)

@app.get("/inventory", response_model=list[Inventory])
def read_inventory(db: Session = Depends(get_db)):
    return crud.get_all_inventory(db)

@app.get("/suppliers", response_model=list[Supplier])
def read_suppliers(db: Session = Depends(get_db)):
    return crud.get_suppliers(db)

@app.get("/changes", response_model=list[ChangeLog])
def read_all_changes(db: Session = Depends(get_db)):
    return crud.get_all_changes(db)


@app.get("/invoices/{InvoiceNumber}", response_model=Invoice)
def read_invoice(InvoiceNumber: str, db: Session = Depends(get_db)):
    #print(f"Fetching invoice using: {InvoiceNumber} calling crud.get_invoice from line 84 of main.py")
    invoice = crud.get_invoice(db, InvoiceNumber)
    if not invoice:
        raise HTTPException(status_code=404, detail="invoice not found")
    return invoice

@app.get("/invoices/{InvoiceNumber}/lineitems", response_model=list[InvoiceLineItem])
def read_invoice_items(InvoiceNumber: str, db: Session = Depends(get_db)):
    return crud.get_line_items(db, InvoiceNumber)

@app.get("/inventory/{ProductID}", response_model=Inventory)
def read_inventory_entry(ProductID: str, db: Session = Depends(get_db)):
    inventory_entry = crud.get_inventory_entry(db, ProductID)
    if not inventory_entry:
        raise HTTPException(status_code=404, detail="inventory entry not found")
    return inventory_entry

@app.get("/invoices/{InvoiceNumber}/changes", response_model=list[ChangeLog])
def read_invoice_changes(InvoiceNumber: str, db: Session = Depends(get_db)):
    return crud.get_invoice_changes(db, InvoiceNumber)

@app.get("/invoices/{InvoiceNumber}/changes/{ChangeID}", response_model=ChangeLog)
def read_change(ChangeID: int, db: Session = Depends(get_db)):
    return crud.get_change(db, ChangeID)


#POST
@app.post("/invoices/all", response_model=Invoice, status_code=201)
def create_new_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    return crud.create_invoice(db, invoice)

@app.post("/invoices/{InvoiceNumber}/lineitems", response_model=InvoiceLineItem, status_code=201)
def create_new_line_item(InvoiceNumber: str, line_item: InvoiceLineItemCreate, db: Session = Depends(get_db)):
    if line_item.InvoiceNumber != InvoiceNumber:
        raise HTTPException(status_code=400, detail="Invoice number does not match request path")
    return crud.create_line_item(db, line_item)

@app.post("/inventory", response_model=Inventory, status_code=201)
def create_new_inventory_entry(entry: InventoryCreate, db: Session = Depends(get_db)):
    return crud.create_inventory_entry(db, entry)

@app.post("/invoices/{InvoiceNumber}/changes", response_model=ChangeLog, status_code=201)
def create_change(change: ChangeLogCreate, db: Session = Depends(get_db)):
    return crud.create_change(db, change)


#PUT
@app.put("/invoices/{InvoiceNumber}", response_model=Invoice)
def update_invoice(InvoiceNumber: str, invoice: InvoiceUpdate, db: Session = Depends(get_db)):
    #print(f"Updating invoice with InvoiceNumber: {InvoiceNumber} 
    updated = crud.update_invoice(db, InvoiceNumber, invoice)
    if not updated:
        raise HTTPException(status_code=404, detail="invoice not found")
    return updated

@app.put("/invoices/{InvoiceNumber}/lineitems/{SuppliersID}", response_model=InvoiceLineItem)
def update_line_item(InvoiceNumber: str,
                     SuppliersID: str,
                     line_item: InvoiceLineItemUpdate,
                     db: Session = Depends(get_db)):
    updated = crud.update_line_item(db, InvoiceNumber, SuppliersID, line_item)
    if not updated:
        raise HTTPException(status_code=404, detail="line item not found")
    return updated

@app.put("/inventory/{ProductID}", response_model=Inventory)
def update_inventory_item(ProductID: str, inventory_entry: InventoryUpdate, db: Session = Depends(get_db)):
    updated = crud.update_inventory_entry(db, ProductID, inventory_entry)
    if not updated:
        raise HTTPException(status_code=404, detail="inventory entry not found")
    return updated


def cache_inventory(db: Session = Depends(get_db)):
    inventory = read_inventory(db)
    d = dict()
    product_ids = [0]
    for item in inventory:
        d[item.SuppliersID] = item
        product_ids.append(int(item.ProductID))
    return d, max(product_ids)


def handle_invoice(metadata: InvoiceCreate, 
                   lineitems: list[InvoiceLineItemCreate], 
                   confidence_intervals: list[tuple[float, float]], 
                   db: Session = Depends(get_db)):
    # -> JSON object{InvoiceCreate, list[InvoiceLineItemCreate], list[tuple[float, float]]}:
    create_new_invoice(metadata, db)
    for item in lineitems:
        create_new_line_item(metadata.InvoiceNumber, item, db)
    return ({"metadata": metadata,
             "lineitems": lineitems,
             "confidence_intervals": confidence_intervals})
    #App.jsx.uploadInvoice calls editInvoice
    #user save calls confirm_values

@app.post("/confirm_values")
def confirm_values(Invoice: InvoiceCreate, InvoiceLineItems: list[InvoiceLineItemUpdate]):
    result = uploader.update(Invoice, InvoiceLineItems) #either '200' or errors
    #if result != "200":
        #raise HTTPException(status_code=400, detail="Validation failed")
    return result
    #if success, app.jsx updates invoice table, changes table, line_items table; calls update_all_inventory


@app.post("/update_all_inventory")
def update_all_inventory(Invoice: InvoiceCreate,
                         InvoiceLineItems: list[InvoiceLineItemUpdate], 
                         db: Session = Depends(get_db)):
    inventory, current_max = cache_inventory(db)
    Supplier = Invoice.Supplier
    updated_items, new_items = inventory_updater.update(inventory, current_max, InvoiceLineItems, Supplier)
    # => list of InventoryCreate and one of InventoryUpdate
    for productID, item in updated_items:
        update_inventory_item(productID, item, db)
    for item in new_items:
        create_new_inventory_entry(item, db)
    return '200'

@app.post("/upload")
#https://medium.com/@ThinkingLoop/fastapi-file-uploads-clean-fast-and-foolproof-4ecf0f00404f
async def upload_file(file: UploadFile, db: Session = Depends(get_db)): 
    # -> handle_invoice(tuple[InvoiceCreate, list[InvoiceLineItemCreate], list[tuple[float, float]]], Session)
    name = file.filename
    target = os.path.join(DROPBOX,name) # pyright: ignore[reportCallIssue, reportArgumentType]
    if file.content_type not in {"application/pdf"}:
        raise HTTPException(415, "Unsupported file type")
    else:
        async with aiofiles.open(target, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                await out.write(chunk)
        #return {"stored_as": str(target)}
    metadata, lineitems, confidence_intervals = uploader.upload(target)
    return handle_invoice(metadata, lineitems, confidence_intervals, db)    

@app.get("/download")
def download_report(db: Session = Depends(get_db), test_toggle=False): 
    right_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    out_path = os.path.join(BASE_DIR,f"report_{right_now}.txt")
    text = [
        f"Report for {right_now}", "",
        "Invoice Summary", "",
        f"Invoice Number     Supplier    Due Date    Total"
    ]
    invoices = read_invoices(db)
    for invoice in invoices:
        text.append(f"{invoice.InvoiceNumber}     {invoice.Supplier}    {invoice.DueDate}    {invoice.TotalAmt}")

    text.extend(["", "Invoice Breakdown", ""])
    for invoice in invoices:
        invnum = invoice.InvoiceNumber
        text.extend([
            f"Invoice number:   {invnum}",
            f"Supplier:         {invoice.Supplier}",
            f"Order date:       {invoice.OrderDate}",
            f"Ship date:        {invoice.ShipDate or 'N/A'}",
            f"Due date:         {invoice.DueDate or 'N/A'}",
            f"Total:            {invoice.TotalAmt:.2f}",
            "",
            "Line items:",
        ])
        line_items = read_invoice_items(invnum,db)
        for item in line_items:
            text.extend([
                f"#{item.LineCount}  {item.SuppliersID}",
                f"    Description: {item.SuppliersDesc}",
                f"    Quantity:    {item.Quantity}",
                f"    Rate:        {item.Rate:.2f}",
                f"    Amount:      {item.Amount:.2f}",
                "",
            ])
            these_changes = read_invoice_changes(invnum,db)
            def sortKey(e):
                return e.Timestamp
            these_changes.sort(key=sortKey)
            for item in these_changes:
                text.append(f"At {item.Timestamp} the field {item.FieldChanged} was changed from {item.OldValue} to {item.NewValue}.")
            text.append("")
    text.append("End of report")
    if test_toggle:
        return (text)
    with open(out_path, 'w') as f:
        f.write("\n".join(text))
    return {"message": "Report downloaded successfully"}