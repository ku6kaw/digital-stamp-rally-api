from . import db, bcrypt
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    @property
    def password(self):
        raise AttributeError('パスワードは読み取れません')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
class Spot(db.Model):
    __tablename__ = 'spot'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spot_name = db.Column(db.Text, nullable=False)
    text = db.Column(db.Text)
    address = db.Column(db.Text)
    coordinate = db.Column(db.Text)
    thum_image = db.Column(db.Text)
    staying_time = db.Column(db.Integer)
    recommendation = db.Column(db.Integer, nullable=False)
    spot_type = db.Column(db.Integer, nullable=False)
    image1 = db.Column(db.Text)
    image2 = db.Column(db.Text)
    image3 = db.Column(db.Text)
    image4 = db.Column(db.Text)
    image5 = db.Column(db.Text)
    image6 = db.Column(db.Text)

    reviews = db.relationship('Review', backref='spot', lazy=True)
    

class Review(db.Model):
    __tablename__ = 'review'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    spot_id = db.Column(db.Integer, db.ForeignKey('spot.id'), nullable=False)
    text = db.Column(db.Text)
    report = db.Column(db.Integer, default=0)
    confirmation = db.Column(db.Integer, default=0)


# Stampモデル
class Stamp(db.Model):
    __tablename__ = 'stamp'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)
    
    # リレーション
    details = db.relationship('StampDetail', backref='stamp', lazy=True)

# StampDetailモデル
class StampDetail(db.Model):
    __tablename__ = 'stamp_detail'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stamp_id = db.Column(db.Integer, db.ForeignKey('stamp.id'), nullable=False)
    spot_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)
