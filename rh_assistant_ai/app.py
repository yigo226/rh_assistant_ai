from flask import Flask, render_template
from config.login_manager import login_manager
from config.settings import Config
from config.database import db, migrate
from models.user import User

from routes.auth_routes import auth_bp
from routes.cv_routes import cv_bp
from routes.offre_routes import offre_bp
from routes.match_routes import matching_bp
from routes.routes_global import global_bp  
from routes.recruteur_route import recruteur_bp
from routes.candidat_route import candidat_bp
def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/")
    def home():
        return render_template('index.html')
    
    # Les autres routes  
    app.register_blueprint(auth_bp)
    app.register_blueprint(cv_bp)
    app.register_blueprint(offre_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(global_bp)
    app.register_blueprint(recruteur_bp)
    app.register_blueprint(candidat_bp)
    
    #print("app.url_map: \n", app.url_map)

    return app


app = create_app()

login_manager.init_app(app)

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )