from flask import Flask, render_template, request, jsonify, send_file, Blueprint, current_app, g, redirect, url_for,session
from datetime import datetime

import pytz

consigee_bp = Blueprint('consigee_bp', __name__)

def capitalize_words(text):
    # Split the text by spaces, capitalize each part, and then join them back with a space
    return ' '.join([word.capitalize() for word in text.split()])

@consigee_bp.route('/check_item_name', methods=['POST'])
def check_item_name():
    db = current_app.config['FIRESTORE_DB']  # Access Firestore client
    item_name = request.json.get('item_name', '').strip()  # Get the item_name as a string
    item_name = capitalize_words(item_name).strip()
    
    if not item_name:
        return jsonify({'error': 'No item_name provided'}), 400

    # Fetch all documents from the 'itemDetails' collection
    items_docs = db.collection('itemDetails').stream()

    # Check for the item_name in the 'items' array
    for doc in items_docs:
        items = doc.to_dict().get('items', [])
        for item in items:
            if item.get('item_name') == item_name:
                return jsonify({'duplicate': True, 'item_name': item_name})

    # If no match is found
    return jsonify({'duplicate': False, 'item_name': item_name})

@consigee_bp.route("/getConsigneeDetails", methods=["POST"])
def get_consignee_details():
    try:
        db = current_app.config['FIRESTORE_DB']

        # Get the consignee_name from the request
        request_data = request.get_json()
        consignee_name = request_data.get("consignee_name", "").strip()

        print("consignee_name----",consignee_name)

        if not consignee_name:
            return jsonify({"success": False, "message": "Consignee name is required"}), 400

        # Query the consigneeDetails collection
        consignee_ref = db.collection("consigneeDetails").where("consignee_name", "==", consignee_name).stream()
        consignee_details = {}

        for doc in consignee_ref:
            consignee_details = doc.to_dict()
            break  # Assuming only one document matches the query
        
        print("Consignee details------",consignee_details)

        if not consignee_details:
            return jsonify({"success": False, "message": "Consignee not found"}), 404

        # Extract required details
        gst_no = consignee_details.get("gst_no", "N/A")
        state = consignee_details.get("state", "N/A")
        code = consignee_details.get("code", "N/A")
        address = consignee_details.get("address", "N/A")

        return jsonify({"success": True, "gst_no": gst_no, "state": state, "code": code, "address": address})

    except Exception as e:
        print("Error fetching consignee details:", e)
        return jsonify({"success": False, "message": "An error occurred while fetching consignee details"}), 500
    
@consigee_bp.route("/getItemDetails", methods=["POST"])
def get_items_details():
    try:
        db = current_app.config['FIRESTORE_DB']

        # Get the consignee_name from the request
        request_data = request.get_json()
        item_name = request_data.get("item_name", "").strip()

        print("item_name----",item_name)

        if not item_name:
            return jsonify({"success": False, "message": "item name is required"}), 400

        # Query the consigneeDetails collection
        item_ref = db.collection("itemDetails").where("item_name", "==", item_name).stream()
        item_details = {}

        for doc in item_ref:
            item_details = doc.to_dict()
            break  # Assuming only one document matches the query
        
        print("item details------",item_details)

        if not item_details:
            return jsonify({"success": False, "message": "item not found"}), 404

        # Extract required details
        HSNCode = item_details.get("HSNCode", "N/A")
        uom = item_details.get("uom", "N/A")
        gst = item_details.get("gst", "N/A")

        return jsonify({"success": True, "gst": gst, "HSNCode": HSNCode , "uom": uom})

    except Exception as e:
        print("Error fetching consignee details:", e)
        return jsonify({"success": False, "message": "An error occurred while fetching consignee details"}), 500


@consigee_bp.route('/submit_consignee', methods=['POST'])
def submit_consignee():    
    try:
        if request.method == 'POST':
            print("Reached submit_item function")

            db = current_app.config['FIRESTORE_DB']  # Access Firestore client
            
            # Get form data
            consignee_names = request.form.getlist('consignee_name')
            gst_nos = request.form.getlist('gst_no')
            addresss = request.form.getlist('address')
            states = request.form.getlist('state')
            codes = request.form.getlist('code')
            print("Received item names:", consignee_names,gst_nos,addresss,states,codes)

            # if not item_names:
            #     raise ValueError("No item names received")

            # logged_in_user = g.strUser
            logged_in_user=session.get('user')

            # print("logged_in_user------",logged_in_user)
            
            # Access the 'Count' document to get the current item_count
            count_doc_ref = db.collection('Count').document('count')
            count_doc = count_doc_ref.get()

            if count_doc.exists:
                count_data = count_doc.to_dict()
                consignee_count = count_data.get('consignee_count', 0)
            else:
                # Initialize item_count if the document doesn't exist
                consignee_count = 0

            print("Current item count:", consignee_count)

            current_time = datetime.now()
            current_time = current_time.astimezone(pytz.timezone('Asia/Kolkata'))

            # Store each item as a separate document
            for consignee_name,gst_no,address,state,code in zip(consignee_names,gst_nos,addresss,states,codes):
                consignee_count += 1  # Increment consignee_count for each item

                # Create data for Firestore
                consignee_data = {
                    'consignee_id': str(consignee_count),
                    'consignee_name': consignee_name.strip().lower() if consignee_name else None,
                    'gst_no': gst_no.strip().lower() if gst_no else None,
                    'address': address.strip().lower() if address else None,
                    'state': state.strip().lower() if state else None,
                    'code': code if code else None,
                    'username': logged_in_user if logged_in_user else None,
                    'created_date' : current_time,
                    'modified_date' : None,
                    'modified_username' : None
                }

                # Store in Firestore with item_count as the document ID
                db.collection('consigneeDetails').document(str(consignee_count)).set(consignee_data)
            
            # Update the item_count in the Count document
            count_doc_ref.set({'consignee_count': consignee_count}, merge=True)

            print("Data successfully stored in Firestore")

            # Redirect to the ItemPage route
            return redirect(url_for('consigneePage'))

    except Exception as e:
        # Log the error for debugging
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return redirect(url_for('consigneePage', error_message=error_message))



@consigee_bp.route('/searchConsignee', methods=['POST', 'GET'])
def searchConsignee():
    try:
        # Get form data
        search_type = request.form.get('searchType')
        search_term = request.form.get('searchTerm').strip()  # Get the search term
        # search_term = capitalize_words(search_term)  # Apply capitalize_words

        db = current_app.config['FIRESTORE_DB']

        item_records = []
        unique_items = set()  # Track unique item names

        if search_type == "Consignee Name":
            # Search by Item Name within itemDetails collection
            docs = db.collection('consigneeDetails').stream()
            for doc in docs:
                data = doc.to_dict()
                consignee_id = doc.id  # Get the document ID (item_id)
                consignee_name = data.get('consignee_name', '')
                gst_no = data.get('gst_no', '')
                address = data.get('address', '')
                state = data.get('state', '')
                code = data.get('code', '')
                # Match the item name with the search term, case-insensitive
                if consignee_name.lower() == search_term.lower() and consignee_name not in unique_items:
                    unique_items.add(consignee_name)  # Add to the set of unique items               

                    # Append the item record with item_name, userName, and the matching suppliers
                    item_records.append({
                        'consignee_id':consignee_id,
                        'consignee_name': consignee_name.upper(),
                        'username': data.get('userame', ''),
                        'gst_no': gst_no.upper(),
                        'address': address.upper(),
                        'state': state.upper(),
                        'code': code
                    })

        print("Unique Item Records: ", item_records)

        # Render the template with the filtered and unique item records
        return render_template(
            "consignee.html",
            data=item_records,
            current_page=0,
            total_pages=0,
            buttons=-0,
			per_page = 0
        )

    except Exception as e:
        # Log the exception and render an error message
        error_message = f"An error occurred: {str(e)}"
        print(error_message)  # Log the error for debugging
        return render_template(
            "consignee.html",
            data=[]
        )


@consigee_bp.route('/updateConsignee', methods=['POST'])
def updateConsignee():
    try:
        db = current_app.config['FIRESTORE_DB']
        data = request.get_json()
        consigneeName = data.get('consigneeName')
        gst_no = data.get('gst_no')
        address = data.get('address')
        state = data.get('state')  # Get the item_id from the request
        code = data.get('code')
        consignee_id = data.get('consignee_id')

        # if not itemName or not itemId:
        #     return jsonify({'success': False, 'message': 'itemName and itemId are required'}), 400

        # Fetch the document by item_id (assuming item_id is the Firestore document ID)
        item_ref = db.collection('consigneeDetails').document(consignee_id)
        item_doc = item_ref.get()

        logged_in_user = g.strUser
        current_time = datetime.now()
        current_time = current_time.astimezone(pytz.timezone('Asia/Kolkata'))

        if item_doc.exists:
            # Update the item_name field in Firestore
            item_ref.update({'consignee_name': consigneeName.strip().lower() if consigneeName else None,
                             'gst_no': gst_no.strip().lower() if gst_no else None,
                             'address': address.strip().lower() if address else None,
                             'state': state.strip().lower() if state else None,
                             'code': code,
                             'modified_username': logged_in_user,
                             'modified_date' : current_time})
            return jsonify({'success': True, 'message': 'Item Name updated successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Item not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@consigee_bp.route('/removeConsignee', methods=['POST'])
def removeConsignee():
    try:
        print("reached  removeitem")
        db = current_app.config['FIRESTORE_DB']
        data = request.get_json()
        item_id = data.get('itemId')
        print("item_id--", item_id)

        if not item_id:
            return jsonify({'success': False, 'message': 'item_id is required'}), 400

        # Remove the item from the itemDetails collection
        db.collection('consigneeDetails').document(item_id).delete()

        # Update the item_count in the Count collection
        count_doc_ref = db.collection('Count').document('count')  # Assuming 'count' is the document name
        count_doc = count_doc_ref.get()

        if count_doc.exists:
            current_count = count_doc.to_dict().get('consignee_count', 0)
            new_count = max(current_count - 1, 0)  # Ensure count doesn't go below zero
            count_doc_ref.update({'consignee_count': new_count})

        return jsonify({'success': True, 'message': 'Item removed and count updated successfully'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
