import csv
from datetime import datetime
import io
import os
import re
import sqlite3
import random
from threading import Thread
import threading
from flask import Flask, jsonify, send_file,flash,g,render_template,request,redirect, send_from_directory, session, url_for
import flask_login
import requests
from grocery_list import create_db
from HandelDB import database_read,database_write,create_account,enable_wal_mode
import uuid
import logging
import hashlib
from messages import get_message
from telegram_utils import send_telegram_message, extract_chat_id
#from internal_logic  import add_list_from_telegram # type: ignore
from flask import send_from_directory
import nest_asyncio
import asyncio

from user_settings import get_user_language, save_user_language


nest_asyncio.apply()

app = Flask(__name__)
app.secret_key = "dsvnjksnvjksdvnsjkvnsjvsvs"


WEBHOOK_URL = 'https://maliknot1bot.pythonanywhere.com/telegram'  # or your correct route
create_db()
enable_wal_mode()

grocery_lists = {}  # Dictionary to hold lists: { "List Name": [ {name, collected}, ... ] }
#Logs
handler = logging.FileHandler('LogFile.log') # creates handler for the log file
app.logger.addHandler(handler) # Add it to the built-in logger
app.logger.setLevel(logging.DEBUG)         # Set the log level to debug
logger = app.logger

#Log in 
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.context_processor
def inject_user():
    return dict(user=flask_login.current_user)

class User(flask_login.UserMixin):
    def __init__(self,userid,email,name):
        self.email = email
        self.name = name
        self.id = userid
    def get_dict(self):
        return{'userid': self.id,'email': self.email, 'name': self.name}
    
#User Login
@login_manager.user_loader
def load_user(userid):
    users = database_read(f"select  * from accounts where userid='{userid}';")
    if len(users)!=1:
        return None
    else:
        user = User(users[0]['userid'],users[0]['email'],users[0]['name'])
        user.id = userid
        return user  

@app.route("/register", methods=['GET'])
def registration_page():
    return render_template('register.html', alert="")

@app.route("/register", methods=['POST'])
def registration_request():
    form = dict(request.values)    
    folderid="0"
    if 'folderid' in request.values:
        folderid = request.values['folderid']
    id="1"
    if 'id' in request.values:
        id = request.values['id']
    reg_email = request.values['email']
    if reg_email:
        ok = create_account(form)
        session['formData'] = form
        print('ok:' ,ok)
        if ok == 1:            
            user = load_user(form['userid'])
            logger.info("New User Created: "+ user.name)           
            flask_login.login_user(user)            
            productsdata = database_read(f"select p.*,cat.name as catName from products p left JOIN categories cat on category_id = cat.id")
            categories = database_read(f"select * from categories order by name;")
            return render_template('index.html', all_items=productsdata,categories=categories)
        else:
            return redirect(f"/error") 
    else:
         return render_template('/register.html',alert = "Please insert valid email to register!")

@app.route("/login", methods=['GET'])
def login_page():
    return render_template('login.html',alert ="")

@app.route("/login", methods=['POST'])
def login_request():
    form = dict(request.values)
    users = database_read("select * from accounts where userid=:userid",form)

    if len(users) == 1: #user name exist, password not checked
        salt = users[0]['salt']
        saved_key = users[0]['password']
        generated_key = hashlib.pbkdf2_hmac('sha256',form['password'].encode('utf-8'),salt.encode('utf-8'),10000).hex()

        if saved_key == generated_key: #password match
            user = load_user(form['userid'])
            logger.info(f"Login successfull - '{form['userid']}'  date: {str(datetime.now())}")
            flask_login.login_user(user)
            productsdata = database_read(f"select p.*,cat.name as catName from products p left JOIN categories cat on category_id = cat.id")
            categories = database_read(f"select * from categories order by name;")
            all_lists =  database_read(f"select * from lists order by id desc;") 
            return render_template('index.html',user=flask_login.current_user, all_items=productsdata,lists=all_lists,categories=categories)
        
        else: #password incorrect
           logger.info(f"Login Failed - '{form['userid']}'  date: {str(datetime.now())}")
           return render_template('/login.html',alert = "Invalid user/password. please try again.") 
    else: #user name does not exist
        logger.info(f"Login Failed - '{form['userid']}'  date: {str(datetime.now())}")
        return render_template('/login.html',alert = "Invalid user/password. please try again.")

@app.route("/logout")
@flask_login.login_required
def logout_page():
    flask_login.logout_user()
    return redirect("/")
    
@app.route("/", methods=["GET", "POST"])
def index():
    if flask_login.current_user.is_authenticated:
        logger.info(str(flask_login.current_user.get_dict()) + "Has Logged in")
        if request.method == "POST":
            list_name = request.form.get("list_name", "").strip()
            if list_name and list_name not in grocery_lists:                
                sql = f"INSERT OR IGNORE INTO lists (name) VALUES  ('{list_name}');"
                ok = database_write(sql)
                #get list id...
                list_id =  database_read(f"select id from lists where name ='{list_name}';")
                curren_list= list_id[0]['id']
                return redirect(url_for("view_list",user=flask_login.current_user, list_id=curren_list))  
            
        all_lists =  database_read(f"select * from lists order by id desc;")      
        data = database_read(f"select p.*,cat.name as catName from products p left JOIN categories cat on category_id = cat.id")
        categories =  database_read(f"select * from categories order by name;")
        
        return render_template('index.html',user=flask_login.current_user,lists=all_lists, all_items=data,categories=categories)
    else:
        return redirect("/login")

@app.route("/add-items",methods=["post"])
def add_items():
    data = dict(request.values)
    return render_template('index2.html', all_items=data)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/category/<category_name>')
def category_name(category_name):
    categories =  database_read(f"select * from categories order by name;")
    cat_items = database_read(f"select p.*,cat.name as catName from products p left JOIN categories  cat on category_id = cat.id where cat.name ='{category_name}';")
    return render_template('category.html', cat=category_name,cat_items=cat_items,categories=categories)


@app.route('/product/<product_id>')
def product_disp(product_id):
    product = database_read(f"select p.*,cat.name as catName from products p left JOIN categories  cat on category_id = cat.id where p.id ='{product_id}';")
    return render_template('product.html', products=product) 


@app.route('/addproduct' , methods=['GET','POST'])
def addproduct():
    categories =  database_read(f"select * from categories order by name;")
    print(categories)
    if request.method == 'POST':
      form = dict(request.values)
      item = request.form['name']
      category_id = request.form['category']
      price =  request.form['price']
      unit =  request.form['unit']
      sql= f"INSERT INTO products (name,price,unit,category_id) VALUES ('{item}', '{price}', '{unit}', '{category_id}');"
      print(sql)
      ok = database_write(sql)
      print(ok)
      if ok == 1 :
        flash(f"Product Added!", "success")
        message = 'Product saved successfully'
        return render_template('index.html',messages=message)  
    else:
        return render_template('add_product.html',categories=categories) 

@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product = database_read(f"select p.*,cat.name as catName from products p left JOIN categories  cat on category_id = cat.id where p.id ='{product_id}';")
    
    category =  database_read(f"select * from categories order by name;")    
    if request.method == 'POST':
        form = dict(request.values)
        form['id'] = request.form['id']
        form['name'] = request.form['name']
        form['price'] = request.form['price']
        form['unit'] = request.form['unit']
        form['category'] = request.form['category']
        sql = "UPDATE products SET name =:name, price =:price,category_id =:category, unit =:unit where id =:id"
        ok = database_write(sql,form)
        if ok == 1:            
            flash(f"Product Saved!", "success")
            message = 'Product saved successfully'
            product = database_read(f"select p.*,cat.name as catName from products p left JOIN categories  cat on category_id = cat.id where p.id ='{request.form['id']}';")
            data = database_read(f"select p.*,cat.name as catName from products p left JOIN categories cat on category_id = cat.id")
            return render_template('index.html', all_items=data,categories=category,messages=message) 
    else:
        return render_template('edit_product.html', products=product,categories=category)

@app.route('/delete_Product/<int:product_id>', methods=['DELETE', 'POST'])
@flask_login.login_required
def delete_product(product_id):
    user = flask_login.current_user.get_dict()
    data=  dict(request.values)
    print("data",data)
    id = product_id
    sql = f"Delete from Products where id ='{id}' ;"

    ok = database_write(sql)
    if ok == 1:            
            flash(f"Product deleted successfully!", "success")
            message = 'Product deleted successfully' 
            #refresh form                                  
    else:
        flash(f"Error deleting product!", "error") 
    data = database_read(f"select p.*,cat.name as catName from products p left JOIN categories cat on category_id = cat.id")
    categories =  database_read(f"select * from categories order by name;")
    return render_template('index.html', all_items=data,categories=categories) 

@app.route("/list/<int:list_id>", methods=["GET", "POST"])
def view_list(list_id):
    
    list_info = database_read("SELECT name, chat_id FROM lists WHERE id = ?", (list_id,))
    if not list_info:
        return "List not found", 404
    list_chat_id = list_info[0]['chat_id']    
    # If coming from Telegram: extract via list name
    if 'from_telegram' in request.args:
        current_chat_id = extract_chat_id(list_info[0]['name'])
    else:
        return "Access restricted", 403  

    if current_chat_id != list_chat_id:
        return "Unauthorized", 403 
    

    lang = get_user_language(list_chat_id) or "en"
    confirm_message = get_message("confirm_all_collected", lang, quantity="{quantity}")

    #items  in list
    list_items_data = []  # make this a list
    items = database_read(f"select * from product_in_list where list_id ='{list_id}' order by collected asc;")
    list_data = database_read(f"select * from product_in_list where list_id ='{list_id}';")
    if items:
        for item in items:
            product_id = item['product_id']         
            item_data =  database_read(f"select pl.*,p.* from products p inner JOIN product_in_list  pl on pl.product_id = p.id where p.id ='{product_id}' and list_id='{list_id}' order by collected desc ;")
            if item_data:
                list_items_data.append(item_data[0])

    list_name_obj = database_read(f"select name from lists where id ='{list_id}';")

    if list_name_obj:
        list_name = list_name_obj[0]['name']
    else:
        list_name = " "
    items_data = database_read(f"select p.*,cat.name as catName from products p left JOIN categories cat on category_id = cat.id")
    categories =  database_read(f"select * from categories order by name;")   
    return render_template("list.html", list_id=list_id,list_data=list_data, items=list_items_data,list_name=list_name,all_items=items_data,categories=categories,confirm_message=confirm_message)

@app.route('/delete_List/<int:List_id>', methods=['DELETE', 'POST'])
@flask_login.login_required
def delete_List(List_id):
    user = flask_login.current_user.get_dict()
    data=  dict(request.values)
    print("data",data)
    id = List_id

    sql = f"Delete from lists where id ='{id}' ;"

    ok = database_write(sql)
    if ok == 1:            
            flash(f"List deleted successfully!", "success")
            message = 'List deleted successfully' 
            #refresh form                                  
    else:
        flash(f"Error deleting List!", "error") 
    data = database_read(f"select p.*,cat.name as catName from products p left JOIN categories cat on category_id = cat.id")
    categories =  database_read(f"select * from categories order by name;")
    return render_template('index.html', all_items=data,categories=categories) 

@app.route("/add_product_to_list", methods=["POST"])
def add_product_to_list():
    list_id = request.form.get("list_id", "").strip()
    product_id = request.form.get("product_id", "").strip()
    QTY = request.form.get("QTY", "").strip()
    notes = request.form.get("notes", "").strip()
    print('notes' , notes)

    if not list_id or not product_id:
        return "Missing list_name or product_name", 400
    # Check if already in list
    existing = database_read(f"SELECT 1 FROM product_in_list WHERE list_id ='{list_id}' AND product_id = '{product_id}';")

    if not existing:
      try:
        sql= f"INSERT INTO product_in_list (list_id, product_id,quantity,notes, collected) VALUES ('{list_id}', '{product_id}','{QTY}','{notes}',0);"
        ok = database_write(sql)
        print(ok)
        if ok == 1 :
            flash(f"Product Added to list!", "success")
            return render_template('list.html',list_id=list_id)
        else:
            flash(f"Failed to add product", "error")  
            return jsonify({'error': 'Missing required fields'}), 400
        
      except sqlite3.Error as e:
        print("SQLite error:", e)
        flash(f"Database error: {e}", "danger")
        return jsonify({'error': str(e)}), 500

@app.route('/update_collected/<int:item_id>', methods=['POST'])
def update_collected(item_id):
    try:
        data = request.get_json()
        
        collected = data.get('collected', 0)
        list_id = data.get('list_id', 0)
        product_id = data.get('product_id', 0)

        sql = f"""
            UPDATE product_in_list
            SET collected = ?
            WHERE product_id = ? AND list_id = ?
        """
        ok = database_write(sql, (collected, product_id, list_id))

        if ok == 1:
            # ✅ Check if all items in the list are collected
            items = database_read(
                "SELECT collected FROM product_in_list WHERE list_id = ?", (list_id,)
            )
            #list_complete = all(item['collected'] for item in items)
            list_complete = all(int(item['collected']) for item in items)

            if list_complete:
                chat_row = database_read("SELECT chat_id FROM lists WHERE id = ?", (list_id,))
                if chat_row and chat_row[0].get("chat_id"):
                    chat_id = chat_row[0]["chat_id"]
                    database_write("""
                        UPDATE lists
                        SET archived = 1,
                            name = CASE
                                WHEN name LIKE '%(Archived%' THEN name
                                ELSE name || ' (Archived ' || strftime('%Y%m%d%H%M%S', 'now') || ')'
                            END
                        WHERE id = ?
                    """, (list_id,))
                    try:
                        print("update_collected",chat_id,list_id)
                        send_telegram_message(chat_id, key="list_completed", list_id=list_id)                       
                    except Exception as e:
                        print("⚠️ Telegram error:", e)
            print("✅ Returning collected status updated with list_complete =", list_complete)    
            return jsonify({'message': 'Collected status updated', 'list_complete': list_complete}), 200

        else:
            return jsonify({'error': 'Update failed'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/Remove_product_from_list", methods=['DELETE', 'POST'])
def Remove_product_from_list():
    list_id = request.form.get("list_id", "").strip()
    product_id = request.form.get("product_id", "").strip()

    print('list_id' , list_id)

    if not list_id or not product_id:
        return "Missing list_name or product_name", 400

    try:
        sql= f"Delete from product_in_list where list_id= '{list_id}' and  product_id = '{product_id}';"
        ok = database_write(sql)
        print(ok)
        if ok > 0 :
            flash(f"Product removed from list!", "success")
            return render_template('list.html',list_id=list_id)
        else:
            flash(f"Failed to remove product", "error")  
            return jsonify({'error': 'Missing required fields'}), 400
        
    except sqlite3.Error as e:
        print("SQLite error:", e)
        flash(f"Database error: {e}", "danger")
        return jsonify({'error': str(e)}), 500
      
@app.context_processor
def inject_collected_count():
    def get_collected_count(list_id=None):
        if list_id is None:
            return 0
        sql = f"SELECT COUNT(*) as count FROM product_in_list WHERE list_id = '{list_id}' AND collected = 1"
        result = database_read(sql)
        return result[0]['count'] if result else 0

    return dict(get_collected_count=get_collected_count)

@app.route("/export/<list_name>")
def export(list_name):
    if list_name not in grocery_lists:
        return redirect(url_for("index"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Item", "Collected"])
    for item in grocery_lists[list_name]:
        writer.writerow([item["name"], "Yes" if item["collected"] else "No"])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), as_attachment=True,
                     download_name=f"{list_name}_grocery_list.csv", mimetype="text/csv")

@app.route("/user_lists/<chat_id>")
def user_lists(chat_id):
    lists = database_read("""
        SELECT 
            l.id, 
            l.name, 
            p.total_amount,
            DATE(p.timestamp) AS purchase_date
        FROM lists l
        LEFT JOIN purchases p ON l.id = p.list_id
        WHERE l.chat_id = ?
        ORDER BY l.id DESC
    """, (chat_id,))
    return render_template("user_lists.html", lists=lists)

@app.after_request
def add_header(response):
    if request.path.endswith('service-worker.js'):
        response.headers['Content-Type'] = 'application/javascript'
    if request.path.endswith('manifest.json'):
        response.headers['Content-Type'] = 'application/manifest+json'
    return response

#Region Telegrambot Api
@app.route('/api/add_list_from_telegram', methods=['POST'])
def add_list_from_telegram():
    data = request.get_json()
    list_name_bot = data.get('list_name', 'Telegram List')
    items_text = data.get('items', '')
    chat_id = str(data.get('chat_id'))
    count = database_read("SELECT COUNT(*) as total FROM lists WHERE chat_id = ?", (chat_id,))[0]["total"]
    list_name = list_name_bot
    if not items_text:
        return jsonify({"error": "No items provided"}), 400

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

    existing_list = database_read("SELECT id FROM lists WHERE archived = 0 and chat_id = ?", (chat_id,))
    if existing_list:
        list_id = existing_list[0]['id']
    else:
        database_write("INSERT INTO lists (name,chat_id) VALUES (?,?)", (list_name,chat_id))
        list_id = database_read("SELECT max(id) as id FROM lists WHERE chat_id = ?", (chat_id,))[0]['id']
        
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

        # Check if item already exists in the list
        existing = database_read("""
            SELECT id, quantity FROM product_in_list
            WHERE list_id = ? AND product_id = ?
        """, (list_id, product_id))

        if existing:
            # ✅ Item exists → update quantity
            existing_qty = existing[0]["quantity"]
            database_write("""
                UPDATE product_in_list
                SET quantity = ?
                WHERE id = ?
                and list_id = ?
            """, (existing_qty + quantity, existing[0]["id"],list_id))
        else:
            database_write("""
                INSERT INTO product_in_list (list_id, product_id, quantity, collected, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (list_id, product_id, quantity, 0, note))

    return jsonify({"status": "success", "list_id": list_id})

@app.route("/api/get_list/<int:list_id>", methods=["GET"])
def get_list(list_id):
    items = database_read("""
        SELECT p.name, pl.quantity, pl.notes, pl.collected
        FROM product_in_list pl
        JOIN products p ON p.id = pl.product_id
        WHERE pl.list_id = ?
    """, (list_id,))
    return jsonify({"items": items})

@app.route("/api/delete_list/<int:list_id>", methods=["DELETE"])
def delete_list(list_id):
    database_write("DELETE FROM product_in_list WHERE list_id = ?", (list_id,))
    database_write("DELETE FROM lists WHERE id = ?", (list_id,))
    return jsonify({"success": True})

#handel list chatid 
@app.route("/api/duplicate_list/<int:list_id>", methods=["POST"])
def duplicate_list(list_id):
    original = database_read("SELECT name FROM lists WHERE id = ?", (list_id,))
    if not original:
        return jsonify({"error": "Not found"}), 404     
       
    chat_id = database_read("SELECT chat_id FROM lists WHERE id = ?", (list_id,))[0]["chat_id"]
    new_name = original[0]['name'] + " (העתק)"
    database_write("INSERT INTO lists (name,chat_id) VALUES (?,?)", (new_name,chat_id))
    new_id = database_read("SELECT max(id) as id FROM lists")[0]['id']

    items = database_read("SELECT product_id, quantity, notes FROM product_in_list WHERE list_id = ?", (list_id,))
    for item in items:
        database_write(
            "INSERT INTO product_in_list (list_id, product_id, quantity, collected, notes) VALUES (?, ?, ?, 0, ?)",
            (new_id, item['product_id'], item['quantity'], item['notes'])
        )
    return jsonify({"new_id": new_id})

@app.route('/save_expense', methods=['POST'])
def save_expense():
    data = request.get_json()
    logger.info(f"save_expense called with:'{data}'  date: {str(datetime.now())}")
    try:
        amount = float(data.get('amount'))
        list_id = int(data.get('list_id'))
    except Exception as e:
        print("❌ Invalid input:", e)
        return jsonify({'status': 'error', 'message': 'Invalid input'}), 400

    list_row = database_read("SELECT chat_id, archived FROM lists WHERE id = ?", (list_id,))
    if not list_row:
        print("❌ List not found")
        return jsonify({'status': 'error', 'message': 'List not found'}), 404

    if list_row[0]['archived'] != 1:
        print("❌ List not archived")
        return jsonify({'status': 'error', 'message': 'List is not archived yet'}), 400

    chat_id = list_row[0]['chat_id']

    # Check if purchase already exists
    existing = database_read("SELECT 1 FROM purchases WHERE list_id = ?", (list_id,))
    if existing:
        print("⚠️ Purchase already exists for this list")
        return jsonify({'status': 'error', 'message': 'Already saved'}), 200

    ok = database_write("""
        INSERT INTO purchases (chat_id, list_id, total_amount)
        VALUES (?, ?, ?)
    """, (chat_id, list_id, amount))

    print("✅ Purchase saved:", ok)
    return jsonify({'status': 'success', 'list_id': list_id})

@app.route('/api/get_user_lang', methods=['GET'])
def get_user_lang_api():
    chat_id = request.args.get("chat_id")
    if not chat_id:
        return jsonify({"error": "Missing chat_id"}), 400
    lang = get_user_language(chat_id)
    return jsonify({"lang": lang or "en"})

@app.route('/api/set_user_lang', methods=['POST'])
def set_user_lang_api():
    data = request.get_json()
    chat_id = data.get("chat_id")
    lang = data.get("lang")
    if not chat_id or not lang:
        return jsonify({"error": "Missing chat_id or lang"}), 400
    save_user_language(chat_id, lang)
    return jsonify({"status": "ok"})
#EndRegion

def check_and_notify_list_completion(list_id):
    # Skip if already archived
    already = database_read("SELECT archived, chat_id FROM lists WHERE id = ?", (list_id,))
    if not already or already[0]['archived'] == 1:
        return
    chat_id = already[0]['chat_id']
    print("testcompleted 'check_and_notify_list_completion' for:",chat_id)

    items = database_read("SELECT collected FROM product_in_list WHERE list_id = ?", (list_id,))
    if items and all(item['collected'] for item in items):
        database_write(""" UPDATE lists SET archived = 1, name = name || ' (Archived)'
                        WHERE id = ? """, (list_id,))
        send_telegram_message(chat_id, key="list_completed", list_id=list_id)        





@app.route('/debug/db/<table>')
def debug_db_table(table):
    try:
        rows = database_read(f"SELECT * FROM {table}")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/test-vision", methods=["GET", "POST"])
def test_vision():
    if request.method == "GET":
        return '''
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="file" accept="image/*">
                <button type="submit">Upload</button>
            </form>'''

    if "file" not in request.files:
        return "Please upload a file.", 400

    file = request.files["file"]
    if file.filename == "" or not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        return "❌ Invalid file type.", 400

    raw_bytes = file.read()

    try:
        from ocr_utils_webapp import extract_text_from_image_bytes
        text = extract_text_from_image_bytes(raw_bytes)
        return f"<pre>{text}</pre>", 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception as e:
        return f"❌ ERROR: {e}", 500

@app.route("/debug-image/<name>")
def debug_image(name):
    path = f"/tmp/debug-{name}.jpg"
    if not os.path.exists(path):
        return f"{path} not found", 404

    return send_file(path, mimetype="image/jpeg")

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":     
    run_flask()



