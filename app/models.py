from app import db
from flask_login import UserMixin, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import secrets
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
# ======== MODELS =========
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_banned = db.Column(db.Boolean, default=False)
    session_version = db.Column(db.String(32), nullable=False, default=lambda: secrets.token_hex(16))

    def set_password(self, password: str):
        self.password = generate_password_hash(password)  

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(128), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)

    def is_valid(self):
       
        return not self.used and (datetime.utcnow() - self.created_at < timedelta(hours=1))

    @staticmethod
    def generate(user_id):
        token = secrets.token_urlsafe(32)
        prt = PasswordResetToken(token=token, user_id=user_id)
        db.session.add(prt)
        db.session.commit()
        return token

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    poster = db.Column(db.String(300), nullable=True)
    average_rating = db.Column(db.Float, default=0.0)

    @property
    def computed_rating(self): 
        if not self.reviews:
            return 0
        return sum(r.rating for r in self.reviews) / len(self.reviews)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    rating = db.Column(db.Integer, nullable=False, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    movie = db.relationship('Movie', backref=db.backref('reviews', lazy=True))


