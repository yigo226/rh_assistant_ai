# Dans un fichier utils/decorators.py (ou en haut de vos fichiers de routes)
from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(role_interdit_ou_autorise):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Si l'utilisateur n'a pas le bon rôle, on lui refuse l'accès (Erreur 403)
            if current_user.role != role_interdit_ou_autorise:
                abort(403) 
            return f(*args, **kwargs)
        return decorated_function
    return decorator
