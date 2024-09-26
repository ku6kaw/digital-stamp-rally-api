from flask import Blueprint, request, jsonify
from .models import User, db, Spot, Stamp, StampDetail
from . import bcrypt
from flask_jwt_extended import create_access_token
from .GenerateRoute.dummy_data import DummyData

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


#　経路生成エンドポイント
@api.route('/generate-route', methods=['POST'])
def generate_route():
    data = request.get_json()
    print(data)
    return jsonify({'route': [1]}), 200


@api.route('/dummy_get', methods=['GET'])
def dummy_get():
    spots = Spot.query.all()
    spot_list = []
    for spot in spots:
        spot_list.append({
            'id': spot.id,
            'spot_name': spot.spot_name,
            'coordinate': spot.coordinate,
            'staying_time': spot.staying_time,
            'recommendation': spot.recommendation,
            'spot_type': spot.spot_type
        })
    return jsonify({'spot_list': spot_list}), 200

# dummyデータをデータベースに登録する
@api.route('/dummy_insert', methods=['GET'])
def dummy_insert():
    for item in DummyData:
        spot = Spot(
            spot_name=item['spot_name'],
            coordinate=str(item['coordinate']),  # 配列を文字列に変換
            staying_time=item['staying_time'],
            recommendation=item['recommendation'],
            spot_type=item['spot_type']
        )
        db.session.add(spot)  # Spotオブジェクトをセッションに追加
    
    db.session.commit()  # データベースに変更をコミット
    return jsonify({"message": "Data inserted successfully!"}), 201