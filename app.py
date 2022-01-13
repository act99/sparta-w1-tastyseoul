import random

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
####################### 렌더링 라우터 #####################

# 홈----------------------
@app.route('/')
def home():
    # 토큰을 먼저 가져옵니다.
    token_receive = request.cookies.get('mytoken')
    try:
        # jwt로 해쉬화 되어 있는 정보를 디코드시켜줍니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 유저 정보를 디코드
        user_info = db.users.find_one({"username": payload["id"]})
        # 코드 렌더링 시 jinja2 사용을 위해 user_info를 넘겨줌
        return render_template('index.html', user_info=user_info)
        # 토큰 만료시간이 다 되었을 때, 또는 로그인 한 사람이 아닐 때 로그인 창으로 넘어가게 함.
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

# 디테일----------------------
@app.route('/detail/<id>')
def detail(id):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        # 클릭한 맛집 정보를 가져온 후 그 맛집의 아이디 값을 가져와 db에서 찾아줌
        food_info = db.foodlist.find_one({'_id': ObjectId(id)})


        # 좋아요 눌렀는지 안 눌렀는지 확인 후 exists 메세지로 True False 보내줌.

        if str(food_info['_id']) in db.users.find_one({"username": payload['id']})['likelist']:
            exists = True
        else:
            exists = False

        print(food_info)
        # 맛집 정보를 jinja2사용을 위해 넘겨줌
        return render_template("detail.html", user_info=user_info, food=food_info, exists=exists)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

# 로그인 & 회원가입
@app.route('/login')
def login():
    # msg는 로그인 alert 메세지
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
        like_list = []
        like_id_list = user_info['likelist']
        for like_id in like_id_list:
            like_post = db.foodlist.find_one({"_id":ObjectId(like_id)}, {})
            if like_post is not None:
                like_list.append(like_post)
        print(like_list)
        return render_template('user.html', user_info=user_info, status=status, like_list=like_list)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))



# //////////////////////////////////////////////////////
####################### API 라우터 #####################


# 회원가입
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    profile_name_receive = request.form['profile_name_give']
    password_receive = request.form['password_give']
    # 패스워드 해쉬화 -> sha256으로 해쉬화 한 후 hexdigest로 보안 해시 & 압축
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": profile_name_receive,                           # 프로필 이름 기본값은 아이디
        'likelist': []
        # "profile_pic": "",                                          # 프로필 사진 파일 이름
        # "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        # "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


# 로그인
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인 인풋 데이터 불러옴
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    # 해쉬화 된 패스워드를 찾기 위해 잇풋 패스워드를 해쉬 인코드 시켜 찾아냄.
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
            # 토큰 만료시간 => 24시간
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)
        }
        # 토큰-> payload 값과 시크릿키를 합쳐 HS256 알고리즘으로 해쉬화한 후 decode (string값 변환) / PyJWT 2.0 이상부턴 decode 붙이면 안됨 (패치됨)
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})



# 중복확인
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    # 유저 아이디 잇풋 값을 db에서 찾은 후 존재하는지 안하는지 boolean 값으로 건네줌.
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


# 게시물 저장
@app.route('/postfood', methods=['POST'])
def save_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        location_receive = request.form['location_give']
        name_receive = request.form['name_give']
        comment_receive = request.form['comment_give']
        # 파일 리퀘스트를 받아 저장
        file = request.files["file_give"]
        # 파일 정리 코드
        extention = file.filename.split('.')[-1]
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
        filename = f'file-{mytime}'
        save_to = f'static/{filename}.{extention}'
        file.save(save_to)
        # 추후 좋아요 기능과 댓글 기능을 위해 미리 key값을 열어둠
        likes = 0
        comments = []
        doc = {
            "username": user_info["username"],
            "profile_name": user_info["profile_name"],
            'name': name_receive,
            'location': location_receive,
            'comment': comment_receive,
            'file': f'{filename}.{extention}',
            'likes': likes,
            'comments': comments
        }

        db.foodlist.insert_one(doc);

        return jsonify({'msg': '저장 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

# 게시물 보여주기
@app.route("/get_postfood", methods=['GET'])
def show_post():
    token_receive = request.cookies.get('mytoken')
    reviews = []
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # db의 모든 맛집 게시물 정보들을 가져옴
        results = list(db.foodlist.find({}, {}))
        # 좋아요 눌렀는지 안 눌렀는지 확인 후 exists 메세지로 True False 보내줌.
        for result in results:
            if str(result['_id']) in db.users.find_one({"username": payload['id']})['likelist']:
                exists = True
            else:
                exists = False
            _id = str(result['_id'])
            name = result['name']
            location = result['location']
            comment = result['comment']
            file = result['file']
            username = result['username']
            profile_name = result['profile_name']
            likes = result['likes']
            comments = result['comments']
            doc = {
                "_id": _id,
                "name": name,
                "location": location,
                "comment": comment,
                "file": file,
                "username": username,
                "profile_name": profile_name,
                'likes':likes,
                'comments':comments,
                'exists': exists
            }
            reviews.append(doc)
            # 최신버전 가져오기
            reviews.reverse()
        # 포스팅 목록 받아오기
        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", 'all_review':reviews})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 프로필 내 게시물 가져오기
@app.route("/get_mypost", methods=['GET'])
def get_mypost():
    username_receive = request.args['username_give']
    reviews = []
    try:
        # 내가 올린 맛집 정보를 가져옴
        foodlist = db.foodlist.find({'username':username_receive}, {})
        # db의 내 맛집 게시물 정보들을 가져옴
        for result in foodlist:
            _id = str(result['_id'])
            name = result['name']
            location = result['location']
            comment = result['comment']
            file = result['file']
            username = result['username']
            profile_name = result['profile_name']
            likes = result['likes']
            comments = result['comments']
            doc = {
                "_id": _id,
                "name": name,
                "location": location,
                "comment": comment,
                "file": file,
                "username": username,
                "profile_name": profile_name,
                'likes':likes,
                'comments':comments
            }
            reviews.append(doc)
            # 최신버전 가져오기
            reviews.reverse()
        # 포스팅 목록 받아오기
        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", 'all_review':reviews})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))



# 좋아요 기능 구현
@app.route("/update_like", methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        _id_receive = request.form["_id_give"]
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 여기부터는 유저db에 내가 좋아요를 눌렀는지 안눌렀는지 확인하고 그 값을 저장하는 코드
        user_info = db.users.find_one({"username": payload["id"]})
        username = user_info['username']
        # 만약 해당 유저의 db의 좋아요 리스트에 좋아요 버튼을 누른 게시물 아이디가 없다면
        if _id_receive not in db.users.find_one({'username':username})['likelist']:
            # 유저 좋아요 리스트에 해당 게시물 아이디값 추가
            db.users.update_one({'username': username}, {'$push': {'likelist': _id_receive}})
            # 해당 게시물의 좋아요 수를 찾아냄
            likes = db.foodlist.find_one({'_id': ObjectId(_id_receive)}, {})['likes']
            # 해당 게시물의 좋아요 수 + 1 시켜줌
            db.foodlist.update_one({'_id': ObjectId(_id_receive)}, {'$set': {'likes': likes + 1}})
            return jsonify({"result": "success", "msg": "좋아요!"})
        else:
            # 만약 해당 유저의 db 좋아요 리스트에 버튼을 누른 게시물 아이디가 있다면 유저db 좋아요리스트 해당 id 삭제
            db.users.update_one({'username': username}, {'$pull': {'likelist': _id_receive}})
            likes = db.foodlist.find_one({'_id': ObjectId(_id_receive)}, {})['likes']
            # 게시물 좋아요 - 1
            db.foodlist.update_one({'_id': ObjectId(_id_receive)}, {'$set': {'likes': likes - 1}})
            return jsonify({"result": "success", "msg": "좋아요 취소!"})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


#


#코멘트
@app.route('/comment', methods=['POST'])
def commenting():
        token_receive = request.cookies.get('mytoken')
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        posting_id_receive = request.form['posting_id_give']
        comment_receive = request.form["comment_give"]
        # 댓글
        user_info = db.users.find_one({"username": payload["id"]})
        doc = {
            'username':user_info['username'],
            'comment':comment_receive,
            # id 값을 랜덤을 만들어 저장시킴
            '_id':random.randint(1,10000)
        }
        db.foodlist.update_one({"_id":ObjectId(posting_id_receive)}, {'$push': {'comments':doc}})

        # doc = {
        #     "username": user_info["username"],
        #     "comment": comment_receive,
        #     "posting_id": posting_id_receive
        # }
        # db.comments.insert_one(doc)
        return jsonify({"result": "success", 'msg': '댓글 저장'})


#삭제부분입니다. 여기 수정
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
        db.comments.delete_one({"comment":comment_receive}, {})
        return jsonify({"result": "success", 'msg': '댓글 삭제 완료'})

    # db.comments.delete_one({}, {'username': False})


@app.route("/postfood/delete", methods=['POST'])
def post_delete():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    _id_receive = request.form["_id_give"]
    writer_receive = request.form["writer_give"]
    writer = db.foodlist.find_one({"_id":ObjectId(_id_receive), "username":writer_receive}, {})['username']
    if writer == payload['id']:
        db.foodlist.delete_one({"_id":ObjectId(_id_receive)}, {})
        return jsonify({"result": "success", 'msg': '글 삭제 완료'})
    else:
        return jsonify({"result": "failed", 'msg': '본인 글이 아니라 삭제가 불가능합니다.'})
    



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)