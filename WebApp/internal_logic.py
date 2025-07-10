import re
from flask import json, jsonify, request
from HandelDB import database_read, database_write


def add_list_from_telegram(data):
    
    print("Incoming data:", data)

    # DO NOT CONVERT to JSON here. Data is already a dictionary!
    list_name = data.get('list_name', 'Telegram List')
    items_text = data.get('items', '')
    chat_id = str(data.get('chat_id'))

    if not items_text:
        return {"error": "No items provided", "status": "error"}

    item_details = []


    for item in items_text.split(','):
        item = item.strip()

        if item:
            # Match first number in the string (int or float)
            match = re.search(r'\b\d+(\.\d+)?\b', item)
            if match:
                try:
                    quantity = float(match.group())
                except ValueError:
                    return jsonify({"error": f"Invalid quantity for item: {item}"}), 400
                product = item[:match.start()].strip()
                note = item[match.end():].strip()
            else:
                # No number found, default to quantity 1
                quantity = 1.0
                product = item.strip()
                note = ''

            if not product:
                return jsonify({"error": f"Missing product name in item: {item}"}), 400

            item_details.append({"product": product, "quantity": quantity, "note": note})

    print("item_details", item_details)

    existing_list = database_read("SELECT id FROM lists WHERE name = ? and archived=0 ", (list_name,))
    if existing_list:
        print(existing_list)
        list_id = existing_list[0]['id']
        created = False
    else:
        # Check if an archived list exists
        archived_list = database_read("SELECT id FROM lists WHERE name = ? AND archived = 1", (list_name,))
        if archived_list:
            # ✅ Archived list found → rename it (add '-archived')
            print("Found archived list, renaming it...")
            database_write("UPDATE lists SET name = name || '-archived' WHERE id = ?", (archived_list[0]['id'],))
        else:
            database_write("INSERT INTO lists (name,chat_id) VALUES (?,?)", (list_name,chat_id))
            list_id = database_read("SELECT max(id) as id FROM lists")[0]['id']
            created = True

    for item in item_details:
        product = item['product']
        quantity = item['quantity']
        note = item['note']

        prod = database_read("SELECT id FROM products WHERE name = ?", (product,))
        if prod:
            product_id = prod[0]['id']
        else:
            database_write("INSERT INTO products (name) VALUES (?)", (product,))
            product_id = database_read("SELECT max(id) as id FROM products")[0]['id']

        database_write("""
            INSERT INTO product_in_list (list_id, product_id, quantity, collected, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (list_id, product_id, quantity, 0, note))

    return {"status": "success", "list_id": list_id, "created": created}
