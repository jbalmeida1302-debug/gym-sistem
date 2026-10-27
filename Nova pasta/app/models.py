from datetime import date

from flask_login import UserMixin

from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    payments = db.relationship("Payment", backref="registered_by", lazy=True)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    document = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="ativo")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    enrollments = db.relationship(
        "Enrollment", backref="student", lazy=True, order_by="Enrollment.start_date.desc()"
    )


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    enrollments = db.relationship("Enrollment", backref="plan", lazy=True)


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ativa")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    payments = db.relationship(
        "Payment", backref="enrollment", lazy=True, order_by="Payment.paid_at.desc()"
    )

    @property
    def has_paid(self):
        return any(p.status == "pago" for p in self.payments)

    @property
    def is_delinquent(self):
        return self.status != "cancelada" and not self.has_paid


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollment.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    paid_at = db.Column(db.Date, nullable=True)
    method = db.Column(db.String(20), nullable=False, default="pix")
    status = db.Column(db.String(20), nullable=False, default="pendente")
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
