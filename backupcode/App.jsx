/*
 * Capstone Group 8 - Invoice Processing System
 * Main file for the React app frontend, including layout and uploader.
 * Author: Seth Z. Roth
 * @slittle95 contribution: Made the logic to make invoices editable. Added flow logic for invoice validation and report download.
 */

import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

function App() {
  const [invoices, setInvoices] = useState([]);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [selectedLineItems, setSelectedLineItems] = useState([]);
  const [status, setStatus] = useState("Connecting to backend...");
  const [editable, setEditable] = useState(false);
  const [confidence, setConfidence] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [originalInvoice, setOriginalInvoice] = useState(null);
  const [originalLineItems, setOriginalLineItems] = useState([]);
  const [refresh, setRefresh] = useState(0);


  useEffect(() => {
    fetch(`${API}/invoices/all`)
      .then((response) => {
        if (!response.ok) throw new Error("Could not load invoices");
        return response.json();
      })
      .then((data) => {
        setInvoices(data);
        setStatus(
          data.length ? "" : "Backend connected. No invoices found yet."
        );
      })
      .catch(() =>
        setStatus("Frontend is working. Backend is not connected yet.")
      );
  }, []);

  async function viewInvoice(invoice) {
    setEditable(false);
    setSelectedInvoice(invoice);
    setSelectedLineItems([]);
    setOriginalLineItems([]);
    try {
      const response = await fetch(
        `${API}/invoices/${invoice.InvoiceNumber}/lineitems`
      );

      if (!response.ok) throw new Error();
      setSelectedLineItems(await response.json());
    } catch {
      setStatus("Invoice loaded, but line items could not be retrieved.");
    }
  }

  async function editInvoice(invoice) {
    console.log("SelectedInvoice: ", JSON.stringify(invoice));
    console.log("selectedLineItems: " + JSON.stringify(selectedLineItems));
    console.log(selectedLineItems);
    setOriginalInvoice({ ...invoice});
    setOriginalLineItems([...selectedLineItems]);
    setEditable(true);  
    console.log(selectedLineItems);
  }


  async function collectUpdate(field, value, isLineitem) {
    console.log("collecUpdate called");
    if (!isLineitem) {
      setSelectedInvoice((prevState) => ({
      ...(prevState || {}),
      [field]: value
    }));
    } else {
      console.log(selectedLineItems);
      console.log(field);
        const line_count = field.split("-")[0] -1;
        const actual_field = field.split("-")[1];
        var temp = selectedLineItems;
        console.log("temp" + temp);
        temp[line_count] = { ...temp[line_count], [actual_field]: value };
        console.log("temp" + temp);
        setSelectedLineItems(temp);
        setRefresh(refresh + 1);
        // Using prevState here appears to convert the array to an object
        //which causes Map to stop working.      
   /*      setSelectedLineItems((prevState) => ({          
        ...(prevState[line_count] || {}),
        [actual_field]: value
      })); */
    }
  //console.log("collectUpdate done",selectedLineItems);
  }


  async function uploadInvoice(e) {
    e.preventDefault();

    if (!selectedFile) {
      setUploadMessage("Please select a PDF first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setUploading(true);
    setUploadMessage("Processing invoice...");

    try {
      const response = await fetch(`${API}/upload`, { //main.upload_file
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Upload failed");
      }

      const result = await response.json(); //should be metadata, lineitems, confidence_intervals

      setUploadMessage("Invoice processed successfully.");

      window.location.reload(false);
      setSelectedLineItems(result.lineitems);
      setConfidenceIntervals(true);
      editInvoice(result.metadata);

    } catch (error) {
      console.error(error);
      setUploadMessage("Unable to process invoice.");
    } finally {
      setUploading(false);
    }
  }



  async function update_form(e) {
    e.preventDefault();
    if (!originalInvoice || !selectedInvoice) return;

   //validation
    fetch(`${API}/confirm_values`, 
    {method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: {
        Invoice: selectedInvoice,
        LineItems: selectedLineItems
      }
    }).then(res => res.json());

    const invoiceNum = originalInvoice.InvoiceNumber;
    
    //log the changes to the main invoice
    Object.entries(selectedInvoice).forEach(([key, value]) => {
      if (key === "InvoiceNumber") return;  
      console.log(`Key: ${key}, Value: ${value}, Original: ${originalInvoice[key]}`);
      if (JSON.stringify(value) !== JSON.stringify(originalInvoice[key])) {
        const change = {
          'InvoiceID': invoiceNum,
          'FieldChanged': key,
          'OldValue': originalInvoice[key],
          'NewValue': value,
        };
        console.log(change);

        fetch(`${API}/invoices/${invoiceNum}/changes`,
        {method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(change)
        });
      }
      else {console.log(`No change in ${key}`);}
    });

    //update invoice in invoice table
    fetch(`${API}/invoices/${invoiceNum}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(selectedInvoice)
    })
    .then(res => res.json())
    .catch(() => setStatus("Invoice update failed."));

    //log the changes to the line items
    selectedLineItems.forEach((item) => { 
      line_count = item.LineCount;
      Object.entries(item).forEach(([key, value]) => {
      console.log(`Key: ${key}, Value: ${value}, Original: ${originalLineItems[line_count][key]}`);
      if (JSON.stringify(value) !== JSON.stringify(originalLineItems[line_count][key])) {
        const change = {
          'InvoiceID': invoiceNum,
          'FieldChanged': line_count+'-'+key,
          'OldValue': originalLineItems[line_count][key],
          'NewValue': value,
        };
        console.log(change);

        fetch(`${API}/invoices/${invoiceNum}/changes`,
        {method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(change)
        });
      }
      });
    
     //update line items in lineitem table
    fetch(`${API}/invoices/${invoiceNum}/lineitems/${item.SuppliersID}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(item)
    })
    .then(res => res.json())
    .catch(() => setStatus("Invoice update failed."));
    });

    //pass control back to main.py to make inventory changes indicated by invoice
    fetch(`${API}/update_all_inventory`, 
    {method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: {
        Invoice: selectedInvoice,
        LineItems: selectedLineItems
      }
    }).then(res => res.json()) //ideally if res.json != '200' raise exception
    .then(() => {
        window.location.reload(false);
    })
    .catch(() => setStatus("Inventory refresh failed."));
  setEditable(false);
  }


async function uploadInvoice(e) {
  e.preventDefault();

  if (!selectedFile) {
      setUploadMessage("Please select a PDF first.");  
     return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setUploading(true);
    setUploadMessage("Processing invoice...");

    try {
      const response = await fetch(`${API}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Upload failed");
      }

      await response.json();
      const res = response.json();

    setUploadMessage("Invoice processed successfully.");
    setSelectedInvoice(res.metadata)
    setSelectedLineItems(res.lineitems)
    setEditable(true);
    setConfidence(true);
    setOriginalInvoice(res.metadata);
      window.location.reload(false);
    } catch (error) {
      console.error(error);
      setUploadMessage("Unable to process invoice.");
    } finally {
      setUploading(false);
    }
}

function downloadReport() {
  setRefresh(refresh + 1);
  fetch(`${API}/download`)
    .then((response) => {
      if (!response.ok) throw new Error("Could not download report");
        return response.json();
      });
  }

  return (   
    <main className="page">
      <header>
        <p className="eyebrow">Capstone Group 8</p>
        <h1>Invoice Processing System</h1>
        <p className="subtitle">
          Human-in-the-loop review of workplace invoice data.
        </p>
      </header>

      {status && <div className="status">{status}</div>}
      
      <section className="panel">
         <h2>Upload Invoice</h2>

        <form onSubmit={uploadInvoice}>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => {
              setSelectedFile(e.target.files[0]);
              setUploadMessage("");
            }}
          />

          <button type="submit" disabled={uploading}>
            {uploading ? "Processing..." : "Upload PDF"}
          </button>
        </form>

        {uploadMessage && <p>{uploadMessage}</p>}
      </section>

      <section className="panel">
        <h2>Invoices</h2>
        <button onClick={() => downloadReport()}>
          Download Report
        </button>

        {invoices.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Supplier</th>
                  <th>Order Date</th>
                  <th>Total</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.InvoiceNumber}>
                    <td>{invoice.InvoiceNumber}</td>
                    <td>{invoice.Supplier}</td>
                    <td>{invoice.OrderDate}</td>
                    <td>${Number(invoice.TotalAmt).toFixed(2)}</td>
                    <td>
                      <button onClick={() => viewInvoice(invoice)}>
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedInvoice && !editable && (
        <section className="panel">
          <h2>Invoice {selectedInvoice.InvoiceNumber}</h2>

          <p>
            <button onClick={() => editInvoice(selectedInvoice)}>
              Edit
            </button>
          </p>

          <div className="summary-grid">
            <span>
              <strong>Supplier:</strong> {selectedInvoice.Supplier}
            </span>

            <span>
              <strong>Order Date:</strong> {selectedInvoice.OrderDate}
            </span>

            <span>
              <strong>Sales Order:</strong> {selectedInvoice.SalesOrderNo}
            </span>

            <span>
              <strong>Due:</strong> {selectedInvoice.DueDate}
            </span>

            <span>
              <strong>Shipped On:</strong> {selectedInvoice.ShipDate}
            </span>
          </div>

          <div className="summary-grid">
            <span>
              <strong>Shipping:</strong> $
              {Number(selectedInvoice.ShippingHandling).toFixed(2)}
            </span>

            <span>
              <strong>Total:</strong> $
              {Number(selectedInvoice.TotalAmt).toFixed(2)}
            </span>
          </div>

          <h3>Line Items</h3>
          {selectedLineItems.length === 0 ? (
            <p>No line items available.</p>
          ) : (
            selectedLineItems.map((item) => (
              <div className="line-item" key={`${item.InvoiceNumber}-${item.LineCount}`}>
                <div>
                  <strong>{item.SuppliersDesc}</strong>
                  <small>{item.SuppliersID}</small>
                </div>

                <span>
                  {item.Quantity} × ${Number(item.Rate).toFixed(2)} = $
                  {Number(item.Amount).toFixed(2)}
                </span>
              </div>
            ))
          )}
        </section>
      )}

      {selectedInvoice && editable && (
        <section className="panel">
          <form name='form1' onSubmit={update_form}>
          <div className="summary-grid">
            {/*<span>
              <label htmlFor="invoice_num">Invoice Number: </label> 
              <input type="text" className="form-control" id="invoice_num" name = "invoice_num" defaultValue={selectedInvoice.InvoiceNumber} required></input>
            </span>*/}
            <span>
              <label htmlFor="supplier">Supplier:</label> 
              <input type="text" className="form_control" id="supplier" name="supplier" 
              value={selectedInvoice.Supplier || ""} required
              onChange={(e) => collectUpdate("Supplier",e.target.value, false)}/>
            </span>
            <span>
              <label htmlFor="order_date">Order Date: </label>
              <input type="date" className="form-control" id="order_date" name = "order_date" 
              value={selectedInvoice.OrderDate || ""} required
              onChange={(e) => collectUpdate("OrderDate",e.target.value, false)}/>
            </span>
            <span>
              <label htmlFor="sales_order">Sales Order: </label>
              <input type="text" className="form-control" id="sales_order" name = "sales_order" 
              value={selectedInvoice.SalesOrderNo || ""} required
              onChange={(e) => collectUpdate("SalesOrderNo",e.target.value, false)}/>
            </span>
            <span>
              <label htmlFor="due_date">Due: </label>
              <input type="date" className="form-control" id="due_date" name = "due_date" 
              value={selectedInvoice.DueDate || ""} required
              onChange={(e) => collectUpdate("DueDate",e.target.value, false)}/>
            </span>
            <span>
              <label htmlFor="ship_date">Shipped On: </label>
              <input type="date" className="form-control" id="ship_date" name = "ship_date" 
              value={selectedInvoice.ShipDate || ""} required
              onChange={(e) => collectUpdate("ShipDate",e.target.value, false)}/>
            </span>
          </div>
          <div className="summary-grid">
            <span>
              <label htmlFor="shipping">Shipping and Handling:</label>
              <input type="number" className="form_control" id="shipping" name="shipping" step = "0.01" min="0"
              value={selectedInvoice.ShippingHandling || ""} required
                onChange={(e) => collectUpdate("ShippingHandling",e.target.value, false)}/>   
            </span>
            <span>
              <label htmlFor="total">Total:</label>
              <input type="number" className="form_control" id="total" name="total" step="0.01" min="0"
              value={selectedInvoice.TotalAmt || ""} required
              onChange={(e) => collectUpdate("TotalAmt",e.target.value, false)}/>    
            </span>
          </div>
          <input type="submit" />
          </form>

          <h3>Line Items</h3>
          {selectedLineItems.length === 0 ? (
            <p>No line items available.</p>
          ) : (

            selectedLineItems.map((item) => (
              <div className="line-item" key={`${item.InvoiceNumber}-${item.LineCount}`}>
                <div>
                  <input type="text" className="form-control" 
                  value={item.SuppliersDesc || ""} required
                  onChange={(e) => collectUpdate(item.LineCount + "-SuppliersDesc",e.target.value, true)}/>
                  <input type="text" className="form-control" 
                  value={item.SuppliersID}
                  onChange={(e) => collectUpdate(item.LineCount + "-SuppliersID",e.target.value, true)}/>
                </div>

                <span>
                  <input type="number" className="form-control"
                  value={item.Quantity} required
                  onChange={(e) => collectUpdate(item.LineCount + "-Quantity",e.target.value, true)}/>
                  × 
                  <input type="number" className="form-control"
                  value={Number(item.Rate).toFixed(2)} required
                  onChange={(e) => collectUpdate(item.LineCount + "-Rate",e.target.value, true)}/>
                  = $
                  <input type="number" className="form-control"
                  value={Number(item.Amount).toFixed(2)} required
                  onChange={(e) => collectUpdate(item.LineCount + "-Amount",e.target.value, true)}/>
                </span>
              </div>
            ))
          )}
        </section>
      )}
    </main>
    
  );
}

export default App;