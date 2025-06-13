from flask import Flask, request, jsonify
from pymongo import MongoClient
import bcrypt
from flask_cors import CORS

from flask_restx import Api, Resource

app = Flask(__name__)
CORS(app)  # CORS 허용

# Swagger 설정
api = Api(app, version='1.0', title='Travel API',
          description='A simple API for travel destinations and reviews')

# 리소스 정의: API 엔드포인트에 해당
ns = api.namespace('Reviews', description='Operations related to reviews')

# MongoDB 연결
client = MongoClient("mongodb://localhost:27017/")
db = client["trabledb"]
user_col = db["users"]
dest_col = db["destinations"]  # 여행지 정보를 위한 컬렉션
review_col = db["reviews"]  # 리뷰 정보를 위한 컬렉션

initial_destinations = [
    {"name": "경복궁", "description": "한국의 대표적인 전통 궁궐", "type": "문화, 도시"},
    {"name": "제주도", "description": "자연과 바다가 아름다운 섬", "type": "섬, 인기, 해변, 자연"},
    {"name": "부산 해운대", "description": "한국에서 가장 유명한 해변 중 하나", "type": "인기, 해변"},
    {"name": "남산타워", "description": "서울 전망을 볼 수 있는 타워", "type": "인기, 자연"},
    {"name": "부산 광안리", "description": "야경이 멋진 부산의 해변", "type": "인기, 해변"},
    {"name": "속초", "description": "동해와 산의 조화", "type": "인기, 도시, 해변"},
    {"name": "강릉", "description": "바다와 커피 거리로 유명한 도시", "type": "인기, 도시"},
    {"name": "경주", "description": "역사적인 유적이 많은 도시", "type": "인기, 도시"},
    {"name": "전주한옥마을", "description": "전통과 현대가 공존하는 공간", "type": "인기, 문화"},
    {"name": "담양", "description": "죽녹원으로 유명한 대나무숲", "type": "자연"},
    {"name": "춘천 남이섬", "description": "데이트 명소로 유명한 섬", "type": "인기, 섬, 자연, 문화"},
    {"name": "여수", "description": "밤바다와 케이블카로 유명", "type": "인기, 도시, 해변"},
    {"name": "인사동", "description": "전통 공예와 갤러리의 거리", "type": "도시, 문화"},
    {"name": "서촌", "description": "한적한 골목 문화거리", "type": "도시, 문화"},
    {"name": "하동", "description": "녹차밭과 자연풍경", "type": "자연"},
    {"name": "울릉도", "description": "자연이 살아있는 섬", "type": "섬, 자연"},
    {"name": "대구 근대골목", "description": "역사 문화 체험 골목", "type": "도시, 문화"},
    {"name": "통영", "description": "예쁜 바닷가 마을", "type": "해변"},
    {"name": "포항 호미곶", "description": "해돋이 명소", "type": "해변"},
    {"name": "양양 서피비치", "description": "서핑하기 좋은 해변", "type": "인기, 해변"}
]

@app.route('/', methods=['POST']) # 홈페이지 방문
def init_destinations():
    dest_col.delete_many({})  # 기존 데이터 제거 (원하면)
    dest_col.insert_many(initial_destinations)
    return jsonify({"message": "20개 여행지 초기화 완료"}), 201


############################################################################### user관련 
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
@app.route('/api/user/update', methods=['PUT'])
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

# 회원 탈퇴
@app.route('/api/user/delete', methods=['DELETE'])
def delete_user():
    data = request.json
    user_id = data.get('user_id')  # 탈퇴하려는 사용자의 _id

    # 필수 입력 확인
    if not user_id:
        return jsonify({'message': '사용자의 고유 ID를 입력해주세요.'}), 400

    # 사용자 조회 (_id로 찾기)
    user_data = user_col.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        return jsonify({'message': '사용자를 찾을 수 없습니다.'}), 404

    # 사용자 정보 삭제
    user_col.delete_one({"_id": ObjectId(user_id)})

    return jsonify({'message': '회원 탈퇴가 완료되었습니다.'}), 200




################################################################################# 여행지 관련

# 여행지 추가
@app.route('/api/destinations/create', methods=['POST'])
def create_destination():
    data = request.json
    name = data.get('name')           # 여행지 이름
    description = data.get('description')  # 여행지 설명

    # 필수 입력 확인
    if not name or not description:
        return jsonify({'message': '여행지 이름과 설명을 입력해주세요.'}), 400

    # 여행지 정보 DB 저장
    dest_col.insert_one({
        "name": name,
        "description": description
    })

    return jsonify({'message': '여행지 정보가 추가되었습니다.'}), 201

# 여행지 정보 수정
@app.route('/api/destinations/update/<string:dest_id>', methods=['PUT'])
def update_destination(dest_id):
    data = request.json
    new_name = data.get('name')           # 수정할 여행지 이름
    new_description = data.get('description')  # 수정할 여행지 설명

    # 필수 입력 확인
    if not new_name or not new_description:
        return jsonify({'message': '여행지 이름과 설명을 입력해주세요.'}), 400

    # 여행지 정보 수정
    #dest_col = db["destinations"]
    result = dest_col.update_one(
        {"_id": ObjectId(dest_id)},  # 여행지의 _id로 찾기
        {"$set": {"name": new_name, "description": new_description}}  # 업데이트할 필드
    )

    if result.matched_count == 0:
        return jsonify({'message': '여행지를 찾을 수 없습니다.'}), 404

    return jsonify({'message': '여행지 정보가 수정되었습니다.'}), 200

# 여행지 삭제
@app.route('/api/destinations/delete/<string:dest_id>', methods=['DELETE'])
def delete_destination(dest_id):
    # 여행지 삭제
    dest_col = db["destinations"]
    result = dest_col.delete_one({"_id": ObjectId(dest_id)})  # _id로 여행지 삭제

    if result.deleted_count == 0:
        return jsonify({'message': '여행지를 찾을 수 없습니다.'}), 404

    return jsonify({'message': '여행지 정보가 삭제되었습니다.'}), 200

# 여행지 목록 조회
@app.route('/api/destinations/list', methods=['GET'])
def get_destinations():
    # 여행지 목록 가져오기
    dest_col = db["destinations"]
    destinations = list(dest_col.find())  # 모든 여행지 데이터를 리스트로 변환

    # ObjectId를 문자열로 변환
    for dest in destinations:
        dest['_id'] = str(dest['_id'])

    return jsonify(destinations), 200

# 여행지 상세 조회
@app.route('/api/destinations/<string:dest_id>', methods=['GET'])
def get_destination(dest_id):
    # 여행지 정보 조회 (_id로 찾기)
    dest_col = db["destinations"]
    destination = dest_col.find_one({"_id": ObjectId(dest_id)})  # _id로 여행지 찾기

    if not destination:
        return jsonify({'message': '여행지를 찾을 수 없습니다.'}), 404

    # ObjectId를 문자열로 변환
    destination['_id'] = str(destination['_id'])

    return jsonify(destination), 200

@app.route('/api/destinations', methods=['GET'])
def get_destinations_by_type():
    category = request.args.get('type')  # 예: '인기', '도시', '자연' 등

    if not category:
        return jsonify({'message': '카테고리(type)를 지정해주세요.'}), 400

    # type 필드에 해당 키워드가 포함된 항목만 필터링 (정규표현식 사용)
    matched = list(dest_col.find({"type": {"$regex": category}}))

    for d in matched:
        d['_id'] = str(d['_id'])

    return jsonify(matched), 200



#################################################################################### 리뷰 관련

# 리뷰 생성
@app.route('/api/reviews/create', methods=['POST'])
def create_review():
    data = request.json
    user_id = data.get('user_id')  # 유저 ID
    dest_id = data.get('dest_id')  # 여행지 ID
    content = data.get('content')  # 리뷰 내용

    # 필수 입력 확인
    if not all([user_id, dest_id, content]):
        return jsonify({'message': '유저 ID, 여행지 ID, 내용은 필수 항목입니다.'}), 400

    # 리뷰 데이터 DB에 저장
    review_col.insert_one({
        "user_id": ObjectId(user_id),
        "dest_id": ObjectId(dest_id),
        "content": content
    })

    return jsonify({'message': '리뷰가 성공적으로 작성되었습니다.'}), 201

# 리뷰 수정
@app.route('/api/reviews/<string:review_id>', methods=['PUT'])
def update_review(review_id):
    data = request.json
    new_content = data.get('content')  # 수정할 리뷰 내용

    # 필수 입력 확인
    if not new_content:
        return jsonify({'message': '리뷰 내용을 입력해주세요.'}), 400

    # 리뷰 정보 조회 (_id로 찾기)
    #review_col = db["reviews"]
    review = review_col.find_one({"_id": ObjectId(review_id)})  # _id로 리뷰 찾기

    if not review:
        return jsonify({'message': '리뷰를 찾을 수 없습니다.'}), 404

    # 리뷰 내용 수정
    review_col.update_one(
        {"_id": ObjectId(review_id)},  # _id로 해당 리뷰 찾기
        {"$set": {"content": new_content}}  # 새로운 내용으로 업데이트
    )

    return jsonify({'message': '리뷰가 수정되었습니다.'}), 200

# 특정 리뷰 상세 조회
@app.route('/api/reviews/<string:review_id>', methods=['GET'])
def get_review_by_id(review_id):
    # 리뷰 ID로 리뷰 정보 조회
    review_col = db["reviews"]
    review = review_col.find_one({"_id": ObjectId(review_id)})  # _id로 리뷰 찾기

    if not review:
        return jsonify({'message': '리뷰를 찾을 수 없습니다.'}), 404

    # _id를 문자열로 변환
    review['_id'] = str(review['_id'])
    review['user_id'] = str(review['user_id'])
    review['dest_id'] = str(review['dest_id'])

    return jsonify(review), 200

# 리뷰 삭제
@app.route('/api/reviews/<string:review_id>', methods=['DELETE'])
def delete_review(review_id):
    # 리뷰 정보 삭제
    review_col = db["reviews"]
    result = review_col.delete_one({"_id": ObjectId(review_id)})  # _id로 리뷰 삭제

    if result.deleted_count == 0:
        return jsonify({'message': '리뷰를 찾을 수 없습니다.'}), 404

    return jsonify({'message': '리뷰가 삭제되었습니다.'}), 200


# 여행지별 리뷰 목록 조회
@app.route('/api/reviews/destination/<string:dest_id>', methods=['GET'])
def get_reviews_by_dest(dest_id):
    # 여행지 ID로 리뷰들 조회
    review_col = db["reviews"]
    reviews = list(review_col.find({"dest_id": ObjectId(dest_id)}))  # 여행지 ID로 필터링

    # 리뷰가 없을 경우
    if not reviews:
        return jsonify({'message': '이 여행지에 대한 리뷰가 없습니다.'}), 404

    # 리뷰 데이터의 _id를 문자열로 변환
    for review in reviews:
        review['_id'] = str(review['_id'])
        review['user_id'] = str(review['user_id'])
        review['dest_id'] = str(review['dest_id'])

    return jsonify(reviews), 200

# 유저가 작성한 리뷰 조회
@app.route('/api/reviews/user/<string:user_id>', methods=['GET'])
def get_reviews_by_user(user_id):
    # 유저 ID로 리뷰들 조회
    review_col = db["reviews"]
    reviews = list(review_col.find({"user_id": ObjectId(user_id)}))  # 유저 ID로 필터링

    # 리뷰가 없을 경우
    if not reviews:
        return jsonify({'message': '이 유저가 작성한 리뷰가 없습니다.'}), 404

    # 리뷰 데이터의 _id, user_id, dest_id를 문자열로 변환
    for review in reviews:
        review['_id'] = str(review['_id'])
        review['user_id'] = str(review['user_id'])
        review['dest_id'] = str(review['dest_id'])

    return jsonify(reviews), 200












if __name__ == '__main__':
    app.run(debug=True)

