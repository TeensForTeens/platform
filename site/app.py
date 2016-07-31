from database import database
from flask import Flask, render_template, flash, redirect, make_response, request, session
from utils import send_email, send_error_email, send_warning_email
import logging
import subprocess
import traceback
import decimal

log_formatter = logging.Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s
''')

def create_app(environment):
    app = Flask(__name__)
    app.config.from_pyfile("config/{}.py".format(environment))

    database.init(app.config["DB_PATH"])

    if app.config["EMAIL_ERRORS"]:
        from logging.handlers import SMTPHandler
        mail_handler = SMTPHandler('127.0.0.1', app.config["EMAIL_FROM"], app.config["SITE_ADMIN"], 'Exception in TFT-{}'.format(environment))
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(log_formatter)
        app.logger.addHandler(mail_handler)

    from modules.account.blueprint import account
    from modules.staticpages.blueprint import staticpages
    from modules.donations.blueprint import donations
    from modules.email_list.blueprint import email_list
    from modules.volunteer.blueprint import volunteer
    from modules.rcon.blueprint import rcon
    from modules.reports.blueprint import reports
    from modules.security.blueprint import security
    from modules.states.blueprint import states

    app.register_blueprint(account)
    app.register_blueprint(security)
    app.register_blueprint(volunteer)
    app.register_blueprint(donations)
    app.register_blueprint(email_list)
    app.register_blueprint(rcon)
    app.register_blueprint(reports)
    app.register_blueprint(states)
    app.register_blueprint(staticpages) # staticpages must be registered last

    @app.route("/favicon.ico")
    def favicon(): return redirect('/static/favicon.ico')

    @app.route("/robots.txt")
    def robots_txt(): return redirect('/static/robots.txt')

    @app.route("/teensforteens.info.html")
    def verify_cert(): return "MTRHYzBuSUg3TU1DSnNiZzJqZHo0WXllWnc0NVB3OWE4MmpUd0ZGa0dSdz0"

    @app.route("/googlefe31abc06e03d8f7.html")
    def google(): return "google-site-verification: googlefe31abc06e03d8f7.html"

    @app.context_processor
    def inject_config():
        if app.config["DISPLAY_DEBUG_INFO"]:
            version = subprocess.check_output(["git", "describe", "--always"]).decode().strip()
        else:
            version = ""
        return dict(global_config=app.config, version=version)

    @app.errorhandler(404)
    def page_not_found(exc):
        return make_response(render_template("not_found.html"), 404)

    @app.errorhandler(500)
    def internal_error(exc):
        trace = traceback.format_exc()
        try:
            send_error_email(environment, trace)
        except:
            trace = traceback.format_exc()
        return make_response(render_template("whoops.html", trace=trace), 500)

    @app.before_request
    def verify_session():
        user_ip = request.headers.get("X-Forwarded-For", None)
        if "ip" not in session:
            session["ip"] = user_ip
        else:
            if session["ip"] != user_ip and "logged_in" in session:
                send_warning_email(environment, "Session validation failed: {}".format(list(session.items())))
                session.pop("logged_in", None)
                session.pop("uid", None)
                session.pop("ip", None)

    @app.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "private, max-age=0, no-cache"
        return response

    @app.template_filter('money_format')
    def money_format(amount):
        dollars = decimal.Decimal(amount) / 100
        return "${}".format(dollars)

    return app

if __name__ == '__main__':
    create_app("dev").run(port=5000, debug=True)
