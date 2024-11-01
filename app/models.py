from flask_login import UserMixin
from datetime import datetime
from app import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class TollChalan(db.Model):
    __tablename__ = 'toll_chalans'
    
    id = db.Column(db.Integer, primary_key=True)
    license_plate_text = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer, nullable=False, default=300)
    confidence = db.Column(db.Float, nullable=False)
    x_coordinate = db.Column(db.Float, nullable=False)
    y_coordinate = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, license_plate_text, confidence, x_coordinate, y_coordinate, width, height, amount=300):
        self.license_plate_text = license_plate_text
        self.confidence = confidence
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.width = width
        self.height = height
        self.amount = amount
