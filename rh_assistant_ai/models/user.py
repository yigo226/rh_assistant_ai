from flask_login import UserMixin
from datetime import datetime, timezone
from config.database import db

# ============================================================
# 1. CLASSE PARENTE GLOBAL : USER
# ============================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(20), nullable=True)
    actif = db.Column(db.Boolean, default=True)
    
    # Remplacement moderne recommandé de utcnow (obsolète en Python 3.12+)
    date_creation = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    derniere_connexion = db.Column(db.DateTime, nullable=True)
    photo = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # Champ discriminateur pour indiquer à SQLAlchemy la classe enfant associée
    role = db.Column(db.String(20), default="candidat", nullable=False) 

    # Configuration du mappage polymorphique parent
    __mapper_args__ = {
        "polymorphic_on": role,
    }

    def est_recruteur(self):
        return self.role == "recruteur"
    
    def est_candidat(self):
        return self.role == "candidat"
    
    def est_employe(self):
        return self.role == "employe"

    def __repr__(self):
        return f"<User {self.email} - Rôle: {self.role}>"


# ============================================================
# 2. CLASSE ENFANT EXCLUSIVE : CANDIDAT
# ============================================================
class Candidat(User):
    __tablename__ = "candidats"

    # Clé primaire liée à la table parente via une contrainte de cascade
    id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Champ spécifique d'affectation si le candidat est plus tard embauché / retenu
    departement_id = db.Column(
        db.Integer, 
        db.ForeignKey("departements.id", ondelete="SET NULL"), 
        nullable=True
    )

    # Identité polymorphique associée
    __mapper_args__ = {
        "polymorphic_identity": "candidat",
    }


# ============================================================
# 3. CLASSE ENFANT EXCLUSIVE : RECRUTEUR
# ============================================================
class Recruteur(User):
    __tablename__ = "recruteurs"

    id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # Déplacement de la clé étrangère d'entreprise : Uniquement pour les recruteurs
    entreprise_id = db.Column(
        db.Integer, 
        db.ForeignKey("entreprises.id", ondelete="SET NULL"), 
        nullable=True # Mis à True temporairement pour l'étape d'inscription initiale, vérifié par la contrainte ci-dessous
    )

    # Sécurisation : Déplacement logique de la contrainte métier au niveau de la table enfant
    __table_args__ = (
        db.CheckConstraint(
            "entreprise_id IS NOT NULL",
            name="check_recruteur_has_entreprise_strict"
        ),
    )

    # Relation ORM propre transférée à l'enfant
    entreprise = db.relationship("Entreprise", back_populates="employes")

    # Identité polymorphique associée
    __mapper_args__ = {
        "polymorphic_identity": "recruteur",
    }
