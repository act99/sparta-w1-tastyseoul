import datetime
import hashlib

import bson
import jwt
from flask import Flask, render_template, jsonify, request, redirect, url_for

app = Flask(__name__)
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://test:test@localhost', 27017)
db = client.tastyseoul

SECRET_KEY = '6조비밀키'


@app.route('/register')
def register():
   return render_template('register.html')


@app.route('/api/register', methods=['POST'])
def api_register():
    email_receive = request.form['email_give']
    password_receive = request.form['password_give']
    nick_receive = request.form['nick_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    doc = {
        "email":email_receive,
        "password":pw_hash,
        "nick":nick_receive,
    }
    db.users.insert_one(doc)

    return jsonify({'msg':'저장이 완료되었습니다.'})