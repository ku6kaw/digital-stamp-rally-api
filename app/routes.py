from flask import Blueprint, request, jsonify, send_file, render_template
from flask import Blueprint, request, jsonify, send_file, render_template
from .models import User, Stamp, StampDetail, Spot, Review, db
from . import bcrypt
from flask_jwt_extended import create_access_token, jwt_required
import boto3
import os
import uuid
import boto3
import os
import uuid
from io import BytesIO
import qrcode
from .GenerateRoute.dummy_data import DummyData
from .GenerateRoute.generate_route_wrapper import GENERATE_ROUTE_WRAPPER
from .GenerateRoute.calculate_travel_time import CALCULATE_TRAVEL_TIME
from datetime import datetime

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

    # emailに基づいてユーザーを検索
    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):  # パスワードチェック
        # トークンに user_id と email を含める
        access_token = create_access_token(identity={"user_id": user.id, "email": user.email})
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"message": "認証に失敗しました"}), 401


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


# QRコードで読み取った観光地IDを基に、スタンプの状態を更新し観光地名を返すAPI
@api.route('/update-stamp', methods=['POST'])
def update_stamp():
    data = request.get_json()
    user_id = data.get('userId')
    spot_id = data.get('spotId')

    # まず、ユーザーの未完了スタンプラリーを取得
    stamp = Stamp.query.filter_by(user_id=user_id, status=0).first()  # status=0は未完了

    if not stamp:
        return jsonify({'message': '未完了のスタンプラリーが見つかりません'}), 404

    # 取得した stamp_id と spot_id でスタンプ詳細を検索
    stamp_detail = StampDetail.query.filter_by(stamp_id=stamp.id, spot_id=spot_id).first()

    if stamp_detail:
        stamp_detail.status = 1  # 状態を実施済みに更新
        db.session.commit()

        # 関連する観光地情報を取得
        spot = Spot.query.filter_by(id=spot_id).first()
        if spot:
            return jsonify({
                'message': 'スタンプが更新されました',
                'spot_name': spot.spot_name  # 観光地名をレスポンスに含める
            }), 200
        else:
            return jsonify({'message': '観光地が見つかりません'}), 404
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

# スタンプラリー情報取得エンドポイント
@api.route('/stamp-rally/details', methods=['POST'])
def get_incomplete_stamp_rally():
    try:
        # リクエストからuser_idを取得
        data = request.get_json()
        user_id = data.get('user_id')

        # user_idがリクエストにない場合はエラーレスポンスを返す
        if not user_id:
            return jsonify({"message": "ユーザーIDが指定されていません"}), 400

        # 指定されたuser_idの未完了のスタンプラリーを取得（status=0が未完了）
        stamp = Stamp.query.filter_by(user_id=user_id, status=0).first()

        # スタンプラリーが見つからない場合、存在しないことをレスポンス
        if not stamp:
            return jsonify({"exist": False}), 200

        # スタンプラリーに含まれるスタンプ詳細（観光地情報）を取得
        stamp_details = StampDetail.query.filter_by(stamp_id=stamp.id).all()

        if not stamp_details:
            return jsonify({"message": "スタンプラリーの詳細情報が見つかりません"}), 404

        # 各観光地の詳細情報を収集
        spot_list = []
        for stamp_detail in stamp_details:
            spot = Spot.query.filter_by(id=stamp_detail.spot_id).first()
            if spot:
                spot_list.append({
                    "id": spot.id,
                    "spot_name": spot.spot_name,
                    "coordinate": spot.coordinate,
                    "staying_time": spot.staying_time,
                    "recommendation": spot.recommendation,
                    "spot_type": spot.spot_type,
                    'status': stamp_detail.status  # 0: 未訪問, 1: 訪問済み
                })

        # 未完了のスタンプラリーの詳細をレスポンスとして返す
        response = {
            "exist": True,
            "stamp_id": stamp.id,
            "user_id": stamp.user_id,
            "status": stamp.status,  # 0: 未完了, 1: 完了
            "spots": spot_list
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"message": f"サーバーエラーが発生しました: {str(e)}"}), 500



#　経路生成エンドポイント
import logging

@api.route('/generate-route', methods=['POST'])
def generate_route():
    # userからデータを受け取る
    data = request.get_json()

    # バリデーション: user_id が空でないか確認
    user_id = data.get('user_id')
    if not user_id or not str(user_id).isdigit():
        return jsonify({"message": "user_idが不正です"}), 400

    # user_id を整数に変換
    user_id = int(user_id)

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
            'status': 0
        })
    
    try:
        # 経路生成関数を呼び出す
        func_gen = GENERATE_ROUTE_WRAPPER(data, spot_list)
    except Exception as e:
        logging.error(f"経路生成関数の呼び出しに失敗しました: {e}")
        return jsonify({"message": "データが不正です"}), 400
    
    route = func_gen.execute_generate_route()
    if route == False:
        return jsonify({"message": "経路が見つかりませんでした"}), 400
    
    try:
        # 移動時間を計算
        func_calc = CALCULATE_TRAVEL_TIME(route, spot_list)
        route_info = func_calc.calculate_travel_time()
    except Exception as e:
        logging.error(f"移動時間計算に失敗しました: {e}")
        return jsonify({"message": "移動時間の計算に失敗しました"}), 500

    try:
        # スタンプラリーの保存
        stamp = Stamp(user_id=user_id, status=0)
        db.session.add(stamp)
        db.session.commit()
        stamp_id = stamp.id
        
        # スタンプラリー詳細の保存
        for spot_id in route:
            stamp_detail = StampDetail(stamp_id=stamp_id, spot_id=spot_id)
            db.session.add(stamp_detail)
        db.session.commit()
    except Exception as e:
        logging.error(f"スタンプラリーの保存に失敗しました: {e}")
        return jsonify({"message": "スタンプラリーの保存に失敗しました"}), 500
    
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


'''
author : nishio takumi
口コミの管理者ページ周りの処理
'''
#口コミ追加エンドポイント
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
    return jsonify({"message": "口コミ追加を成功しました"}), 200

#口コミ通報エンドポイント
@api.route('/report_review', methods=['POST'])
def report_review():
    data = request.get_json()
    review_id = data.get('id')
    #Flagを立てる
    test = db.session.query(Review).filter(Review.id==review_id).first()
    if test is None:
        return jsonify({"message": "口コミが見つかりません"}), 404
    test.report = 1
    db.session.commit()
    
    return jsonify({"message": "口コミを通報しました"}), 200

# 建物の詳細ページのエンドポイント
@api.route('/tourist_spots/<int:spot_id>', methods=['GET'])
def building_detail(spot_id):
    spot_data = db.session.query(Spot).filter(Spot.id==spot_id).first()# 建物の紹介文と住所
    if spot_data is None:
        return jsonify({"message": "該当のものがありません"}), 404

    revew_data_all = db.session.query(Review).filter(Review.spot_id==spot_id)# 口コミ情報

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

    identity_dict = {
        'spot_id': spot_data.id,
        'name': spot_data.spot_name,
        'description': spot_data.text,
        'address': spot_data.address,
        'staying_time': spot_data.staying_time,
        'image1': spot_data.image1,
        'image2': spot_data.image2,
        'image3': spot_data.image3,
        'image4': spot_data.image4,
        'image5': spot_data.image5,
        'image6': spot_data.image6,
        'reviews': review_list
    }
    return jsonify(identity_dict), 200


# S3の設定
S3_BUCKET_NAME = "bucket-yamada-1"
S3_REGION = "ap-northeast-1"
s3 = boto3.client('s3', region_name=S3_REGION)

# 画像アップロード許可拡張子
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file_to_s3(file, acl="public-read"):
    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4()}.{ext}"
        file_path = f"static/images/{new_filename}"
        s3.upload_fileobj(
            file,
            S3_BUCKET_NAME,
            file_path,
            ExtraArgs={"ACL": acl, "ContentType": file.content_type}
        )
        return f"/static/images/{new_filename}"  # 相対パスを返す
    except Exception as e:
        print("Something Happened: ", e)
        return None

# 観光地データのアップロードエンドポイント
@api.route('/upload', methods=['POST'])
def upload_place():
    try:
        if request.method == 'POST':
            # 必須フィールドのチェック
            required_fields = ['name', 'address', 'coordinates', 'avg_stay_time', 'popularity', 'type', 'description']
            for field in required_fields:
                if field not in request.form:
                    return jsonify({"error": f"{field}が入力されていません。"}), 400

            thumbnail = request.files['thumbnail']
            name = request.form['name']
            address = request.form['address']
            coordinates = request.form['coordinates']
            avg_stay_time = request.form['avg_stay_time']
            popularity = request.form['popularity']
            type = request.form['type']
            description = request.form['description']
            photos = request.files.getlist('photos[]')

            # サムネイルのチェック
            if not thumbnail or not allowed_file(thumbnail.filename):
                return jsonify({"error": "サムネイル画像が無効です。"}), 400

            thumbnail_url = upload_file_to_s3(thumbnail)
            if not thumbnail_url:
                return jsonify({"error": "サムネイル画像のアップロードに失敗しました。"}), 500

            image_urls = [''] * 6
            for i, photo in enumerate(photos):
                if i >= 6:
                    break
                if photo and allowed_file(photo.filename):
                    image_url = upload_file_to_s3(photo)
                    if not image_url:
                        return jsonify({"error": f"{i+1}番目の画像のアップロードに失敗しました。"}), 500
                    image_urls[i] = image_url

            # データベースに保存
            new_spot = Spot(
                spot_name=name,
                text=description,
                address=address,
                coordinate=coordinates,
                image1=image_urls[0],
                image2=image_urls[1],
                image3=image_urls[2],
                image4=image_urls[3],
                image5=image_urls[4],
                image6=image_urls[5],
                thum_image=thumbnail_url,
                staying_time=avg_stay_time,
                recommendation=popularity,
                spot_type=type
            )
            db.session.add(new_spot)
            db.session.commit()

            return jsonify({"message": "場所が正常に投稿されました！"}), 200

    except Exception as e:
        return jsonify({"error": f"予期せぬエラーが発生しました: {str(e)}"}), 500

    return jsonify({"error": "無効なリクエストです。"}), 400
