from app import app
from extensions import db
from models import User

with app.app_context():
    user = User.query.filter_by(email="nino.music@mail.ru").first()
    if user:
        user.is_admin = True
        db.session.commit()
        print("ADMIN READY 👑")
    else:
        print("User not found ❌")