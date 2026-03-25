from flask import render_template


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/error.html", code=400, message="Bad request."), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/error.html", code=403, message="You do not have permission to access this resource."), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/error.html", code=404, message="The page you requested could not be found."), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("errors/error.html", code=500, message="An unexpected error occurred."), 500
