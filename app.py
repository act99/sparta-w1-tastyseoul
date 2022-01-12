from bson import ObjectId
from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'
# client = MongoClient('mongodb://test:test@localhost', 27017)
client = MongoClient('localhost', 27017)
db = client.groupsix


# //////////////////////////////////////////////////////
# Front 라우터

# 홈
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        print("이거 체크")
        print(user_info)
        return render_template('index.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


# 디테일
@app.route('/detail/<id>')
def detail(id):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        food_info = db.foodlist.find_one({'_id': ObjectId(id)})
        print(food_info)
        return render_template("detail.html", user_info=user_info, food=food_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


# 로그인 & 회원가입
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


# 프로필
@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# //////////////////////////////////////////////////////
# API
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    profile_name_receive = request.form['profile_name_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": profile_name_receive,  # 프로필 이름 기본값은 아이디
        'likelist': []
        # "profile_pic": "",                                          # 프로필 사진 파일 이름
        # "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        # "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


#
# @app.route('/update_profile', methods=['POST'])
# def save_img():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 프로필 업데이트
#         return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))
#

# @app.route('/posting', methods=['POST'])
# def posting():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         user_info = db.users.find_one({"username": payload["id"]})
#         comment_receive = request.form["comment_give"]
#         date_receive = request.form["date_give"]
#         doc = {
#             "username": user_info["username"],
#             "profile_name": user_info["profile_name"],
#             "profile_pic_real": user_info["profile_pic_real"],
#             "comment": comment_receive,
#             "date": date_receive
#         }
#         db.posts.insert_one(doc)
#         return jsonify({"result": "success", 'msg': '포스팅 성공'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


# @app.route("/get_posts", methods=['GET'])
# def get_posts():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#
#         # 포스팅 목록 받아오기
#         return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다."})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


# @app.route('/update_like', methods=['POST'])
# def update_like():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 좋아요 수 변경
#         user_info = db.users.find_one({"username": payload["id"]})
#         post_id_receive = request.form["post_id_give"]
#         type_receive = request.form["type_give"]
#         action_receive = request.form["action_give"]
#         doc = {
#             "post_id": post_id_receive,
#             "username": user_info["username"],
#             "type": type_receive
#         }
#         if action_receive == "like":
#             db.likes.insert_one(doc)
#         else:
#             db.likes.delete_one(doc)
#         count = db.likes.count_documents({"post_id": post_id_receive, "type": type_receive})
#         return jsonify({"result": "success", 'msg': 'updated', "count": count})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


@app.route('/postfood', methods=['POST'])
def save_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        location_receive = request.form['location_give']
        name_receive = request.form['name_give']
        comment_receive = request.form['comment_give']
        file = request.files["file_give"]
        extention = file.filename.split('.')[-1]
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
        filename = f'file-{mytime}'
        save_to = f'static/{filename}.{extention}'
        file.save(save_to)
        likes = 0
        doc = {
            "username": user_info["username"],
            "profile_name": user_info["profile_name"],
            'name': name_receive,
            'location': location_receive,
            'comment': comment_receive,
            'file': f'{filename}.{extention}',
            'likes': likes
        }

        db.foodlist.insert_one(doc);

        return jsonify({'msg': '저장 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/get_postfood", methods=['GET'])
def show_post():
    token_receive = request.cookies.get('mytoken')
    reviews = []
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        results = list(db.foodlist.find({}, {}))
        for result in results:
            _id = str(result['_id'])
            name = result['name']
            location = result['location']
            comment = result['comment']
            file = result['file']
            username = result['username']
            profile_name = result['profile_name']
            likes = result['likes']
            doc = {
                "_id": _id,
                "name": name,
                "location": location,
                "comment": comment,
                "file": file,
                "username": username,
                "profile_name": profile_name,
                'likes': likes
            }
            reviews.append(doc)
        # 포스팅 목록 받아오기
        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", 'all_review': reviews})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 좋아요 기능 구현
@app.route("/update_like", methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        _id_receive = request.form["_id_give"]
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 여기는 유저db에 내가 좋아요를 눌렀는지 안눌렀는지 확인하고 그 값을 저장하는 코드
        user_info = db.users.find_one({"username": payload["id"]})
        username = user_info['username']
        if _id_receive not in db.users.find_one({'username': username})['likelist']:
            db.users.update_one({'username': username}, {'$push': {'likelist': _id_receive}})
            likes = db.foodlist.find_one({'_id': ObjectId(_id_receive)}, {})['likes']
            db.foodlist.update_one({'_id': ObjectId(_id_receive)}, {'$set': {'likes': likes + 1}})
            return jsonify({"result": "success", "msg": "좋아요!"})
        else:
            db.users.update_one({'username': username}, {'$pull': {'likelist': _id_receive}})
            likes = db.foodlist.find_one({'_id': ObjectId(_id_receive)}, {})['likes']
            db.foodlist.update_one({'_id': ObjectId(_id_receive)}, {'$set': {'likes': likes - 1}})
            return jsonify({"result": "success", "msg": "좋아요 취소!"})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 코멘트
@app.route('/comment', methods=['POST'])
def commenting():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    # 댓글
    user_info = db.users.find_one({"username": payload["id"]})
    comment_receive = request.form["comment_give"]

    doc = {
        "username": user_info["username"],
        "comment": comment_receive,
    }
    db.comments.insert_one(doc)
    return jsonify({"result": "success", 'msg': '댓글 저장'})


# 코멘트 보여주는 부분입니다.
@app.route("/get_comment", methods=['GET'])
def comment_show():
    reviews = []
    results = list(db.comments.find({}, {}))
    for result in results:
        _id = str(result['_id'])
        username = result['username']
        comment = result['comment']

        doc = {
            "_id": _id,
            "username": username,
            "comment": comment

        }
        reviews.append(doc)
    return jsonify({'all_review': reviews})


# 삭제부분입니다. 여기 수정
@app.route("/comment/delete", methods=['POST'])
def comment_delete():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    comment_receive = request.form["comment_give"]
    comment = db.comments.find_one({"comment": comment_receive}, {})
    username = payload["id"]
    if username != comment['username']:
        return jsonify({"result": "failed", 'msg': '댓글 삭제 실패 / 본인의 글이 아닙니다.'})
    else:
        db.comments.delete_one({"comment": comment_receive}, {})
        return jsonify({"result": "success", 'msg': '댓글 삭제 완료'})

    # db.comments.delete_one({}, {'username': False})


@app.route("/postfood/delete", methods=['POST'])
def post_delete():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    _id_receive = request.form["_id_give"]
    writer_receive = request.form["writer_give"]
    writer = db.foodlist.find_one({"_id": ObjectId(_id_receive), "username": writer_receive}, {})['username']
    if writer == payload['id']:
        db.foodlist.delete_one({"_id": ObjectId(_id_receive)}, {})
        return jsonify({"result": "success", 'msg': '글 삭제 완료'})
    else:
        return jsonify({"result": "failed", 'msg': '본인 글이 아니라 삭제가 불가능합니다.'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)