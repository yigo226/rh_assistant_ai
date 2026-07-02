from flask_login import UserMixin
from datetime import datetime, timezone
from config.database import db

# ============================================================
from flask_login import UserMixin
from datetime import datetime, timezone
from config.database import db

# ============================================================
# 1. CLASSE PARENTE : UTILISATEUR
# ============================================================
class Utilisateur(UserMixin, db.Model):
    # Changement du nom de la table en français
    __tablename__ = "utilisateurs"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(20), nullable=True)
    actif = db.Column(db.Boolean, default=True)
    
    # Gestion du temps UTC moderne
    date_creation = db.Column(
        db.DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    derniere_connexion = db.Column(db.DateTime(timezone=True), nullable=True)
    photo = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # Champ discriminateur pour l'héritage
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
        return f"<Utilisateur {self.email} - Rôle: {self.role}>"


# ============================================================
# 2. CLASSE ENFANT EXCLUSIVE : CANDIDAT
# ============================================================
class Candidat(Utilisateur):
    __tablename__ = "candidats"

    # Clé primaire liée à la table parente via une contrainte de cascade
    id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True)
    
    cvs = db.relationship(
        "CV", 
        back_populates="candidat", 
        cascade="all, delete-orphan"
    )

    @property
    def candidatures(self):
        liste = []
        for mon_cv in self.cvs:
            liste.extend(mon_cv.candidatures)
        return liste

    # Identité polymorphique associée
    __mapper_args__ = {
        "polymorphic_identity": "candidat",
    }

    def __repr__(self):
        return f"<Candidat ID={self.id} Email={self.email}>"


# ============================================================
# 3. CLASSE ENFANT EXCLUSIVE : RECRUTEUR
# ============================================================
class Recruteur(Utilisateur):
    __tablename__ = "recruteurs"

    id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True)

    # Déplacement de la clé étrangère d'entreprise : Uniquement pour les recruteurs
    entreprise_id = db.Column(
        db.Integer, 
        db.ForeignKey("entreprises.id", ondelete="SET NULL"), 
        nullable=True # Mis à True temporairement pour l'étape d'inscription initiale, vérifié par la contrainte ci-dessous
    )
    offres_publiees = db.relationship(
        "Offre", 
        back_populates="recruteur", 
        cascade="all, delete-orphan"
    )


    # Relation ORM propre transférée à l'enfant
    entreprise = db.relationship("Entreprise", back_populates="employes")

    # Sécurisation : Déplacement logique de la contrainte métier au niveau de la table enfant
    __table_args__ = (
        db.CheckConstraint(
            "entreprise_id IS NOT NULL",
            name="check_recruteur_has_entreprise_strict"
        ),
    )


    # Identité polymorphique associée
    __mapper_args__ = {
        "polymorphic_identity": "recruteur",
    }
