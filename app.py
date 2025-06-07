from flask import Flask, request, jsonify
from pymongo import MongoClient
import bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # CORS 허용

# MongoDB 연결
client = MongoClient("mongodb://localhost:27017/")
db = client["userdb"]
user_col = db["users"]

############################################################ user관련 
# 회원가입
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    phone = data.get('phone')

    # 필수 입력 확인
    if not all([email, password, name, phone]):
        return jsonify({'message': '모든 필드를 입력해주세요.'}), 400

    # 중복 체크
    if user_col.find_one({"email": email}):
        return jsonify({'message': '이미 존재하는 이메일입니다.'}), 409

    # 비밀번호 해싱
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # DB 저장
    user_col.insert_one({
        "email": email,
        "password": hashed_pw,
        "name": name,
        "phone": phone
    })

    return jsonify({'message': '회원가입 성공'}), 201

# 로그인
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # 필수 입력 확인
    if not email or not password:
        return jsonify({'message': '이메일과 비밀번호를 입력해주세요.'}), 400

    # 사용자 조회
    user_data = user_col.find_one({"email": email})
    if not user_data:
        return jsonify({'message': '사용자를 찾을 수 없습니다.'}), 404

    # 비밀번호 확인
    if not bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
        return jsonify({'message': '비밀번호가 일치하지 않습니다.'}), 401

    return jsonify({'message': '로그인 성공', 'user': {
        "email": user_data['email'],
        "name": user_data['name']
    }}), 200

from bson.objectid import ObjectId  # ObjectId를 사용하여 _id로 찾기

# 회원 정보 수정
@app.route('/api/update', methods=['PUT'])
def update_user():
    data = request.json
    user_id = data.get('user_id')  # 유저의 고유 _id
    new_email = data.get('email')  # 이메일 수정 가능하도록 추가
    new_password = data.get('password')
    new_name = data.get('name')
    new_phone = data.get('phone')

    # 필수 입력 확인
    if not all([user_id, new_password, new_name, new_phone]):
        return jsonify({'message': '모든 필드를 입력해주세요.'}), 400

    # 사용자 조회 (_id로 찾기)
    user_data = user_col.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        return jsonify({'message': '사용자를 찾을 수 없습니다.'}), 404
    
    # 중복 체크
    if user_col.find_one({"email": new_email}):
        return jsonify({'message': '이미 존재하는 이메일입니다.'}), 409

    # 비밀번호 해싱
    hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    # 업데이트할 데이터 (이메일도 수정 가능하게 추가)
    updated_data = {
        "email": new_email,
        "password": hashed_pw,
        "name": new_name,
        "phone": new_phone
    }

    # 사용자 정보 업데이트
    user_col.update_one({"_id": ObjectId(user_id)}, {"$set": updated_data})

    return jsonify({'message': '회원정보가 수정되었습니다.'}), 200



############################################################## 여행지 관련









if __name__ == '__main__':
    app.run(debug=True)

