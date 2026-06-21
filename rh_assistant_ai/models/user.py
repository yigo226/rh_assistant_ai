from flask_login import UserMixin
from datetime import datetime

from config.database import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False )
    mot_de_passe = db.Column(
        db.String(255),
        nullable=False
    )

    telephone = db.Column(
        db.String(20),
        nullable=True
    )
    actif = db.Column(
        db.Boolean,
        default=True
    )
    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    derniere_connexion = db.Column(
        db.DateTime,
        nullable=True
    )

    photo = db.Column(
        db.String(255),
        nullable=True
    )

    bio = db.Column(
        db.Text,
        nullable=True
    )

    role = db.Column(db.String(20), default="candidat", nullable=False) 
   
    def est_admin(self):
        return self.role == "admin"
    def est_recruteur(self):
        return self.role == "recruteur"
    def est_candidat(self):
        return self.role == "candidat"

    def __repr__(self):
        return f"<User {self.email}>"