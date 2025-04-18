from flask import Blueprint, render_template, redirect, url_for, flash
from app.forms import ChooseForm
from flask_login import current_user, logout_user, login_required
from app import db
from app.models import User

admin_bp = Blueprint('admin', __name__, template_folder='templates/admin')


@admin_bp.route('/', methods=['GET', 'POST'])
@login_required
def admin():
    form = ChooseForm()
    if current_user.role != 'Admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('public.landing'))

    if form.validate_on_submit():
        try:
            delete_value = int(form.delete.data) if form.delete.data else -1
            change_value = int(form.change.data) if form.change.data else -1
            admin_count = User.query.filter_by(role='Admin').count()

            if (
                    delete_value == current_user.id and admin_count > 1
                    or
                    change_value == current_user.id and admin_count > 1
            ):
                logout_user()

            if delete_value != -1:
                user = User.query.get(delete_value)
                if not user:
                    flash(f"User with ID: {delete_value} does not exist", 'danger')
                    return redirect(url_for('.admin'))
                if user.role == 'Admin':
                    if admin_count <= 1:
                        flash('Must have at least one admin', 'danger')
                        return redirect(url_for('.admin'))
                db.session.delete(user)
                db.session.commit()
                flash(f"{user.username} has been deleted successfully", 'success')
                return redirect(url_for('.admin'))
            elif change_value != -1:
                user = User.query.get(change_value)
                if not user:
                    flash(f"User with ID: {change_value} does not exist", 'danger')
                    return redirect(url_for('.admin'))
                if user.role == 'Admin':
                    if admin_count <= 1:
                        flash('Must have at least one admin', 'danger')
                        return redirect(url_for('.admin'))
                    user.role = 'Normal'
                else:
                    user.role = 'Admin'
                db.session.commit()
                flash(f"{user.username}'s role has been changed successfully", 'success')
                return redirect(url_for('.admin'))
        except Exception as e:
            flash('Error occurred while performing action', 'danger')
            print(f"Error: {e}")

    users = User.query.all()
    headers = ['ID', 'Username', 'Email', 'Role', 'Delete', 'Swap Role']
    return render_template(
        'admin.html',
        title='Admin Page',
        form=form,
        headers=headers,
        users=users
    )
