import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, "academia.db")
    app.config["SECRET_KEY"] = "dev-academia-secret-change-me"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.replace("\\", "/")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para continuar."
    login_manager.login_message_category = "warning"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.enrollments import bp as enrollments_bp
    from app.routes.payments import bp as payments_bp
    from app.routes.plans import bp as plans_bp
    from app.routes.students import bp as students_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(plans_bp)
    app.register_blueprint(enrollments_bp)
    app.register_blueprint(payments_bp)

    with app.app_context():
        db.create_all()
        _ensure_admin()

    return app


def _ensure_admin():
    from app.models import User

    if User.query.filter_by(username="admin").first():
        return
    admin = User(
        username="admin",
        name="Recepção",
        password_hash=generate_password_hash("admin123"),
    )
    db.session.add(admin)
    db.session.commit()
