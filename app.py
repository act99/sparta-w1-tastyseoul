import datetime
import hashlib

import bson
import jwt
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://test:test@localhost', 27017)
db = client.tastyseoul

SECRET_KEY = '6조비밀키'

## HTML을 주는 부분
@app.route('/')
def home():
   return render_template('index.html')

@app.route('/register')
def register():
   return render_template('register.html')

@app.route('/login')
def login():
   return render_template('login.html')


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


@app.route('/api/login', methods=['POST'])
def api_login():
    email_receive = request.form['email_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    result = db.users.find_one({'email':email_receive, 'password':pw_hash})

    if result is not None:

        payload = {
            'email':email_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})




# @app.route('/memo', methods=['GET'])
# def listing():
#     article_array = []
#     articles = list(db.articles.find({}, {}))
#     print(articles)
#     for article in articles:
#       id = str(article['_id'])
#       title = article['title']
#       image = article['image']
#       desc = article['desc']
#       url = article['url']
#       comment = article['comment']
#       doc = {
#          "id": id,
#          "title": title,
#          "image": image,
#          "desc": desc,
#          "url": url,
#          "comment": comment
#       }
#       article_array.append(doc)
#     return jsonify({"all_articles":article_array})



# ## API 역할을 하는 부분
# @app.route('/memo', methods=['POST'])
# def saving():
#     url_receive = request.form['url_give']
#     comment_receive = request.form['comment_give']

#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
#     data = requests.get(url_receive, headers=headers)

#     soup = BeautifulSoup(data.text, 'html.parser')

#     # 여기에 코딩을 해서 meta tag를 먼저 가져와보겠습니다.
#     title = soup.select_one('meta[property="og:title"]')["content"]
#     image = soup.select_one('meta[property="og:image"]')["content"]
#     desc = soup.select_one('meta[property="og:description"]')["content"]

#     doc = {
#         "title":title,
#         "image":image,
#         "desc":desc,
#         "url":url_receive,
#         "comment":comment_receive
#     }
#     db.articles.insert_one(doc)

#     return jsonify({'msg':'저장이 완료되었습니다.'})

# @app.route('/memo/delete', methods=['POST'])
# def delete():
#    id_receive = request.form['id_give']
#    set_id = ObjectId(id_receive)
#    db.articles.delete_one({'_id': set_id})

#    return jsonify({'msg': '삭제 완료!'})


if __name__ == '__main__':
   app.run('0.0.0.0',port=5000,debug=True)