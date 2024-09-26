from flask import Blueprint, request, jsonify
from .models import User, db
from . import bcrypt
from flask_jwt_extended import create_access_token

api = Blueprint('api', __name__)

# ユーザー登録エンドポイント
@api.route('/register', methods=['POST'])
def register():
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
