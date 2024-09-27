from flask import Blueprint, request, jsonify
from .models import User, db, Spot, Stamp, StampDetail
from . import bcrypt
from flask_jwt_extended import create_access_token
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