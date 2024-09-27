from flask import Blueprint, request, jsonify, send_file
from .models import User, Stamp, StampDetail, Spot, Review, db
from . import bcrypt
from flask_jwt_extended import create_access_token, jwt_required
from io import BytesIO
import qrcode
from .GenerateRoute.dummy_data import DummyData
from .GenerateRoute.generate_route_wrapper import GENERATE_ROUTE_WRAPPER
from .GenerateRoute.calculate_travel_time import CALCULATE_TRAVEL_TIME

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


# 観光地一覧取得API
@api.route('/spots_list', methods=['GET'])
def get_spots_list():
    # データベースから全観光地を取得し、名前のあいうえお順で並べ替える
    spots = Spot.query.order_by(Spot.spot_name.asc()).all()

    # 取得したデータをレスポンス用のリストに整形
    spots_list = [
        {
            'spot_id': spot.id,
            'spot_name': spot.spot_name,
            'thum_image': spot.thum_image
        }
        for spot in spots
    ]

    # JSON形式でレスポンスを返す
    return jsonify({'spots_list': spots_list}), 200


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



'''
author : kabetani yusei
経路生成周りの処理
'''
# スタンプラリークリック時エンドポイント
@api.route('stamp-rally/incomplete', methods=['POST'])
def stamp_rally_imcomplete():
    data = request.get_json()
    user_id = data.get('user_id')
    stamp = Stamp.query.filter_by(user_id=user_id, status=0).first()
    if not stamp:
        return jsonify({"exist": False}), 200

    #スタンプラリーが見つかった場合は、stamp_detailから詳細を取得する
    stamp_details = StampDetail.query.filter_by(stamp_id=stamp.id).all()
    spot_list = []
    route = []
    for stamp_detail in stamp_details:
        spot = Spot.query.filter_by(id=stamp_detail.spot_id).first()
        route.append(spot.id)
        spot_list.append({
            "id": spot.id,
            "spot_name": spot.spot_name,
            "coordinate": spot.coordinate,
            "staying_time": spot.staying_time,
            "recommendation": spot.recommendation,
            "spot_type": spot.spot_type,
            'status': stamp_detail.status
        })
    func_calc = CALCULATE_TRAVEL_TIME(route, spot_list)
    route_info = func_calc.calculate_travel_time()
    route_info["exist"] = True
    route_info["stamp_id"] = stamp.id
    return jsonify(route_info), 200

#　経路生成エンドポイント
@api.route('/generate-route', methods=['POST'])
def generate_route():
    # userからデータを受け取る
    data = request.get_json()
    # データベースからデータを受け取る
    spots = Spot.query.all()
    spot_list = []
    for spot in spots:
        spot_list.append({
            'id': spot.id,
            'spot_name': spot.spot_name,
            'coordinate': spot.coordinate,
            'staying_time': spot.staying_time,
            'recommendation': spot.recommendation,
            'spot_type': spot.spot_type,
            'status' : 0
        })
    try:
        func_gen = GENERATE_ROUTE_WRAPPER(data, spot_list)
    except:
        return jsonify({"message": "データが不正です"}), 400
    route = func_gen.execute_generate_route()
    if route == False:
        return jsonify({"message": "経路が見つかりませんでした"}), 400
    func_calc = CALCULATE_TRAVEL_TIME(route, spot_list)
    route_info = func_calc.calculate_travel_time()
    # スタンプラリーの保存
    stamp = Stamp(user_id=data.get('user_id'), status=0)
    db.session.add(stamp)
    db.session.commit()
    stamp_id = stamp.id
    for spot_id in route:
        stamp_detail = StampDetail(stamp_id=stamp_id, spot_id=spot_id)
        db.session.add(stamp_detail)
    db.session.commit()
    route_info['stamp_id'] = stamp_id
    return jsonify(route_info), 200

# dummyデータをデータベースに登録する
@api.route('/dummy_insert', methods=['GET'])
def dummy_insert():
    for item in DummyData:
        spot = Spot(
            spot_name=item['spot_name'],
            coordinate=str(item['coordinate']),
            staying_time=item['staying_time'],
            recommendation=item['recommendation'],
            spot_type=item['spot_type']
        )
        db.session.add(spot)  # Spotオブジェクトをセッションに追加
    
    db.session.commit()  # データベースに変更をコミット
    return jsonify({"message": "Data inserted successfully!"}), 201



'''
author : ninomiya osuke
口コミの管理者ページ周りの処理
'''
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# 悪質レビュー取得のエンドポイント
@api.route('/get_reviews')
def get_reviews():
    # レビューを取得
    reviews = (
        db.session.query(Review.id, Review.text, Spot.spot_name)
        .join(Spot, Review.spot_id == Spot.id)
        .filter(Review.report == 1, Review.confirmation == 0)
        .all()
    )
    
    # 結果を辞書形式に変換
    result = [{'id': r.id, 'text': r.text, 'spot_name': r.spot_name} for r in reviews]
    if result == []:
        return jsonify({"message": "該当のものがありません"}), 404
    return jsonify(result), 200

# レビュー承認のエンドポイント
@api.route('/approve/<int:review_id>', methods=['POST'])
def approve_review(review_id):
    review = Review.query.get(review_id)  # IDでレビューを取得
    if review is None:
        return jsonify({"message": "レビューが見つかりません"}), 404
    review.confirmation = 1
    db.session.commit()
    return jsonify({"message": "レビューが承認されました"}), 200

# レビュー削除のエンドポイント
@api.route('/delete_review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    review = Review.query.get(review_id)  # IDでレビューを取得
    if review is None:
        return jsonify({"message": "レビューが見つかりません"}), 404
    db.session.delete(review)  # レビューをセッションから削除
    db.session.commit()
    return jsonify({"message": "レビューが削除されました"}), 200