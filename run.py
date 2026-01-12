import os
from app import app
from extensions import db
from app import ensure_default_admin

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_default_admin()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)