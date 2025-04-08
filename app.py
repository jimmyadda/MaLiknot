import datetime
import sqlite3
import random
from flask import Flask, send_file,flash,render_template,request,redirect, send_from_directory, session, url_for
import flask_login
from flask import Flask, session, render_template, request, g
from grocery_list import create_db
from HandelDB import database_read,database_write,create_account
import uuid
import logging
import hashlib

app = Flask(__name__)
app.secret_key = "dsvnjksnvjksdvnsjkvnsjvsvs"
create_db()

#Logs
handler = logging.FileHandler('LogFile.log') # creates handler for the log file
app.logger.addHandler(handler) # Add it to the built-in logger
app.logger.setLevel(logging.DEBUG)         # Set the log level to debug
logger = app.logger

#Log in 
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

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
            productsdata = get_db()
            categories = get_categories()
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
            productsdata = get_db()
            categories = get_categories()
            return render_template('index.html', all_items=productsdata,categories=categories)
        
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
    
@app.route("/")
def index():
    if flask_login.current_user.is_authenticated:
        logger.info(str(flask_login.current_user.get_dict()) + "Has Logged in")

        data = database_read(f"select p.id,p.name,cat.name as catName from products p left JOIN categories cat on category_id = cat.id")
        print("items",data)
        categories =  database_read(f"select * from categories order by name;")
        return render_template('index.html',user=flask_login.current_user, all_items=data,categories=categories)
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
    cat_items = database_read(f"select p.id,p.name,cat.name as catName from products p left JOIN categories  cat on category_id = cat.id where cat.name ='{category_name}';")
    return render_template('category.html', cat=category_name,cat_items=cat_items)

@app.route('/product/<product_id>')
def product_disp(product_id):
    product = database_read(f"select p.*,cat.name as catName from products p left JOIN categories  cat on category_id = cat.id where p.id ='{product_id}';")
    return render_template('product.html', products=product) 


@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product = database_read(f"select p.*,cat.name as catName from products p left JOIN categories  cat on category_id = cat.id where p.id ='{product_id}';")

    if request.method == 'POST':
        form = dict(request.values)
        form['id'] = request.form['id']
        form['name'] = request.form['name']
        form['price'] = request.form['price']
        form['unit'] = request.form['unit']
        sql = "UPDATE products SET name =:name, price =:price, unit =:unit where id =:id"
        ok = database_write(sql,form)
        if ok == 1:
            product = database_read(f"select p.*,cat.name as catName from products p left JOIN categories  cat on category_id = cat.id where p.id ='{request.form['id']}';")
            return redirect(url_for('product_disp',product_id=request.form['id']))
    else:
        print("edit_product")
        return render_template('edit_product.html', products=product)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port = 80, debug=True)