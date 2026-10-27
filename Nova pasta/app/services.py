from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from app import db
from app.models import Enrollment, Payment, Student


def refresh_enrollment_statuses():
    today = date.today()
    rows = Enrollment.query.filter(Enrollment.status != "cancelada").all()
    changed = False
    for enrollment in rows:
        new_status = "vencida" if enrollment.end_date < today else "ativa"
        if enrollment.status != new_status:
            enrollment.status = new_status
            changed = True
    if changed:
        db.session.commit()


def create_enrollment(student, plan, start_date=None):
    start = start_date or date.today()
    enrollment = Enrollment(
        student=student,
        plan=plan,
        start_date=start,
        end_date=start + timedelta(days=plan.duration_days),
        status="ativa",
    )
    db.session.add(enrollment)
    student.status = "ativo"
    return enrollment


def renew_enrollment(enrollment):
    today = date.today()
    start = enrollment.end_date if enrollment.end_date >= today else today
    if start < today:
        start = today
    plan = enrollment.plan
    enrollment.start_date = start
    enrollment.end_date = start + timedelta(days=plan.duration_days)
    enrollment.status = "ativa"
    enrollment.student.status = "ativo"
    return enrollment


def cancel_enrollment(enrollment):
    enrollment.status = "cancelada"


def dashboard_stats():
    refresh_enrollment_statuses()
    today = date.today()
    start_month = today.replace(day=1)
    end_month = today.replace(day=monthrange(today.year, today.month)[1])

    active_students = Student.query.filter_by(status="ativo").count()
    expired = Enrollment.query.filter_by(status="vencida").count()
    pending_payments = Payment.query.filter_by(status="pendente").count()

    paid_this_month = Payment.query.filter(
        Payment.status == "pago",
        Payment.paid_at >= start_month,
        Payment.paid_at <= end_month,
    ).all()
    revenue = sum((p.amount for p in paid_this_month), Decimal("0.00"))

    delinquent = [
        e
        for e in Enrollment.query.filter(Enrollment.status.in_(["ativa", "vencida"])).all()
        if e.is_delinquent
    ]

    recent_enrollments = (
        Enrollment.query.order_by(Enrollment.created_at.desc()).limit(8).all()
    )

    return {
        "active_students": active_students,
        "expired": expired,
        "pending_payments": pending_payments,
        "revenue": revenue,
        "delinquent_count": len(delinquent),
        "recent_enrollments": recent_enrollments,
        "delinquent": delinquent[:8],
    }
