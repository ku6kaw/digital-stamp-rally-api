from . import db, bcrypt
from sqlalchemy import func

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
    __tablename__ = 'spot_info'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spot_name = db.Column(db.Text, nullable=False)
    text = db.Column(db.Text, nullable=True)
    address = db.Column(db.Text, nullable=True)
    coordinate = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text, nullable=True)
    thum_image = db.Column(db.Text, nullable=True)
    staying_time = db.Column(db.Integer, nullable=False)
    recommendation = db.Column(db.Integer, nullable=False)
    spot_type = db.Column(db.Integer, nullable=False)



class Stamp(db.Model):
    __tablename__ = 'stamp'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    status = db.Column(db.Integer, nullable=False)

class StampDetail(db.Model):
    __tablename__ = 'stamp_detail'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stamp_id = db.Column(db.Integer, nullable=False)
    spot_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)