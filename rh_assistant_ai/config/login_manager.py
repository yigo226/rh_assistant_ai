from flask_login import LoginManager
from models.utilisateur import Utilisateur

login_manager = LoginManager()

# page de redirection si non connecté
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))