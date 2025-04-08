import sqlite3
from flask import Flask, session, render_template, request, g
import hashlib
import uuid
import getpass
import json

database_filename = 'grocery_list.db'


def database_write(sql,data=None):
    connection = sqlite3.connect(database_filename)
    connection.row_factory = sqlite3.Row
    db = connection.cursor()
    row_affected = 0
    if data:
        row_affected = db.execute(sql, data).rowcount
    else:
        row_affected = db.execute(sql).rowcount
    connection.commit()
    db.close()
    connection.close()

    return row_affected

def database_read(sql,data=None):
    connection = sqlite3.connect(database_filename)
    connection.row_factory = sqlite3.Row
    db = connection.cursor()

    if data:
         db.execute(sql, data)
    else:
         db.execute(sql)
    records = db.fetchall()    
    rows = [dict(record) for record in records]
    db.close()
    connection.close()
    return rows

def create_account(userpassed):
    print(userpassed)
    userid = userpassed['userid'] #input("userid: ")
    email = userpassed['email'] #input("email: ")
    name = userpassed['name'] #input("name: ")
    password = userpassed['password'] #getpass.getpass("password: ")
    
    salt = str(uuid.uuid1())
    key = hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt.encode('utf-8'),10000).hex()
    sql = f"Insert into accounts (userid,salt,password,email,name) Values (:userid,:salt,:password,:email,:name);"
    record ={
      "userid": userid,
      "salt": salt,
      "password": key,
      "email": email,
      "name": name
    }
    ok = database_write(sql,record)
    return ok
