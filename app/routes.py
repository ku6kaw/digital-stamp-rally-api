from flask import Blueprint, request, jsonify, send_file
from .models import User, StampDetail, db
from . import bcrypt
from flask_jwt_extended import create_access_token, jwt_required
from io import BytesIO
import qrcode

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


# QRコードで読み取った観光地IDを基に、スタンプの状態を更新するAPI
@api.route('/update-stamp', methods=['POST'])
def update_stamp():
    data = request.get_json()
    user_id = data.get('userId')
    spot_id = data.get('spotId')

    # スタンプ詳細を検索して更新
    stamp_detail = StampDetail.query.filter_by(stamp_id=user_id, spot_id=spot_id).first()
    if stamp_detail:
        stamp_detail.status = 1  # 状態を実施済みに更新
        db.session.commit()
        return jsonify({'message': 'スタンプが更新されました'}), 200
    else:
        return jsonify({'message': 'QRコードが無効です'}), 404


# 観光地IDを持つQRコードを生成するエンドポイント
@api.route('/generate-qrcode', methods=['POST'])
def generate_qrcode():
    data = request.get_json()
    spot_id = data.get('spotId')

    if not spot_id:
        return jsonify({'message': '観光地IDが必要です'}), 400

    # QRコードの内容に観光地IDを埋め込む
    qr_data = f"spot_id:{spot_id}"

    # QRコードを生成
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    # 生成したQRコードを画像に変換
    img = qr.make_image(fill='black', back_color='white')

    # 画像をバイナリとしてレスポンスに送信
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')