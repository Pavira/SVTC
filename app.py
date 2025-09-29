import base64
import logging
import subprocess
import sys
import threading
import time
import traceback
from flask import (
    Flask,
    render_template,
    request,
    session,
    jsonify,
    send_file,
    Blueprint,
    current_app,
    g,
    url_for,
    redirect,
)
from datetime import datetime, timedelta
from time import time
import firebase_admin
from firebase_admin import credentials, auth, storage
from firebase_admin import firestore, db
import pyrebase
import json
import os

# import pandas as pd
import decimal
from flask_wtf.csrf import CSRFProtect
from flask import Flask, session
from flask_session import Session
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin

# from io import BytesIO
# import re
import webview
from os.path import join, dirname, realpath
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField
from items import items_bp
from consignee import consigee_bp
import urllib.parse
import matplotlib
import tempfile

matplotlib.use("Agg")  # Ensure no GUI is used
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from flask import Flask, request, render_template, make_response
from io import BytesIO
from num2words import num2words
import pytz


# GlobalVariable
flgLoggedIn = False
strUserId = ""
strUser = ""
strUserRole = ""
lstMstrICD = []
lstSearchTermDwgNum = []
lstSearchTermDwgName = []
lstSearchTermCusName = []
lstServiceType = ["With Material", "Only Labour"]
# (/\:?*"<>|)
lstIgnoreFileNameChar = ["/", "\\", ":", "?", "*", "<", ">", "|"]
""" strDeskFolderPath = os.path.expanduser("~\Desktop")
strDeskFolderPath = strDeskFolderPath.replace("\\","/")
strBillFolderPath = strDeskFolderPath+"/"+"AUV Engineering Management/Bills"
print(strDeskFolderPath)
flgBillFolderExists = os.path.exists(strBillFolderPath)
if flgBillFolderExists == False:
    os.makedirs(strBillFolderPath)
strDischSumFolderPath = strDeskFolderPath+"/"+"AUV Engineering Management/Bills"
flgDischSumFolderExists = os.path.exists(strDischSumFolderPath)
if flgDischSumFolderExists == False:
    os.makedirs(strDischSumFolderPath) """

strRootPath = dirname(realpath(__file__))
# Initialize App
if getattr(sys, "frozen", False):
    # root_folder = os.path.join(sys._MEIPASS,)
    root_folder = join(dirname(realpath(__file__)))
    app = Flask(__name__, root_path=root_folder)
    print("frozen")
else:
    # app = Flask(__name__)
    root_folder = join(dirname(realpath(__file__)))
    app = Flask(__name__, root_path=root_folder)
secretKey = "aodhleirbnkljnvlaekjhherasdnvkjvn"
app.secret_key = secretKey
# app.secret_key = "kjalskdjghakjghapeiuruervnkfdnvxcbzlgerhiuah"

# Security
app.config["SESSION_TYPE"] = "filesystem"
# app.config['SESSION_PERMANENT'] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_KEY_PREFIX"] = "myapp_"
app.config["WTF_CSRF_ENABLED"] = True

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

app.config["UPLOAD_EXTENSIONS"] = [".jpg", ".png", ".gif"]
app.config["UPLOAD_PATH"] = strRootPath

jinja_options = {
    "extensions": ["jinja2.ext.autoescape", "jinja2.ext.with_"]  # Turn auto escaping on
}

# Autoescaping
app.jinja_env.autoescape = True

# LoginManager
""" login_manager = LoginManager()
login_manager.init_app(app)
 """
# CSRF
csrf = CSRFProtect()
csrf.init_app(app)

# Initialize the Flask-Session extension
Session(app)


def delete_temp_files():
    temp_dir = r"C:\Windows\Temp\AUV_temp"

    # Check if the directory exists
    if os.path.exists(temp_dir):
        # Iterate over all files in the directory and delete them
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
    else:
        print(f"Directory does not exist: {temp_dir}")


# # Confirmation callback for the window close event
def on_close():
    print("Window is closing...")
    delete_temp_files()
    return True  # Allow the window to close


def run_flask():
    app.run(debug=False, use_reloader=False)  # disable reloader for thread safety


# def delete_temp_files():
#     # Get the system's temporary directory
#     system_temp_dir = tempfile.gettempdir()
#     temp_dir = os.path.join(system_temp_dir, "AUV_temp")

#     # Ensure the AUV_temp directory exists
#     if not os.path.exists(temp_dir):
#         os.makedirs(temp_dir)
#         print(f"Created directory: {temp_dir}")
#     else:
#         # Iterate over all files in the directory and delete them
#         for file in os.listdir(temp_dir):
#             file_path = os.path.join(temp_dir, file)
#             try:
#                 os.remove(file_path)
#                 print(f"Deleted file: {file_path}")
#             except Exception as e:
#                 print(f"Error deleting file {file_path}: {e}")


# #Webwiew Window
# window = webview.create_window(
#     "AUV Engineering ERP", app, confirm_close=True, min_size=(1000, 800)
# )


strTempFilePath = join(strRootPath, ("TempFiles/"))
strStaticPath = join(strRootPath, ("Static/"))
# Connect to firebase
# cred = credentials.Certificate('./firebase/fbAdminConfig.json')
cred = credentials.Certificate(join(strRootPath, ("fbAdminConfig.json")))
firebase = firebase_admin.initialize_app(
    cred, {"storageBucket": "ferrous-terrain-422918-e3.appspot.com"}
)
# pb = pyrebase.initialize_app(json.load(open('./firebase/fbconfig.json')))
pb = pyrebase.initialize_app(json.load(open(join(strRootPath, ("fbconfig.json")))))
# datetime.now().strftime("%H:%M:%S.%f")
print(strTempFilePath)

# -----------//------------//--------------------#

# Register the blueprint for supplier routes
db = firestore.client()

# Pass db to supplier blueprint for Firestore access
app.config["FIRESTORE_DB"] = db
# app.register_blueprint(supplier_bp)
# app.register_blueprint(po_bp)
# app.register_blueprint(admin_bp)
app.register_blueprint(items_bp)
app.register_blueprint(consigee_bp)


@app.before_request
def set_user():
    g.strUser = strUser
    print("g.strUser-------", g.strUser)
    g.strUserRole = strUserRole


def capitalize_words(text):
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    return " ".join(word.capitalize() for word in text.split())


def convert_total_bill_to_words(total_bill):
    """
    Converts a numeric total bill into words with 'rupees only' appended.

    Args:
        total_bill (int or float): The total bill amount to convert.

    Returns:
        str: Total bill amount in words.
    """
    try:
        # Convert the numeric value to words
        total_in_words = num2words(total_bill).replace(",", "")

        # Append 'rupees only' to the result
        total_in_words_with_suffix = f"{total_in_words} rupees only"
        return total_in_words_with_suffix
    except Exception as e:
        return f"Error converting total bill to words: {e}"


def generate_invoice_id():
    # Calculate the current financial year
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # Financial year from April to March
    if current_month >= 4:  # From April to December
        start_year = current_year
        end_year = current_year + 1
    else:  # From January to March
        start_year = current_year - 1
        end_year = current_year

    financial_year = f"{str(start_year)[-2:]}-{str(end_year)[-2:]}"  # Format: "24-25"
    month_str = (
        f"{current_month:02d}"  # Format the month as two digits (e.g., "08" for August)
    )

    # Access the Firestore database
    db = current_app.config["FIRESTORE_DB"]
    count_collection = db.collection("Count")

    # Fetch the document for the current financial year
    doc_ref = count_collection.document("count")
    doc = doc_ref.get()

    # Initialize the last invoice ID and stored financial year
    last_invoice_id = 0
    stored_financial_year = None

    if doc.exists:
        doc_data = doc.to_dict()
        stored_financial_year = doc_data.get("financial_year", None)
        last_invoice_id = doc_data.get("invoice_count", 0)

    # If the financial year has changed, reset `present_invoice_id` to 1 and update the financial year
    if stored_financial_year != financial_year:
        last_invoice_id = 0  # Reset the invoice ID
        doc_ref.update(
            {
                "financial_year": financial_year,
                "invoice_count": 0,  # Reset the invoice ID in the database
            }
        )

    # Increment the last invoice ID by 1 to generate the new invoice ID
    new_invoice_number = last_invoice_id + 1

    # Generate the new invoice ID in the desired format
    invoice_id = (
        f"{financial_year}{month_str}{new_invoice_number:01d}"  # Format: "24-250801"
    )

    # Store the new invoice ID in the Firestore collection
    doc_ref.update({"invoice_count": new_invoice_number})

    print("Generated Invoice ID:", invoice_id)
    return invoice_id


@app.route("/generate_invoice", methods=["POST"])
def generateInvoice():

    invoice_no = generate_invoice_id()

    timestamp = datetime.now()
    timestamp = timestamp.astimezone(pytz.timezone("Asia/Kolkata"))
    # Store server timestamp in invoice_date
    invoice_date = timestamp
    current_time = datetime.now().strftime("%Y-%m-%d")
    print("invoice_date//////", invoice_date)
    print("current_time//////", current_time)

    consignee_name = capitalize_words(request.form["consignee_name"]).strip()
    # consignee_name = consignee_name
    gst_no = request.form["gst_no"].upper()
    address = capitalize_words(request.form["address"])
    state = request.form["state"].upper()
    code = request.form["code"]
    purchase_order_no = request.form["purchase_order_no"].upper()
    purchase_order_date = request.form["purchase_order_date"]
    half_gst = request.form["half_gst"]

    mode = request.form["mode"].upper()
    vehicle_no = request.form["vehicle_no"].upper()
    supply_place = request.form["supply_place"].upper()
    supply_date = request.form["supply_date"]
    supply_time = request.form["supply_time"]
    bill_no = request.form["bill_no"].upper()

    totalGST = request.form["totalGST"]
    totalUnitPrice = request.form["totalUnitPrice"]
    totalBill = request.form["totalBill"]

    logged_in_user = session["user"]
    # status = None

    # Construct the data dictionary
    item_data = {
        "invoice_id": invoice_no,
        "consignee_name": consignee_name.lower(),
        "gst_no": gst_no.lower(),
        "address": address.lower(),
        "state": state.lower(),
        "code": code,
        "purchase_order_no": purchase_order_no.lower(),
        "purchase_order_date": purchase_order_date,
        "mode": mode.lower(),
        "vehicle_no": vehicle_no.lower(),
        "supply_place": supply_place.lower(),
        "supply_date": supply_date,
        "supply_time": supply_time,
        "bill_no": bill_no.lower(),
        "items_details": [],  # To be filled below
        "totalGST": totalGST,
        "totalUnitPrice": totalUnitPrice,
        "totalBill": totalBill,
        "username": logged_in_user,
        "created_date": invoice_date,
        "status": None,
    }

    items_details = []

    item_names = request.form.getlist("item_name")
    HSNCodes = request.form.getlist("HSNCode")
    qtys = request.form.getlist("qty")
    uoms = request.form.getlist("uom")
    rates = request.form.getlist("rate")
    gsts = request.form.getlist("gst")
    totalPrices = request.form.getlist("totalPrice")

    print(
        "Received item names:",
        item_names,
        HSNCodes,
        qtys,
        uoms,
        rates,
        gsts,
        totalPrices,
    )

    for item_name, HSNCode, qty, uom, rate, gst, totalPrice in zip(
        item_names, HSNCodes, qtys, uoms, rates, gsts, totalPrices
    ):
        item_name = capitalize_words(item_name)  # Capitalize item name
        items_details.append(
            {
                "item_name": item_name,
                "HSNCode": HSNCode,
                "qty": qty,
                "uom": uom.lower(),
                "rate": rate,
                "gst": gst,
                "totalPrice": totalPrice,
            }
        )

    # Assign the items_details list directly to the dictionary
    item_data["items_details"] = items_details

    total_bill_in_words = convert_total_bill_to_words(totalBill)

    # Increment the invoice_count
    # new_invoice_count = invoice_no + 1

    db.collection("invoiceDetails").document(str(invoice_no)).set(item_data)

    # Update the document with the new invoice_count
    # count_doc_ref.update({'invoice_count': new_invoice_count})

    print("Item Details", items_details)

    # totalGST_bytes = totalGST.encode('utf-8')
    # totalGST_decoded = totalGST_bytes.decode('utf-8')
    # totalGST_value = float(totalGST_decoded)
    # half_gst = totalGST_value / 2

    # Create the PDF in memory
    buffer = BytesIO()

    create_pdf(
        buffer,
        invoice_no,
        current_time,
        consignee_name,
        gst_no,
        address,
        state,
        code,
        mode,
        vehicle_no,
        supply_place,
        supply_date,
        supply_time,
        bill_no,
        purchase_order_no,
        purchase_order_date,
        totalGST,
        half_gst,
        totalUnitPrice,
        totalBill,
        total_bill_in_words,
        items_details,
    )

    buffer.seek(0)

    # Return the PDF as a response
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    # response.headers['Content-Disposition'] = 'inline; filename="invoice.pdf"'
    response.headers["Content-Disposition"] = (
        f"inline; filename={invoice_no}-{current_time}.pdf"
    )
    return response


# 	# Save the PDF file temporarily on the server
# 	pdf_filename = f"invoice_{invoice_no}.pdf"
# 	with open(pdf_filename, 'wb') as f:
# 		f.write(buffer.getvalue())

#     # Redirect to the PDF viewing URL
# 	return redirect(url_for('view_invoice', invoice_no=invoice_no))

# @app.route('/view_invoice/<invoice_no>')
# def view_invoice(invoice_no):
#     pdf_filename = f"invoice_{invoice_no}.pdf"
#     return send_file(pdf_filename, mimetype='application/pdf')


# Define constants for positioning and dimensions
def create_pdf(
    buffer,
    invoice_no,
    current_time,
    consignee_name,
    gst_no,
    address,
    state,
    code,
    mode,
    vehicle_no,
    supply_place,
    supply_date,
    supply_time,
    bill_no,
    purchase_order_no,
    purchase_order_date,
    totalGST,
    half_gst,
    totalUnitPrice,
    totalBill,
    total_bill_in_words,
    items_details,
):

    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("Invoice")
    # width, height = A4

    # Define margins
    left_margin = 50  # Points (1 inch = 72 points)
    top_margin = 50

    # Shift content inward
    pdf.translate(left_margin, top_margin)

    # Get page dimensions
    width, height = A4

    # Draw content
    pdf.drawString(0, height - top_margin - 50, "")
    pdf.rect(0, 0, width - 2 * left_margin, height - 2 * top_margin)  # Example border

    # Add a border around the entire page
    # pdf.setLineWidth(1)
    # pdf.rect(0, 0, width, height)

    # Define 50% of the page height
    upper_half_height = height / 2

    # Define the sections in the upper half
    upper_10_percent = upper_half_height * 0.2
    middle_30_percent = upper_half_height * 0.4

    # Section 1: Upper 10% (split vertically 70:30)
    section1_y_start = height - 100
    section1_y_end = height - upper_10_percent

    section1_left_width = width * 0.7
    section1_right_width = width * 0.3

    # Section 1: Left (70%)
    section_width = width * 0.7  # 70% of the page width
    offset = 140  # Shift the section slightly to the left
    section_x_start = (
        (width - section_width) / 2
    ) - offset  # Adjust the starting position to the left

    pdf.setFont("Helvetica-Bold", 14)  # Bold and larger font for the title
    text_title = "Sree Venkateswara Textiles & Chemicals"
    text_width = pdf.stringWidth(text_title, "Helvetica-Bold", 14)
    pdf.drawString(
        section_x_start + (section_width - text_width) / 2,
        section1_y_start - 20,
        text_title,
    )  # Centered title in 70% section

    # Reduced line spacing
    line_spacing = 12
    y_position = section1_y_start - 40

    # Helper function to center text within the adjusted section
    def draw_centered_in_section(
        pdf, text, font, font_size, y_position, section_x_start, section_width
    ):
        pdf.setFont(font, font_size)
        text_width = pdf.stringWidth(text, font, font_size)
        x_position = section_x_start + (section_width - text_width) / 2
        pdf.drawString(x_position, y_position, text)

    # Centered address
    draw_centered_in_section(
        pdf,
        "95-A, Avinashi Road, Hope College, Peelamedu, Coimbatore-641004.",
        "Helvetica",
        8,
        y_position,
        section_x_start,
        section_width,
    )

    y_position -= line_spacing

    # Centered Email and Phone
    email_text = "Email: "
    email_bold = "manoharan123_2002@yahoo.com"
    phone_text = "Phone: "
    phone_bold = "0422 2593392"

    # Email
    draw_centered_in_section(
        pdf,
        f"{email_text}{email_bold}",
        "Helvetica",
        8,
        y_position,
        section_x_start,
        section_width,
    )

    y_position -= line_spacing

    # Phone
    draw_centered_in_section(
        pdf,
        f"{phone_text}{phone_bold}",
        "Helvetica",
        8,
        y_position,
        section_x_start,
        section_width,
    )

    y_position -= line_spacing

    # GSTIN
    gst_text = "GST IN: "
    gst_bold = "33ADPPV9152L1ZQ"
    draw_centered_in_section(
        pdf,
        f"{gst_text}{gst_bold}",
        "Helvetica",
        8,
        y_position,
        section_x_start,
        section_width,
    )

    # Draw vertical line between left and right sections
    pdf.setLineWidth(1)
    pdf.line(
        section1_left_width - 110,
        section1_y_start - 85,
        section1_left_width - 110,
        section1_y_end - 15,
    )  # done

    # Section 1: Right (30%)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(section1_left_width - 100, section1_y_start - 20, "Invoice")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        section1_left_width - 100, section1_y_start - 40, f"No     : {invoice_no}"
    )
    pdf.drawString(
        section1_left_width - 100, section1_y_start - 60, f"Date  : {current_time}"
    )
    pdf.drawString(section1_left_width - 100, section1_y_start - 80, "Type  : Original")

    # Draw horizontal line after the right section
    pdf.line(0, section1_y_end - 100, width - 100, section1_y_end - 100)  # done

    # Section 2: Middle 30% (split vertically 50:50)
    section2_y_start = section1_y_end - 100
    section2_y_end = section1_y_end - middle_30_percent
    section2_half_width = width / 2

    # Section 2: Left (50%)
    # Set bold and larger font for "Details of Consignee"
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(20, section2_y_start - 20, "Details of Consignee")

    # Set bold font for "Name :"
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20, section2_y_start - 40, "Name ")

    # Set regular font for name and compose it in one line
    pdf.setFont("Helvetica", 10)

    # # Split the consignee_name into words
    consignee_words = consignee_name.split()
    if len(consignee_words) > 2:
        first_line = " ".join(consignee_words[:2])
        second_line = " ".join(consignee_words[2:])
    else:
        first_line = consignee_name
        second_line = ""

    pdf.drawString(100, section2_y_start - 40, f": {first_line}")
    pdf.drawString(100, section2_y_start - 50, second_line)

    # Set bold font for "Address :"
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20, section2_y_start - 70, "Address ")

    pdf.setFont("Helvetica", 10)

    # # Split the address into words
    address_words = address.split()
    if len(address_words) > 7:
        first_line = " ".join(address_words[:3])
        second_line = " ".join(address_words[3:6])
        third_line = " ".join(address_words[6:])
    elif len(address_words) > 3:
        first_line = " ".join(address_words[:3])
        second_line = " ".join(address_words[3:])
        third_line = ""
    else:
        first_line = address
        second_line = ""
        third_line = ""

    pdf.drawString(100, section2_y_start - 70, f": {first_line}")
    pdf.drawString(100, section2_y_start - 90, second_line)
    pdf.drawString(100, section2_y_start - 100, third_line)

    # # Set regular font for address lines
    # pdf.setFont("Helvetica", 10)
    # pdf.drawString(100, section2_y_start - 80, "E11, H12, H13,")
    # pdf.drawString(100, section2_y_start - 100, "SIPCOT INDUSTRIAL GROWTH CENTER,")
    # pdf.drawString(100, section2_y_start - 120, "PERUNDURAI, PIN - 638052.")

    # Set bold font for "State&Code :"
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20, section2_y_start - 110, "State&Code ")

    # Set regular font for state and code
    pdf.setFont("Helvetica", 10)
    pdf.drawString(100, section2_y_start - 110, f": {state}, {code}")

    # Set bold font for "GSTIN Number:"
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20, section2_y_start - 130, "GSTIN Number ")

    # Set regular font for GSTIN value
    pdf.setFont("Helvetica", 10)
    pdf.drawString(100, section2_y_start - 130, f": {gst_no}")

    # Draw vertical line between left and right sections
    pdf.setLineWidth(1)
    pdf.line(
        section1_left_width - 150,
        section1_y_start - 232,
        section1_left_width - 150,
        section1_y_end - 100,
    )  # done

    # Section 2: Right (50%)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(section2_half_width - 20, section2_y_start - 20, "Transport details")
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(section2_half_width - 20, section2_y_start - 40, "Mode")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(section2_half_width + 100, section2_y_start - 40, ": " + mode)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(section2_half_width - 20, section2_y_start - 60, "Vehicle No.")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(section2_half_width + 100, section2_y_start - 60, ": " + vehicle_no)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(section2_half_width - 20, section2_y_start - 80, "Place of Supply")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        section2_half_width + 100, section2_y_start - 80, ": " + supply_place
    )
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(section2_half_width - 20, section2_y_start - 100, "Date of Supply")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        section2_half_width + 100, section2_y_start - 100, ": " + supply_date
    )
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(section2_half_width - 20, section2_y_start - 120, "Time of Supply")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        section2_half_width + 100, section2_y_start - 120, ": " + supply_time
    )
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(section2_half_width - 20, section2_y_start - 140, "E.way Bill No")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(section2_half_width + 100, section2_y_start - 140, ": " + bill_no)

    # Draw a vertical line between the two sections (Section 2: Left and Section 2: Right)
    line_x = (
        section2_half_width + 10
    )  # X-coordinate of the line (boundary between left and right sections)
    # pdf.setLineWidth(1)
    # pdf.line(line_x-100, section2_y_start, line_x, section2_y_end)  # Start at the top, end at the bottom of Section 2

    # Draw horizontal line after the second section
    pdf.line(0, section2_y_end - 80, width - 100, section2_y_end - 80)

    # Section 3: Lower 10% (Table header)
    table_y_start = section2_y_end - 80
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(5, table_y_start - 20, "SI.no")
    pdf.drawString(40, table_y_start - 20, "Description of the goods")
    pdf.drawString(165, table_y_start - 20, "HSN Code")
    pdf.drawString(225, table_y_start - 20, "Qty")
    pdf.drawString(255, table_y_start - 20, "UOM")
    pdf.drawString(295, table_y_start - 20, "RATE")
    pdf.drawString(340, table_y_start - 20, "GST%")
    pdf.drawString(385, table_y_start - 20, "Total Price")

    # Draw horizontal line after the header row
    header_line_y = table_y_start - 25
    pdf.line(0, header_line_y, width - 100, header_line_y)

    row_height = 14  # Height of each row
    pdf.setFont("Helvetica", 8)

    # Calculate the total height of the table based on the number of rows
    # table_height = 35 + (len(items_details) * row_height)
    table_height = table_y_start - 35 - ((len(items_details) - 1) * row_height)

    # Draw rows
    for i, item in enumerate(items_details):
        row_y = table_y_start - 35 - (i * row_height)
        pdf.drawString(10, row_y - 5, str(i + 1))  # SI.no
        pdf.drawString(40, row_y - 5, item["item_name"])  # Description
        pdf.drawString(165, row_y - 5, item["HSNCode"].upper())  # HSN Code
        pdf.drawString(225, row_y - 5, item["qty"])  # Quantity
        pdf.drawString(255, row_y - 5, item["uom"].upper())  # UOM
        pdf.drawString(295, row_y - 5, item["rate"])  # Rate
        pdf.drawString(340, row_y - 5, f'{item["gst"]}%')  # GST%
        pdf.drawString(385, row_y - 5, item["totalPrice"])  # Total Price

        # Draw horizontal line after each row
        pdf.line(0, row_y - 10, width - 100, row_y - 10)

    # Draw vertical lines to separate columns (including column headings)
    column_positions = [
        0,
        35,
        160,
        220,
        250,
        290,
        330,
        380,
        width,
    ]  # Include table borders
    for x in column_positions:
        pdf.line(x, table_y_start, x, table_height - 10)

    # ///////////////// Half ////////////////////////////////

    # Count the number of items
    item_count = len(items_details)
    if item_count > 10:
        # pdf.setLineWidth(2)
        # pdf.rect(5, 5, width - 10, height - 10)
        # pdf.drawString(50, height - top_margin - 50, "")
        # pdf.rect(0, 0, width - 2 * left_margin, height - 2 * top_margin)  # Example border
        # Count the number of items
        pdf.showPage()
        # Shift content inward
        pdf.translate(left_margin, top_margin)
        pdf.drawString(0, height - top_margin - 50, "")
        pdf.rect(
            0, 0, width - 2 * left_margin, height - 2 * top_margin
        )  # Example border

    # Define section heights for the remaining 50%
    remaining_50_height = 0.5 * height
    next_50_y_start = section2_y_end
    next_50_y_end = next_50_y_start - remaining_50_height
    vertical_offset = 160
    shifted_y_start = next_50_y_start - vertical_offset

    # Line at the start of Section 1
    pdf.line(0, shifted_y_start - 90, width - 100, shifted_y_start - 90)

    # Section 1: Payment Terms
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(
        width / 2.5, shifted_y_start - 105, "Payment Terms: 45 Days LC"
    )

    # Line at the between of Section 1
    pdf.line(0, shifted_y_start - 110, width - 100, shifted_y_start - 110)

    # Section 2: PO Number and Date
    section2_y_start = shifted_y_start - 40
    pdf.setFont("Helvetica", 10)
    pdf.drawString(10, section2_y_start - 85, f"Purchase Order No:{purchase_order_no}")
    pdf.drawRightString(
        width - 110, section2_y_start - 85, f"Date: {purchase_order_date}"
    )

    # Line at the end of Section 2
    pdf.line(0, section2_y_start - 90, width - 100, section2_y_start - 90)

    # Section 3: Bank Details and Total Amounts
    section3_y_start = section2_y_start - 30
    section3_height = remaining_50_height * 0.40
    left_section3_width = width * 0.5

    # Left 50% (Bank Details)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(20, section3_y_start - 90, "Our Bank Details:")

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20, section3_y_start - 110, "A/C No")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(80, section3_y_start - 110, ": 012705300003092")

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20, section3_y_start - 130, "Bank ")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(80, section3_y_start - 130, ": Danalaxmi Bank Ltd.")

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20, section3_y_start - 150, "Branch ")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(80, section3_y_start - 150, ": Peelamedu, Coimbatore-04")

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20, section3_y_start - 170, "IFSC Code")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(80, section3_y_start - 170, ": DLXB0000127")

    # Right 50% (Amounts)
    right_section3_start = section3_y_start - 10
    section3_right_x_start = left_section3_width

    # Calculate the width of the right section (50%)
    right_section_width = width - left_section3_width

    # Calculate the x-coordinate for the 30:20 divider
    divider_x = section3_right_x_start + (right_section_width * 0.3)

    # Draw the vertical line for the 30:20 ratio
    pdf.line(
        divider_x + 20,
        section3_y_start - 60,
        divider_x + 20,
        section3_y_start - section3_height - 12,
    )

    # Divide into 30:20 ratio
    pdf.line(
        left_section3_width - 60,
        section3_y_start - 60,
        left_section3_width - 60,
        section3_y_start - section3_height - 12,
    )

    amount_rows = [
        ("Total Amount before Tax", totalUnitPrice),
        ("Add SGST   ", half_gst),
        ("Add CGST   ", half_gst),
        ("Add IGST   ", "0.00"),
        ("Tax Amount GST", totalGST),
        ("Total Amount after Tax", totalBill),
    ]
    pdf.setFont("Helvetica", 10)
    for i, (label, value) in enumerate(amount_rows):
        row_y = right_section3_start - (i * 20)
        pdf.drawString(section3_right_x_start - 50, row_y - 65, label)
        pdf.drawRightString(width - 110, row_y - 65, value)
        pdf.line(section3_right_x_start - 60, row_y - 50, width - 100, row_y - 50)

    # Line at the end of Section 2
    pdf.line(0, right_section3_start - 170, width - 100, right_section3_start - 170)

    # Section 4: Total Amount in Words
    section4_y_start = section3_y_start - section3_height - 20

    # Left 50% (Bank Details)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(10, section4_y_start - 5, "Amount in Words:")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2.5, section4_y_start - 20, total_bill_in_words)

    # Line at the end of Section 2
    pdf.line(0, right_section3_start - 210, width - 100, right_section3_start - 210)

    # Section 5: Terms & Conditions
    section5_y_start = section4_y_start - 42

    # Bold title
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(10, section5_y_start - 5, "TERMS & CONDITIONS:")

    # Normal text
    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        20,
        section5_y_start - 15,
        "Our responsibility ceases after the goods have been delivered to the carriers.",
    )
    pdf.drawString(
        20,
        section5_y_start - 25,
        "No claims for breakage or shortage during transit entertained. Subject to Coimbatore Jurisdiction.",
    )

    # Draw a horizontal line at the end of this section
    pdf.line(0, section5_y_start - 30, width - 100, section5_y_start - 30)

    # Section 6: Tax on Reverse Charge
    section6_y_start = section5_y_start - 60
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(
        width / 2.5, section6_y_start + 17, "Tax is payable on Reverse Charge: NO"
    )

    # Draw a horizontal line at the end of this section
    pdf.line(0, section6_y_start + 10, width - 100, section6_y_start + 10)

    # Section 7: Consignee and Signature
    section7_y_start = section6_y_start - 40
    section7_y_end = (
        section7_y_start - 78
    )  # Adjusted to account for the height of Section 7
    left_section7_width = width * 0.4
    pdf.setFont("Helvetica", 10)

    # Left 50%: Consignee
    pdf.drawString(20, section7_y_start + 38, "Received the above in good condition.")
    pdf.drawString(20, section7_y_start - 10, "Signature of the Consignee")

    # Right 50%: Proprietor
    pdf.drawString(
        left_section7_width + 20,
        section7_y_start + 38,
        "For Sree Venkateswara Textiles & Chemicals",
    )
    pdf.drawString(left_section7_width + 20, section7_y_start - 10, "Proprietor")

    # Vertical line between the sections
    pdf.line(
        left_section7_width + 10,
        section7_y_start + 50,
        left_section7_width + 10,
        section7_y_end + 50,
    )

    # Draw a border around the whole PDF
    # pdf.setLineWidth(1)
    # pdf.rect(5,5, width - 10, height - 10)

    pdf.save()


# ////////////////////////// Invoice Generation ends ////////////////////////////


# @app.route("/analyticPage")
# def analyticPage():
# 	return render_template('Analytic.html')


@app.route("/itemsPage", methods=["GET", "POST"])
def itemsPage():
    try:
        db = current_app.config["FIRESTORE_DB"]  # Access Firestore client

        # Fetch items from Firestore
        items_ref = (
            db.collection("itemDetails")
            .order_by("created_date", direction=firestore.Query.DESCENDING)
            .stream()
        )
        unique_items = set()  # To store distinct item names
        data = []  # To store the final data for rendering
        # supp_ref = db.collection('invoiceDetails').order_by('created_date', direction=firestore.Query.DESCENDING)
        #     all_supp_docs = list(supp_ref.stream())  # Call `.stream()` only once here

        # print("Fetching items from itemDetails collection...")

        for doc in items_ref:
            doc_data = doc.to_dict()
            item_id = doc.id  # Get the document ID (item_id)
            userName = doc_data.get("userName", "Unknown")  # Fetch userName
            item_name = doc_data.get("item_name", "Unknown")  # Fetch item_name
            HSNCode = doc_data.get("HSNCode", "Unknown")
            gst = doc_data.get("gst", "Unknown")
            uom = doc_data.get("uom", "Unknown")

            # Add unique items to the set
            if item_name not in unique_items:
                unique_items.add(item_name)

                # Add item details along with suppliers and item_id to data
                data.append(
                    {
                        "item_id": item_id,
                        "item_name": str(item_name).upper(),
                        "userName": userName,
                        "HSNCode": HSNCode.upper(),  # Add HSNCode
                        "gst": gst,  # Add gst
                        "uom": uom.upper(),  # Add uom
                    }
                )

        # Implement pagination
        per_page = 5  # Items per page
        page = int(request.args.get("page", 1))  # Current page number (default: 1)
        total_records = len(data)  # Total number of records
        total_pages = (
            total_records + per_page - 1
        ) // per_page  # Calculate total pages

        # Calculate start and end indices for slicing
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        # Slice the data for the current page
        paginated_data = data[start_idx:end_idx]

        # Generate pagination buttons
        buttons = list(range(1, total_pages + 1))

        # Print the final data being passed to the template
        # print("Final data to be rendered (current page):")
        print(paginated_data)

        # Render template with paginated data and pagination buttons
        return render_template(
            "Items.html",
            data=paginated_data,
            item_names=list(unique_items),
            current_page=page,
            total_pages=total_pages,
            buttons=buttons,
            per_page=per_page,
        )

    except Exception as e:
        print(f"Error: {e}")
        return render_template(
            "Items.html",
            data=[],
            item_names=[],
            current_page=1,
            total_pages=0,
            buttons=[],
        )


@app.route("/consigneePage", methods=["GET", "POST"])
def consigneePage():
    try:
        db = current_app.config["FIRESTORE_DB"]  # Access Firestore client

        # Fetch items from Firestore
        consignee_ref = (
            db.collection("consigneeDetails")
            .order_by("created_date", direction=firestore.Query.DESCENDING)
            .stream()
        )
        unique_items = set()  # To store distinct item names
        data = []  # To store the final data for rendering

        # print("Fetching items from itemDetails collection...")

        for doc in consignee_ref:
            doc_data = doc.to_dict()
            consignee_id = doc.id  # Get the document ID (cosignee_id)
            userName = doc_data.get("username", "Unknown")  # Fetch userName
            consignee_name = doc_data.get(
                "consignee_name", "Unknown"
            )  # Fetch item_name
            gst_no = doc_data.get("gst_no", "Unknown")
            address = doc_data.get("address", "Unknown")
            state = doc_data.get("state", "Unknown")
            code = doc_data.get("code", "Unknown")

            # Add unique items to the set
            if consignee_name not in unique_items:
                unique_items.add(consignee_name)

                # Add item details along with suppliers and item_id to data
                data.append(
                    {
                        "consignee_id": consignee_id,
                        "consignee_name": consignee_name.upper(),
                        "username": userName,
                        "gst_no": gst_no.upper(),  # Add HSNCode
                        "address": address.upper(),
                        "state": state.upper(),  # Add HSNCode
                        "code": code,  # Add gst
                    }
                )

        # Implement pagination
        per_page = 5  # Items per page
        page = int(request.args.get("page", 1))  # Current page number (default: 1)
        total_records = len(data)  # Total number of records
        total_pages = (
            total_records + per_page - 1
        ) // per_page  # Calculate total pages

        # Calculate start and end indices for slicing
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        # Slice the data for the current page
        paginated_data = data[start_idx:end_idx]

        # Generate pagination buttons
        buttons = list(range(1, total_pages + 1))

        # Print the final data being passed to the template
        # print("Final data to be rendered (current page):")
        print("items-names--------------", unique_items)

        # Render template with paginated data and pagination buttons
        return render_template(
            "consignee.html",
            data=paginated_data,
            consignee_names=list(unique_items),
            current_page=page,
            total_pages=total_pages,
            buttons=buttons,
            per_page=per_page,
        )

    except Exception as e:
        print(f"Error: {e}")
        return render_template(
            "index.html",
            data=[],
            item_names=[],
            current_page=1,
            total_pages=0,
            buttons=[],
        )


# Redirect to supplier page
@app.route("/generateInvoicePage")
def generateInvoicePage():
    try:
        if "user" in session:
            db = current_app.config["FIRESTORE_DB"]

            # Fetch all consignee details
            consignee_ref = db.collection("consigneeDetails").stream()
            consignee_names = set()

            for doc in consignee_ref:
                doc_data = doc.to_dict()
                consignee_name = doc_data.get(
                    "consignee_name", ""
                ).strip()  # Get consignee_name

                if consignee_name:  # Ensure consignee_name is not empty
                    consignee_names.add(consignee_name)

            # Total consignee count
            total_consignee = len(consignee_names)

            # Fetch all item details
            items_ref = db.collection("itemDetails").stream()
            unique_items = set()

            for doc in items_ref:
                doc_data = doc.to_dict()
                item_name = doc_data.get("item_name", "").strip()  # Get item_name

                if item_name:  # Ensure item_name is not empty
                    unique_items.add(item_name)

            # Total item count
            total_items = len(unique_items)

            # Convert sets to sorted lists
            consignee_names_list = sorted(list(consignee_names))
            item_name_list = sorted(list(unique_items))

            # Debugging logs
            print("Consignee Names:", consignee_names_list)
            print("Item Names:", item_name_list)

            return render_template(
                "generate_invoice.html",
                Total_Consignee=total_consignee,
                Total_Items=total_items,
                item_names=item_name_list,
                consignee_names=consignee_names_list,
            )
        else:
            dispMsg = ["Welcome to Sree Venkateswara Textiles & Chemicals! "]
            return render_template(
                "index.html",
                welcome_messages=dispMsg,
                login_message="Please login to continue.",
            )
    except Exception as e:
        # Log the error
        print("An error occurred:", e)

        # Fallback to the else statement
        dispMsg = ["Welcome to Sree Venkateswara Textiles & Chemicals! "]
        return render_template(
            "index.html",
            welcome_messages=dispMsg,
            login_message="Please login to continue.",
        )


@app.route("/searchInvoiceConsignee", methods=["POST", "GET"])
def searchInvoiceConsignee():
    try:
        # Get form data
        search_type = request.form.get("searchType")
        search_term = request.form.get("searchTerm").strip()  # Get the search term
        search_term = (
            search_term.lower() if search_type == "Consignee Name" else search_term
        )  # Apply capitalize_words

        db = current_app.config["FIRESTORE_DB"]

        item_records = []
        # consignee_list = []  # Track unique item names

        if search_type == "Consignee Name":
            # Search by Item Name within itemDetails collection
            docs = db.collection("invoiceDetails").stream()
            for doc in docs:
                formatted_created_date = (
                    doc.get("created_date").strftime("%Y-%m-%d")
                    if doc.get("created_date")
                    else "N/A"
                )
                data = doc.to_dict()
                invoice_no = data.get("invoice_id", "")  # Get the document ID (item_id)
                consignee_name = (
                    data.get("consignee_name", "").strip().upper()
                )  # Get the item_name
                gst_no = data.get("gst_no", "")
                invoice_date = formatted_created_date
                purchase_order_date = data.get("purchase_order_date", "")
                purchase_order_no = data.get("purchase_order_no", "")
                totalBill = data.get("totalBill", "")
                # Match the item name with the search term, case-insensitive
                if consignee_name.lower() == search_term.lower():
                    # unique_items.add(consignee_name)  # Add to the set of unique items

                    # Append the item record with item_name, userName, and the matching suppliers
                    item_records.append(
                        {
                            "invoice_no": invoice_no,
                            "consignee_name": consignee_name,
                            "userName": data.get("userName", ""),
                            "gst_no": gst_no,
                            "invoice_date": invoice_date,
                            "purchase_order_date": purchase_order_date,
                            "purchase_order_no": purchase_order_no,
                            "totalBill": totalBill,
                        }
                    )

        print("Unique Item Records: ", item_records)

        # Render the template with the filtered and unique item records
        return render_template(
            "view_invoice.html",
            supp_records=item_records,
            current_page=0,
            total_pages=0,
            buttons=-0,
            per_page=0,
        )

    except Exception as e:
        # Log the exception and render an error message
        error_message = f"An error occurred: {str(e)}"
        print(error_message)  # Log the error for debugging
        return render_template("view_invoice.html", data=[])


@app.route("/viewInvoicePage", methods=["GET", "POST"])
def viewInvoicePage():
    try:

        if "user" in session:
            db = current_app.config["FIRESTORE_DB"]

            # Query supplier details, ordered by createdDate in descending order
            supp_ref = db.collection("invoiceDetails").order_by(
                "created_date", direction=firestore.Query.DESCENDING
            )
            all_supp_docs = list(supp_ref.stream())  # Call `.stream()` only once here

            # Pagination logic
            per_page = 5
            page = int(
                request.args.get("page", 1)
            )  # Get the page number from request arguments (default: 1)

            # Calculate start and end indices for slicing
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page

            # Slice the records
            supp_docs = all_supp_docs[start_idx:end_idx]

            # Process and extract required details
            supp_records = []
            for supp in supp_docs:
                data = supp.to_dict()
                formatted_created_date = (
                    data.get("created_date").strftime("%Y-%m-%d")
                    if data.get("created_date")
                    else "N/A"
                )
                if (
                    "consignee_name" in data
                    and "gst_no" in data
                    and "purchase_order_date" in data
                    and "purchase_order_no" in data
                    and "totalBill" in data
                    and "created_date" in data
                ):
                    supp_record = {
                        "invoice_no": supp.id,
                        # "invoice_no": data.get("invoice_id", "N/A"),
                        "consignee_name": data.get("consignee_name", "N/A").upper(),
                        "gst_no": data.get("gst_no", "N/A").upper(),
                        "purchase_order_date": data.get("purchase_order_date", "N/A"),
                        "purchase_order_no": data.get(
                            "purchase_order_no", "N/A"
                        ).upper(),
                        "totalBill": data.get("totalBill", "N/A"),
                        "invoice_date": formatted_created_date,
                    }
                    supp_records.append(supp_record)

            # Calculate total pages and generate button data
            total_records = len(all_supp_docs)
            total_pages = (total_records + per_page - 1) // per_page  # Ceiling division
            buttons = list(range(1, total_pages + 1))

            consignee_ref = db.collection("consigneeDetails").stream()
            unique_items = set()  # To store distinct item names
            for doc in consignee_ref:
                doc_data = doc.to_dict()
                consignee_name = doc_data.get(
                    "consignee_name", "Unknown"
                )  # Fetch item_name
                # Add unique items to the set
                if consignee_name not in unique_items:
                    unique_items.add(consignee_name)

            # print("consignee_name----------",consignee_name)

            # Render the template with processed records
            return render_template(
                "view_invoice.html",
                supp_records=supp_records,
                buttons=buttons,
                consignee_names=list(unique_items),
                current_page=page,
                total_pages=total_pages,
                per_page=per_page,
            )
        else:
            dispMsg = ["Welcome to Sree Venkateswara Textiles & Chemicals!"]
            return render_template(
                "index.html",
                welcome_messages=dispMsg,
                login_message="Some Error in View Invoice Pages",
            )
    except Exception as e:
        # Log the exception and render an error message
        error_message = f"An error occurred: {str(e)}"
        print(error_message)  # Log the error for debugging
        return render_template("view_invoice.html", data=[])
    # except Exception as e:
    #     print("An error occurred:", e)
    #     dispMsg = ["Welcome to Sree Venkateswara Textiles & Chemicals!"]
    # return render_template("index.html", welcome_messages=dispMsg, login_message="Some Error in View Invoice Page")


# -----------//------------//--------------------#


@app.route("/")
def index():
    global flgLoggedIn
    flgLoggedIn = False

    dispMsg = ["Welcome to Sree Venkateswara Textiles & Chemicals! "]
    return render_template("index.html", welcome_messages=dispMsg, login_message="")


@app.route("/Home", methods=["POST", "GET"])
def greeter():
    global flgLoggedIn
    global strUserId
    global strUser
    global lstMstrICD
    global strUserRole

    if "user" in session:
        try:
            # LoginCheck
            # print(request.method)
            session.permanent = True  # Mark the session as permanent
            print("session['user']------", session["user"])
            # Get Total Docs
            db = firestore.client()
            doc_ref = db.collection("productDetails")
            docs = doc_ref.get()
            # strDrawringCount = str(len(docs))
            # lst_Patient = []

            # for doc in docs:
            # 		dic_Patient = doc.to_dict()
            # 		strCustomerName = dic_Patient["productCustomerName"]
            # 		if strCustomerName not in lst_Patient:
            # 			lst_Patient.append(dic_Patient["productCustomerName"])
            # strCustomerCount = str(len(lst_Patient))
            # updateListSearchTerms()

            db = current_app.config["FIRESTORE_DB"]
            # Total Consignees
            consigee_ref = db.collection("consigneeDetails")
            # Count the number of documents to get total suppliers
            Total_Consignee = len(consigee_ref.get())

            # items Details Count
            item_ref = db.collection("itemDetails")
            # Count the number of documents to get total suppliers
            Total_items = len(item_ref.get())

            # invoice Details Count
            invoice_ref = db.collection("invoiceDetails").where("status", "==", None)
            # Count the number of documents to get the total number of POs
            Total_invoice = len(invoice_ref.get())

            role = 1 if strUserRole == "Admin" else 0

            print(Total_Consignee)
            print(Total_items)
            print(Total_invoice)

            # --------- Total Bill ----------

            # Fetch all POs and calculate total bill
            total_bill_amount = 0  # Initialize the total bill amount
            for invoice in invoice_ref.get():
                invoice_data = invoice.to_dict()
                total_bill = invoice_data.get(
                    "totalBill", "0"
                )  # Default to 0 if total_bill is not found
                try:
                    total_bill_amount += float(total_bill)  # Convert to float and add
                except ValueError:
                    print(
                        f"Invalid total_bill value: {total_bill}"
                    )  # Log invalid entries

            # Format the total_bill_amount after summation
            if total_bill_amount >= 10**7:  # Crores
                formatted_total_bill = f"{total_bill_amount / 10**7:.1f}Cr"
            elif total_bill_amount >= 10**5:  # Lakhs
                formatted_total_bill = f"{total_bill_amount / 10**5:.1f}L"
            elif total_bill_amount >= 10**3:  # Thousands
                formatted_total_bill = f"{total_bill_amount / 10**3:.1f}k"
            else:  # Below 1000
                formatted_total_bill = (
                    f"{total_bill_amount:.2f}"  # Keep two decimal places
                )

            # Example: Pass `formatted_total_bill` to the template or use it elsewhere
            print(f"Formatted Total Bill Amount: {formatted_total_bill}")

            # --------Graph----------

            # Get the selected year or set a default
            # Set timezone
            # india_tz = pytz.timezone("Asia/Kolkata")
            today = datetime.now()
            current_year = today.year
            current_month = today.month

            if current_month >= 4:  # From April onward
                start_year = current_year % 100  # Get the last two digits of the year
                end_year = (current_year + 1) % 100
            else:  # Before April
                start_year = (current_year - 1) % 100
                end_year = current_year % 100

            # Format the fiscal year as 'YY-YY'
            default_year = f"{start_year:02d}-{end_year:02d}"

            # Use the default year if 'year' parameter is not provided
            selected_year = request.args.get("year", default_year)
            start_year = int(selected_year.split("-")[0]) + 2000
            end_year = start_year + 1

            # Define the month range dynamically based on selected year
            start_date = datetime(start_year, 4, 1, tzinfo=pytz.UTC)
            end_date = datetime(end_year, 3, 31, tzinfo=pytz.UTC)

            # Convert start_date and end_date to the same timezone as created_date
            # start_date = india_tz.localize(start_date)
            # end_date = india_tz.localize(end_date)

            # print("Start year////////",start_date)
            # print("End year",end_date)

            # Query Firestore for POs in the selected year range
            invoice_ref = db.collection("invoiceDetails")
            invoice_docs = invoice_ref.where("status", "==", None).get()
            invoice_counts = [0] * 12  # Initialize counts for 12 months
            for doc in invoice_docs:
                invoice_data = doc.to_dict()
                try:
                    # Try parsing with date and time format
                    created_date = invoice_data["created_date"]

                    # Convert created_date_str to a datetime object
                    # created_date = datetime.strptime(created_date_str[:-6], "%Y-%m-%d %H:%M:%S")
                    # print("Created Date",created_date)
                    # created_date = created_date_obj.astimezone(pytz.timezone("Asia/Kolkata"))

                except ValueError:
                    # Fallback to date-only formats
                    # created_date_obj = invoice_data['created_date']
                    # created_date = created_date_obj.astimezone(pytz.timezone("Asia/Kolkata"))
                    created_date = invoice_data["created_date"]

                if start_date <= created_date <= end_date:
                    month_index = (created_date.month - 4) % 12
                    invoice_counts[month_index] += 1

            print("invoice_counts", invoice_counts)

            # Generate the graph
            months = [
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
                "Jan",
                "Feb",
                "Mar",
            ]
            plt.figure(figsize=(6, 3))
            plt.bar(months, invoice_counts, color="blue")
            plt.title(f"PO Count for {selected_year}")
            # plt.xlabel("Months", fontsize=10)
            plt.ylabel("Invoice Count", fontsize=10)
            plt.yticks(range(0, 100, 10))  # Fixed y-axis from 0 to 100
            plt.savefig("po_graph.png")  # Save the graph as an image

            return render_template(
                "Analytic.html",
                role=role,
                Total_Consignee=Total_Consignee,
                Total_items=Total_items,
                Total_invoice=Total_invoice,
                time=time,
                total_bill_amount=formatted_total_bill,
                year=selected_year,
            )
        except Exception as e:
            strMessage = ""
            for i in traceback.format_exception(*sys.exc_info()):
                strMessage = strMessage + " " + i
            print(strMessage)
            dispMsg = ["Welcome to Sree Venkateswara Textiles & Chemicals! "]
            return render_template(
                "Analytic.html", welcome_messages=dispMsg, login_message=strMessage
            )

    elif request.method == "POST":
        print("POST-------------")
        email = request.form["username_input"]
        password = request.form.get("password_input")
        try:
            user = pb.auth().sign_in_with_email_and_password(email, password)
            strUserId = user["idToken"]
            strUserRole = ""
            strUser = email
            print("strUser-------", strUser)
            session["user"] = strUser

            print("session-strUser---", session["user"])

            # print(f"Username set in session:{strUser}")
            strfbuserid = auth.get_user_by_email(email).uid
            # print("Logged in user")
            # Get User Role
            db = firestore.client()
            doc_ref = db.collection("users").document(strfbuserid)
            doc_ref.update({"lastlogin": firestore.SERVER_TIMESTAMP})
            doc_ref = db.collection("users").where("email", "==", email)
            docs = doc_ref.get()
            for doc in docs:

                dic_Patient = doc.to_dict()
                strUserRole = dic_Patient["Role"]

            # print(strUserRole)
            # LoginCheck
            # print(request.method)
            # Get Total Docs
            # db = firestore.client()
            # doc_ref = db.collection(u'productDetails')
            # docs = doc_ref.get()
            # strDrawringCount = str(len(docs))
            # lst_Patient = []
            # for doc in docs:
            # 		dic_Patient = doc.to_dict()
            # 		strCustomerName = dic_Patient["productCustomerName"]
            # 		if strCustomerName not in lst_Patient:
            # 			lst_Patient.append(dic_Patient["productCustomerName"])
            # strCustomerCount = str(len(lst_Patient))
            # updateListSearchTerms()
            # # print(strDrawringCount)
            db = current_app.config["FIRESTORE_DB"]
            # Total Consignees
            consigee_ref = db.collection("consigneeDetails")
            # Count the number of documents to get total suppliers
            Total_Consignee = len(consigee_ref.get())

            # items Details Count
            item_ref = db.collection("itemDetails")
            # Count the number of documents to get total suppliers
            Total_items = len(item_ref.get())

            # invoice Details Count
            invoice_ref = db.collection("invoiceDetails")
            # Count the number of documents to get the total number of POs
            Total_invoice = len(invoice_ref.get())

            role = 1 if strUserRole == "Admin" else 0

            print(Total_Consignee)
            print(Total_items)
            print(Total_invoice)

            # --------- Total Bill ----------

            # Fetch all POs and calculate total bill
            total_bill_amount = 0  # Initialize the total bill amount
            for invoice in invoice_ref.get():
                invoice_data = invoice.to_dict()
                total_bill = invoice_data.get(
                    "totalBill", "0"
                )  # Default to 0 if total_bill is not found
                try:
                    total_bill_amount += float(total_bill)  # Convert to float and add
                except ValueError:
                    print(
                        f"Invalid total_bill value: {total_bill}"
                    )  # Log invalid entries

            # Format the total_bill_amount after summation
            if total_bill_amount >= 10**7:  # Crores
                formatted_total_bill = f"{total_bill_amount / 10**7:.1f}Cr"
            elif total_bill_amount >= 10**5:  # Lakhs
                formatted_total_bill = f"{total_bill_amount / 10**5:.1f}L"
            elif total_bill_amount >= 10**3:  # Thousands
                formatted_total_bill = f"{total_bill_amount / 10**3:.1f}k"
            else:  # Below 1000
                formatted_total_bill = (
                    f"{total_bill_amount:.2f}"  # Keep two decimal places
                )

            # Example: Pass `formatted_total_bill` to the template or use it elsewhere
            print(f"Formatted Total Bill Amount: {formatted_total_bill}")

            # -------- Graph ---------------

            # Get the selected year or set a default
            today = datetime.today()
            current_year = today.year
            current_month = today.month

            if current_month >= 4:  # From April onward
                start_year = current_year % 100  # Get the last two digits of the year
                end_year = (current_year + 1) % 100
            else:  # Before April
                start_year = (current_year - 1) % 100
                end_year = current_year % 100

            # Format the fiscal year as 'YY-YY'
            default_year = f"{start_year:02d}-{end_year:02d}"

            # Use the default year if 'year' parameter is not provided
            selected_year = request.args.get("year", default_year)
            start_year = int(selected_year.split("-")[0]) + 2000
            end_year = start_year + 1

            # Define the month range dynamically based on selected year
            start_date = datetime(start_year, 4, 1, tzinfo=pytz.UTC)
            end_date = datetime(end_year, 3, 31, tzinfo=pytz.UTC)

            print("Start year", start_date)
            print("End year", end_date)

            # Query Firestore for POs in the selected year range
            invoice_ref = db.collection("invoiceDetails")
            invoice_docs = invoice_ref.get()

            invoice_counts = [0] * 12  # Initialize counts for 12 months
            for doc in invoice_docs:
                invoice_data = doc.to_dict()
                try:
                    # Try parsing with date and time format
                    created_date = invoice_data["created_date"]
                    # created_date = created_date_obj.astimezone(pytz.timezone("Asia/Kolkata"))

                except ValueError:
                    # Fallback to date-only format
                    created_date = invoice_data["created_date"]
                    # created_date = created_date_obj.astimezone(pytz.timezone("Asia/Kolkata"))

                if start_date <= created_date <= end_date:
                    month_index = (created_date.month - 4) % 12
                    invoice_counts[month_index] += 1

            print("invoice_counts", invoice_counts)

            # Generate the graph
            months = [
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
                "Jan",
                "Feb",
                "Mar",
            ]
            plt.figure(figsize=(6, 3))
            plt.bar(months, invoice_counts, color="blue")
            plt.title(f"PO Count for {selected_year}")
            # plt.xlabel("Months", fontsize=10)
            plt.ylabel("Invoice Count", fontsize=10)
            plt.yticks(range(0, 100, 10))  # Fixed y-axis from 0 to 100
            plt.savefig("po_graph.png")  # Save the graph as an image

            # Pass graph URL to the template
            return render_template(
                "Analytic.html",
                role=role,
                Total_Consignee=Total_Consignee,
                Total_items=Total_items,
                Total_invoice=Total_invoice,
                time=time,
                total_bill_amount=formatted_total_bill,
            )

        except Exception as e:
            strMessage = traceback.format_exc()  # Get the full traceback
            # print(strMessage)
            dispMsg = ["Welcome to Sree Venkateswara Textiles & Chemical! "]
            print(strMessage)
            return render_template(
                "index.html",
                welcome_messages=dispMsg,
                login_message="Please login using valid credentials.",
            )
    else:
        dispMsg = ["Welcome to Sree Venkateswara Textiles & Chemicals! "]
        return render_template(
            "index.html",
            welcome_messages=dispMsg,
            login_message="Please login to continue.",
        )


# def updateListSearchTerms():
# 	print("updateListSearchTerms - started")
# 	global lstSearchTermDwgNum
# 	global lstSearchTermDwgName
# 	global lstSearchTermCusName

# 	lstSearchTermDwgNum = []
# 	lstSearchTermDwgName = []
# 	lstSearchTermCusName = []
# 	if ('user' in session):
# 		try:
# 		#LoginCheck
# 			print(request.method)
# 			#Get Total Docs
# 			db = firestore.client()
# 			doc_ref = db.collection(u'productDetails')
# 			docs = doc_ref.get()
# 			strDrawringCount = str(len(docs))
# 			for doc in docs:
# 					dic_Patient = doc.to_dict()
# 					strCustomerName = dic_Patient["productCustomerName"]
# 					if strCustomerName not in lstSearchTermCusName:
# 						lstSearchTermCusName.append(strCustomerName)
# 					strDwgName = dic_Patient["productDrawingName"]
# 					if strDwgName not in lstSearchTermDwgName:
# 						lstSearchTermDwgName.append(strDwgName)
# 					strDwgNum = dic_Patient["productDrawingNumber"]
# 					if strDwgNum not in lstSearchTermDwgNum:
# 						lstSearchTermDwgNum.append(strDwgNum)

# 		except Exception as e:
# 			strMessage = ""
# 			for i in traceback.format_exception(*sys.exc_info()):
# 				strMessage = strMessage + " " + i
# 			print(strMessage)
# 	print("updateListSearchTerms - completed")


@app.route("/Logout", methods=["POST", "GET"])
def Logout():
    global strUser
    try:
        session.pop("user")
        session.clear()  # Clear the session
        dispMsgs = ["Welcome to Sree Venkateswara Textiles & Chemicals!"]
        return render_template(
            "index.html",
            welcome_messages=dispMsgs,
            login_message="You are successfully logged out.",
        )
    except:
        dispMsg = ["Welcome to Sree Venkateswara Textiles & Chemicals! "]
        return render_template("index.html", welcome_messages=dispMsg, login_message="")


# ---------------- Logging Setup ----------------
# log_dir = "logs"
# os.makedirs(log_dir, exist_ok=True)  # create logs folder if not exists
# log_file = os.path.join(log_dir, "app.log")

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[
#         logging.FileHandler(log_file, encoding="utf-8"),
#         logging.StreamHandler(),  # also print logs to console
#     ],
# )

# logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Run Flask in a background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Create the WebView window
    window = webview.create_window(
        "AUV Engineering ERP", app, confirm_close=True, min_size=(1000, 800)
    )

    # Start WebView loop (main thread)
    webview.start(on_close, window)


# if __name__ == "__main__":
#     app.run(debug=True)
#     webview.start(on_close)  # Attach the close callback
