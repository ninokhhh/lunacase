from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from extensions import db, login_manager
from forms import RegisterForm, LoginForm
from models import User, WishlistItem, CartItem, Order, OrderItem



DEFAULT_ADMIN_EMAIL = "admin@lunacase.com"
DEFAULT_ADMIN_PASSWORD = "Admin123!"


def admin_required(view_func):
    
    from functools import wraps

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return view_func(*args, **kwargs)

    return wrapper


def ensure_default_admin():
   
    existing_admin = User.query.filter_by(is_admin=True).first()
    if existing_admin:
        return

   
    u = User.query.filter_by(email=DEFAULT_ADMIN_EMAIL.lower().strip()).first()
    if u:
        u.is_admin = True
        db.session.commit()
        return

    
    admin_user = User(full_name="Admin", email=DEFAULT_ADMIN_EMAIL.lower().strip(), is_admin=True)
    admin_user.set_password(DEFAULT_ADMIN_PASSWORD)
    db.session.add(admin_user)
    db.session.commit()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "change-this-to-any-random-string"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lunacase.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "login"
    login_manager.login_message_category = "info"

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/products")
    def products():
        return render_template("product.html")

    @app.route("/upload")
    @login_required
    def upload():
        return render_template("upload.html")

    @app.route("/cart")
    @login_required
    def cart():
        items = (
            CartItem.query.filter_by(user_id=current_user.id)
            .order_by(CartItem.created_at.desc())
            .all()
        )
        total = sum((it.price or 0) * (it.quantity or 1) for it in items)
        return render_template("cart.html", items=items, total=total)

    @app.route("/cart/add", methods=["POST"])
    @login_required
    def cart_add():
        img = request.form.get("img")
        title = request.form.get("title")
        price = int(request.form.get("price", 45))

        if not img or not title:
            flash("Missing product data.", "danger")
            return redirect(url_for("products"))

        existing = CartItem.query.filter_by(user_id=current_user.id, img=img).first()
        if existing:
            existing.quantity = (existing.quantity or 1) + 1
            db.session.commit()
            flash("Quantity updated ✅", "success")
            return redirect(url_for("cart"))

        item = CartItem(
            img=img,
            title=title,
            price=price,
            quantity=1,
            user_id=current_user.id,
        )
        db.session.add(item)
        db.session.commit()
        flash("Added to cart ✅", "success")
        return redirect(url_for("cart"))

    @app.route("/cart/remove/<int:item_id>", methods=["POST"])
    @login_required
    def cart_remove(item_id):
        item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
        db.session.delete(item)
        db.session.commit()
        flash("Removed from cart.", "info")
        return redirect(url_for("cart"))

    @app.route("/cart/inc/<int:item_id>", methods=["POST"])
    @login_required
    def cart_inc(item_id):
        item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
        item.quantity = (item.quantity or 1) + 1
        db.session.commit()
        return redirect(url_for("cart"))

    @app.route("/cart/dec/<int:item_id>", methods=["POST"])
    @login_required
    def cart_dec(item_id):
        item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
        item.quantity = (item.quantity or 1) - 1

        if (item.quantity or 0) <= 0:
            db.session.delete(item)

        db.session.commit()
        return redirect(url_for("cart"))

    @app.route("/wishlist")
    @login_required
    def wishlist():
        items = (
            WishlistItem.query.filter_by(user_id=current_user.id)
            .order_by(WishlistItem.created_at.desc())
            .all()
        )
        return render_template("wishlist.html", items=items)

    @app.route("/wishlist/add", methods=["POST"])
    @login_required
    def wishlist_add():
        img = request.form.get("img")
        title = request.form.get("title")
        price = int(request.form.get("price", 45))

        if not img or not title:
            flash("Missing product data.", "danger")
            return redirect(url_for("products"))

        exists = WishlistItem.query.filter_by(user_id=current_user.id, img=img).first()
        if exists:
            flash("Already in wishlist 💜", "info")
            return redirect(url_for("wishlist"))

        item = WishlistItem(img=img, title=title, price=price, user_id=current_user.id)
        db.session.add(item)
        db.session.commit()
        flash("Added to wishlist ✅", "success")
        return redirect(url_for("wishlist"))

    @app.route("/wishlist/remove/<int:item_id>", methods=["POST"])
    @login_required
    def wishlist_remove(item_id):
        item = WishlistItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
        db.session.delete(item)
        db.session.commit()
        flash("Removed from wishlist.", "info")
        return redirect(url_for("wishlist"))

    @app.route("/checkout", methods=["GET", "POST"])
    @login_required
    def checkout():
        items = CartItem.query.filter_by(user_id=current_user.id).all()
        if not items:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("cart"))

        total = sum((it.price or 0) * (it.quantity or 1) for it in items)

        if request.method == "POST":
            phone_model = request.form.get("phone_model", "").strip()
            address = request.form.get("address", "").strip()
            city = request.form.get("city", "").strip()
            phone_number = request.form.get("phone_number", "").strip()

            if not all([phone_model, address, city, phone_number]):
                flash("Please fill all fields.", "danger")
                return render_template("checkout.html", items=items, total=total)

            order = Order(
                phone_model=phone_model,
                address=address,
                city=city,
                phone_number=phone_number,
                total=total,
                user_id=current_user.id,
            )
            db.session.add(order)
            db.session.flush()

            for it in items:
                db.session.add(
                    OrderItem(
                        img=it.img,
                        title=it.title,
                        price=it.price or 0,
                        quantity=it.quantity or 1,
                        order_id=order.id,
                    )
                )

            CartItem.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()

            return redirect(url_for("order_success", order_id=order.id))

        return render_template("checkout.html", items=items, total=total)

    @app.route("/order/success/<int:order_id>")
    @login_required
    def order_success(order_id):
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
        return render_template("order_success.html", order=order)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        form = RegisterForm()
        if form.validate_on_submit():
            email = form.email.data.lower().strip()
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash("Email already registered. Please login.", "warning")
                return redirect(url_for("login"))

            user = User(full_name=form.full_name.data.strip(), email=email)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            flash("Account created! Please login.", "success")
            return redirect(url_for("login"))

        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        form = LoginForm()
        if form.validate_on_submit():
            email = form.email.data.lower().strip()
            user = User.query.filter_by(email=email).first()

            if user and user.check_password(form.password.data):
                login_user(user)
                flash("Logged in successfully!", "success")
                return redirect(url_for("home"))

            flash("Invalid email or password.", "danger")

        return render_template("login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out.", "info")
        return redirect(url_for("home"))

  
    @app.route("/admin")
    @login_required
    @admin_required
    def admin_panel():
        users = User.query.order_by(User.created_at.desc()).all()
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return render_template("admin.html", users=users, orders=orders)

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
       
        ensure_default_admin()

    app.run(debug=True)