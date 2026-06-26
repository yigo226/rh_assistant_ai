from flask_login import UserMixin
from datetime import datetime

from config.database import db


# class User(UserMixin, db.Model):
#     __tablename__ = "users"

#     id = db.Column(db.Integer, primary_key=True)

#     nom = db.Column(db.String(100), nullable=False)
#     prenom = db.Column(db.String(100), nullable=False)
#     email = db.Column(db.String(150), unique=True, nullable=False )
#     mot_de_passe = db.Column(
#         db.String(255),
#         nullable=False
#     )

#     telephone = db.Column(
#         db.String(20),
#         nullable=True
#     )
#     actif = db.Column(
#         db.Boolean,
#         default=True
#     )
#     date_creation = db.Column(
#         db.DateTime,
#         default=datetime.utcnow
#     )

#     derniere_connexion = db.Column(
#         db.DateTime,
#         nullable=True
#     )

#     photo = db.Column(
#         db.String(255),
#         nullable=True
#     )

#     bio = db.Column(
#         db.Text,
#         nullable=True
#     )

#     role = db.Column(db.String(20), default="candidat", nullable=False) 
   
#     def est_admin(self):
#         return self.role == "admin"
#     def est_recruteur(self):
#         return self.role == "recruteur"
#     def est_candidat(self):
#         return self.role == "candidat"

#     def __repr__(self):
#         return f"<User {self.email}>"
    


class User(UserMixin, db.Model):
    __tablename__ = "users"

    # ============================================================
    # SÉCURITÉ : CONTRAINTE DE VÉRIFICATION CONDITIONNELLE
    # ============================================================
    __table_args__ = (
        db.CheckConstraint(
            "(role = 'recruteur' AND entreprise_id IS NOT NULL) OR (role != 'recruteur')",
            name="check_recruteur_has_entreprise"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(20), nullable=True)
    actif = db.Column(db.Boolean, default=True)
    
    date_creation = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )

    derniere_connexion = db.Column(db.DateTime, nullable=True)
    photo = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # Rôle utilisateur ('candidat', 'recruteur')
    role = db.Column(db.String(20), default="candidat", nullable=False) 

    # CLÉ ÉTRANGÈRE : Liée à la table entreprises
    entreprise_id = db.Column(
        db.Integer, 
        db.ForeignKey("entreprises.id", ondelete="SET NULL"), 
        nullable=True
    )

    # Relation ORM pour récupérer facilement l'objet Entreprise depuis le code Python
    entreprise = db.relationship("Entreprise", foreign_keys=[entreprise_id])
    
    # AJOUT : Liaison vers le département (rempli uniquement si le candidat est retenu/employé)
    departement_id = db.Column(
        db.Integer, 
        db.ForeignKey("departements.id", ondelete="SET NULL"), 
        nullable=True
    )

    def est_recruteur(self):
        return self.role == "recruteur"
    
    def est_candidat(self):
        return self.role == "candidat"
    
    def est_employe(self):
        return self.role == "employe"

    def __repr__(self):
        return f"<User {self.email} - Rôle: {self.role}>"
