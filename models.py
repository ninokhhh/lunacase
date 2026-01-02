from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


    is_admin = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wishlist_items = db.relationship("WishlistItem", backref="user", lazy=True)
    cart_items = db.relationship("CartItem", backref="user", lazy=True)
    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, default=45)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, default=45)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)


    phone_model = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(220), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(40), nullable=False)

    total = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    items = db.relationship("OrderItem", backref="order", lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    img = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False, default=45)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))