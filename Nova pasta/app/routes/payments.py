from datetime import date
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms import PaymentForm
from app.models import Enrollment, Payment
from app.services import refresh_enrollment_statuses

bp = Blueprint("payments", __name__, url_prefix="/pagamentos")


@bp.route("/")
@login_required
def list_payments():
    refresh_enrollment_statuses()
    view = request.args.get("view") or "todos"
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    enrollments = Enrollment.query.filter(Enrollment.status.in_(["ativa", "vencida"])).all()
    delinquent = [e for e in enrollments if e.is_delinquent]
    pending = [p for p in payments if p.status == "pendente"]
    return render_template(
        "payments/list.html",
        payments=payments,
        pending=pending,
        delinquent=delinquent,
        view=view,
    )


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def create():
    form = PaymentForm()
    enrollment_id = request.args.get("matricula", type=int)
    _set_choices(form)
    if not form.is_submitted():
        form.paid_at.data = date.today()
        if enrollment_id:
            form.enrollment_id.data = enrollment_id
            enrollment = Enrollment.query.get(enrollment_id)
            if enrollment:
                form.amount.data = enrollment.plan.price
    if form.validate_on_submit():
        enrollment = Enrollment.query.get_or_404(form.enrollment_id.data)
        payment = Payment(
            enrollment=enrollment,
            user_id=current_user.id,
            amount=Decimal(form.amount.data),
            method=form.method.data,
            status=form.status.data,
            notes=(form.notes.data or "").strip() or None,
            paid_at=form.paid_at.data if form.status.data == "pago" else None,
        )
        db.session.add(payment)
        db.session.commit()
        flash("Pagamento registrado.", "success")
        return redirect(url_for("payments.list_payments"))
    return render_template("payments/form.html", form=form, title="Registrar pagamento")


@bp.route("/<int:payment_id>/pagar", methods=["POST"])
@login_required
def mark_paid(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = "pago"
    payment.paid_at = date.today()
    db.session.commit()
    flash("Pagamento marcado como pago.", "success")
    return redirect(url_for("payments.list_payments", view="pendentes"))


def _set_choices(form):
    enrollments = Enrollment.query.order_by(Enrollment.id.desc()).all()
    form.enrollment_id.choices = [
        (
            e.id,
            f"#{e.id} — {e.student.name} / {e.plan.name} ({e.status})",
        )
        for e in enrollments
    ]
