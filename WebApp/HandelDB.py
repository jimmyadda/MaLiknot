import sqlite3
from flask import Flask, session, render_template, request, g
import hashlib
import uuid
import getpass
import json

from config import DATABASE_PATH

database_filename = connection = DATABASE_PATH


# Set this once during app startup
def enable_wal_mode():
    with sqlite3.connect(database_filename, timeout=10) as conn:
        conn.execute("PRAGMA journal_mode=WAL")

def database_write(sql, data=None):
    with sqlite3.connect(database_filename, timeout=10) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        if data:
            result = cursor.execute(sql, data)
        else:
            result = cursor.execute(sql)

        connection.commit()
        return result.rowcount
    

def database_read(sql, data=None):
    with sqlite3.connect(database_filename, timeout=10) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        if data:
            cursor.execute(sql, data)
        else:
            cursor.execute(sql)

        records = cursor.fetchall()
        return [dict(record) for record in records]

def create_account(userpassed):
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
