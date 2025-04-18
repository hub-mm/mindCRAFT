from flask import Blueprint, render_template

errors_bp = Blueprint('errors', __name__, template_folder='templates/errors')


# Error handler for 403 Forbidden
@errors_bp.errorhandler(403)
def error_403(error):
    return render_template('errors/403.html', title='Error'), 403


# Handler for 404 Not Found
@errors_bp.errorhandler(404)
def error_404(error):
    return render_template('errors/404.html', title='Error'), 404


@errors_bp.errorhandler(413)
def error_413(error):
    return render_template('errors/413.html', title='Error'), 413


# 500 Internal Server Error
@errors_bp.errorhandler(500)
def error_500(error):
    return render_template('errors/500.html', title='Error'), 500
