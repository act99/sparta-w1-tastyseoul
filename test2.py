import datetime
import hashlib
import register
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