from flask import Blueprint, render_template

public_bp = Blueprint('public', __name__, template_folder='templates/public')


@public_bp.route('/')
def landing():
    return render_template('landing.html', title='Home')
