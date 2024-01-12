from flask import Flask

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'buzzcar-team018-cs6400'

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for landing page
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # blueprint for reports
    from .report import rep as rep_blueprint
    app.register_blueprint(rep_blueprint)

    return app
