from flask import Flask, render_template, request, jsonify, send_file, Blueprint, current_app, g, redirect, url_for,session
from datetime import datetime

import pytz

items_bp = Blueprint('items_bp', __name__)

def capitalize_words(text):
    # Split the text by spaces, capitalize each part, and then join them back with a space
    return ' '.join([word.capitalize() for word in text.split()])

@items_bp.route('/check_item_name', methods=['POST'])
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

@items_bp.route('/submit_item', methods=['POST'])
def submit_item():    
    try:
        if request.method == 'POST':
            print("Reached submit_item function")

            db = current_app.config['FIRESTORE_DB']  # Access Firestore client
            
            # Get form data
            item_names = request.form.getlist('item_name')
            HSNCodes = request.form.getlist('HSNCode')
            gsts = request.form.getlist('gst')
            uoms = request.form.getlist('uom')
            print("Received item names:", item_names, HSNCodes, gsts, uoms)

            if not item_names:
                raise ValueError("No item names received")

            logged_in_user = session.get('user')
            
            # Access the 'Count' document to get the current item_count
            count_doc_ref = db.collection('Count').document('count')
            count_doc = count_doc_ref.get()

            if count_doc.exists:
                count_data = count_doc.to_dict()
                item_count = count_data.get('item_count', 0)
            else:
                # Initialize item_count if the document doesn't exist
                item_count = 0

            print("Current item count:", item_count)

            current_time = datetime.now()
            current_time = current_time.astimezone(pytz.timezone('Asia/Kolkata'))
            print("current_time_item//////", current_time)

            # Store each item as a separate document
            for item_name, HSNCode, gst, uom in zip(item_names, HSNCodes, gsts, uoms):
                item_count += 1  # Increment item_count for each item

                # Create data for Firestore
                item_data = {
                    'item_id': str(item_count),
                    'item_name': item_name.strip().lower(),
                    'HSNCode': HSNCode.strip().lower(),
                    'gst': gst,
                    'uom': uom.strip().lower(),
                    'username': logged_in_user,
                    'created_date' : current_time,
                    'modified_date' : None,
                    'modified_username  ' : None,

                }

                # Store in Firestore with item_count as the document ID
                db.collection('itemDetails').document(str(item_count)).set(item_data)
            
            # Update the item_count in the Count document
            count_doc_ref.set({'item_count': item_count}, merge=True)

            print("Data successfully stored in Firestore")

            # Redirect to the ItemPage route
            return redirect(url_for('itemsPage'))

    except Exception as e:
        # Log the error for debugging
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return redirect(url_for('itemsPage', error_message=error_message))



@items_bp.route('/searchItemName', methods=['POST', 'GET'])
def searchItemName():
    try:
        # Get form data
        search_type = request.form.get('searchType')
        search_term = request.form.get('searchTerm').strip()  # Get the search term
        search_term = capitalize_words(search_term)  # Apply capitalize_words

        db = current_app.config['FIRESTORE_DB']

        item_records = []
        unique_items = set()  # Track unique item names

        if search_type == "Item Name":
            # Search by Item Name within itemDetails collection
            docs = db.collection('itemDetails').stream()
            for doc in docs:
                data = doc.to_dict()
                item_id = doc.id  # Get the document ID (item_id)
                item_name = data.get('item_name', '').strip()  # Get the item_name
                HSNCode = data.get('HSNCode', '')
                uom = data.get('uom', '')
                gst = data.get('gst', '')
                # Match the item name with the search term, case-insensitive
                if item_name.lower() == search_term.lower() and item_name not in unique_items:
                    unique_items.add(item_name)  # Add to the set of unique items               

                    # Append the item record with item_name, userName, and the matching suppliers
                    item_records.append({
                        'item_id':item_id,
                        'item_name': item_name.upper(),
                        'userName': data.get('userName', ''),
                        'HSNCode': HSNCode.upper(),
                        'gst': gst,
                        'uom': uom.upper(),
                    })

        print("Unique Item Records: ", item_records)

        # Render the template with the filtered and unique item records
        return render_template(
            "Items.html",
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
            "Items.html",
            data=[]
        )


@items_bp.route('/updateItemName', methods=['POST'])
def updateItemName():
    try:
        db = current_app.config['FIRESTORE_DB']
        data = request.get_json()
        itemName = data.get('itemName')
        HSNCode = data.get('HSNCode')
        gst = data.get('gst')
        uom = data.get('uom')
        itemId = data.get('itemId')  # Get the item_id from the request

        if not itemName or not itemId:
            return jsonify({'success': False, 'message': 'itemName and itemId are required'}), 400

        # Fetch the document by item_id (assuming item_id is the Firestore document ID)
        item_ref = db.collection('itemDetails').document(itemId)
        item_doc = item_ref.get()

        logged_in_user = g.strUser
        current_time = datetime.now()
        current_time = current_time.astimezone(pytz.timezone('Asia/Kolkata'))

        if item_doc.exists:
            # Update the item_name field in Firestore
            item_ref.update({'item_name': itemName.strip().lower(),
                             'HSNCode': HSNCode.strip().lower(),
                             'gst': gst.strip().lower(),
                             'uom': uom.strip().lower(),
                             'modified_username': logged_in_user,
                             'modified_date' : current_time})
            return jsonify({'success': True, 'message': 'Item Name updated successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Item not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@items_bp.route('/removeItem', methods=['POST'])
def remove_item():
    try:
        print("reached  removeitem")
        db = current_app.config['FIRESTORE_DB']
        data = request.get_json()
        item_id = data.get('itemId')
        print("item_id--", item_id)

        if not item_id:
            return jsonify({'success': False, 'message': 'item_id is required'}), 400

        # Remove the item from the itemDetails collection
        db.collection('itemDetails').document(item_id).delete()

        # Update the item_count in the Count collection
        count_doc_ref = db.collection('Count').document('count')  # Assuming 'count' is the document name
        count_doc = count_doc_ref.get()

        if count_doc.exists:
            current_count = count_doc.to_dict().get('item_count', 0)
            new_count = max(current_count - 1, 0)  # Ensure count doesn't go below zero
            count_doc_ref.update({'item_count': new_count})

        return jsonify({'success': True, 'message': 'Item removed and count updated successfully'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
