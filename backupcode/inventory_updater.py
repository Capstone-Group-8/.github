'''
author: Sally Little
Date Created: September 16

'''
import validation

from inv import CompleteInvoice
from datetime import date
from dateutil.parser import parse
from schemas import (
    InventoryCreate,
    InventoryUpdate
)

def update(inventory, current_max, new_lineitems, supplier):# -> tuple[tuple[str, list[InventoryUpdate], list[InventoryCreate]]:
    new_items = []
    updated_items = []
    for item in new_lineitems:
        if item.SuppliersID in inventory:
            #update existing inventory entry with new quantity and LastPrice
            inv_entry = inventory[item.SuppliersID]
            new_qty = inv_entry.QtyOnHand + item.Quantity
            print(f"Inventory entry for {item.SuppliersID} already exists under {inv_entry.ProductID}.")
            updated_items.append((
                inv_entry.ProductID,
                InventoryUpdate(
                    SuppliersID=inv_entry.SuppliersID,
                    Description=inv_entry.Description,
                    ProductType=inv_entry.ProductType,
                    QtyOnHand=new_qty,
                    LastPrice=item.Rate,
                    TotalQtyDesired=inv_entry.TotalQtyDesired,
                    Supplier=supplier
                )
            ))
        else:
            #create new inventory entry
            current_max += 1
            print(f"Current max is {current_max - 1} so new product {item.SuppliersID} created with ID {current_max}")
            new_items.append(
                InventoryCreate(
                    ProductID=str(current_max), 
                    SuppliersID=item.SuppliersID,
                    Description=item.SuppliersDesc,
                    ProductType="Unknown", #"switch" statement tbd
                    QtyOnHand=item.Quantity,
                    LastPrice=item.Rate,                        
                    TotalQtyDesired=0, #default value
                    Supplier=supplier
                )
            )
    return updated_items, new_items