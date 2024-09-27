from flask import Blueprint, request, jsonify
from .models import User, db, Review, Spot
from . import bcrypt
from flask_jwt_extended import create_access_token

api = Blueprint('api', __name__)


# ユーザー登録エンドポイント
@api.route('/register', methods=['POST'])
def register():
    print('ok')
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    # ユーザーが既に存在するか確認
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'ユーザーは既に存在します'}), 400

    # 新しいユーザーを作成
    new_user = User(name=name, email=email)
    new_user.password = password
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'ユーザー登録に成功しました'}), 201

# ログインエンドポイント
@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # ユーザーを検索
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'メールアドレスまたはパスワードが間違っています'}), 401

    # JWTトークンを作成
    access_token = create_access_token(identity={'email': user.email, 'name': user.name})
    return jsonify({'access_token': access_token}), 200


from datetime import datetime

#口コミ追加
"""
入力
user_id
spot_id
text
出力
なし
"""
@api.route('/add_review', methods=['POST'])
def add_review():
    data = request.get_json()
    user_id=data.get('user_id')
    spot_id=data.get('spot_id')
    text=data.get('text')
    current_time = datetime.now()

    # 新しい口コミを作成
    new_review = Review(user_id=user_id, spot_id=spot_id, text=text, date=current_time)
    
    db.session.add(new_review)
    db.session.commit()
    

    

    return jsonify({'status': 'success'})

#口コミ通報
"""
入力
review_id ... 口コミのid
出力
なし
"""
@api.route('/report_review', methods=['POST'])
def report_review():
    data = request.get_json()
    review_id = data.get('id')
    #Flagを立てる
    test = db.session.query(Review).filter(Review.id==review_id).first()
    test.report = True
    db.session.commit()
    

    return jsonify({'status': 'success'})

# 建物の詳細ページを表示
"""
入力
spot_id

出力
spot_id
name
description ... spotの紹介文
address
phpto_url
staying_time
review_list = [{
review_id
date
review_text
}*口コミの個数分]
"""
@api.route('/tourist_spots/<int:spot_id>', methods=['POST'])
def building_detail(spot_id):
    data = request.get_json()
    spot_id_ = data.get('spot_id')


    # 建物の紹介文と住所を取得
    spot_data = db.session.query(Spot).filter(Spot.id==spot_id_).first()
    # 口コミ情報を取得
    revew_data_all = db.session.query(Review).filter(Review.spot_id==spot_id_)

    review_list = [
        {
            'review_id': revew_data.id,
            'user_id': revew_data.user_id,
            'date': revew_data.date,
            'text': revew_data.text,
            'report': revew_data.report,
            'confirmation': revew_data.confirmation
    }
    for revew_data in revew_data_all
    ]
    # # JWTトークンを作成
    access_token = create_access_token(identity={ 'spot_id':spot_data.id,  'name': spot_data.spot_name, 'description': spot_data.text, 'address': spot_data.address, 'photo_url': spot_data.image, 'staying_time':spot_data.staying_time, 'reviews': review_list})
    return jsonify({'access_token': access_token}), 200
    # ↓テスト用
    # return jsonify({ 'spot_id':spot_data.id,  'name': spot_data.spot_name, 'description': spot_data.text, 'address': spot_data.address, 'photo_url': spot_data.image, 'staying_time':spot_data.staying_time, 'review_list': review_list}), 200

@api.route('/test', methods=['POST'])
def test():
    return jsonify({'status': 'success'})