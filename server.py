import json
import os
import pdfkit
import base64
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables (GitHub token)
load_dotenv()

app = Flask(__name__)

# Constants
INVOICE_DB = "invoice_data.json"
GITHUB_REPO = "https://api.github.com/repos/MARC0CND/LASRY/contents/invoices/"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Ensure invoice storage exists
if not os.path.exists("invoices"):
    os.makedirs("invoices")

# Function to read and update invoice number
def get_next_invoice_number():
    if not os.path.exists(INVOICE_DB):
        with open(INVOICE_DB, "w") as f:
            json.dump({"last_invoice": 0}, f)
    
    with open(INVOICE_DB, "r") as f:
        data = json.load(f)

    data["last_invoice"] += 1
    with open(INVOICE_DB, "w") as f:
        json.dump(data, f)

    return f"2025-{data['last_invoice']:03d}"

@app.route("/generate_invoice", methods=["POST"])
def generate_invoice():
    data = request.json
    invoice_number = get_next_invoice_number()

    # Generate invoice HTML
    invoice_html = f"""
    <html>
    <head><title>Facture {invoice_number}</title></head>
    <body>
    <h1>Facture: {invoice_number}</h1>
    <p>Nom de l'élève: {data['student_name']}</p>
    <p>Montant: ${data['payment_amount']}</p>
    <p>Raison: {data['payment_reason']}</p>
    </body></html>
    """

    pdf_filename = f"invoices/{invoice_number}.pdf"
    pdfkit.from_string(invoice_html, pdf_filename)

    # Upload to GitHub
    with open(pdf_filename, "rb") as f:
        pdf_content = f.read()
    
    encoded_content = base64.b64encode(pdf_content).decode()
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    upload_data = {
        "message": f"Add invoice {invoice_number}",
        "content": encoded_content
    }

    response = requests.put(f"{GITHUB_REPO}{invoice_number}.pdf", json=upload_data, headers=headers)
    
    if response.status_code == 201:
        return jsonify({"success": True, "invoice_number": invoice_number, "github_url": response.json()["content"]["html_url"]})
    else:
        return jsonify({"success": False, "error": response.text}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
