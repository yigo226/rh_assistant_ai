from datetime import datetime, timezone
from config.database import db

class Offre(db.Model):
    __tablename__ = "offres"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(255), nullable=False)
    entreprise = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=False)
    
    # Ajouts indispensables pour l'upload du fichier PDF de l'offre (comme pour le CV)
    nom_fichier = db.Column(db.String(255), nullable=False)
    chemin_fichier = db.Column(db.String(500), nullable=False)
    contenu_texte = db.Column(db.Text, nullable=True)

    # Correction de la date avec fuseau horaire UTC moderne
    date_creation = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Clé étrangère sécurisée avec suppression en cascade
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Un utilisateur peut avoir PLUSIEURS offres (contrairement au CV qui est unique)
    # On garde uselist=True implicite (pas besoin de le spécifier), mais on gère les orphelins.
    user = db.relationship(
        "User",
        backref=db.backref(
            "offres",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    # relation bidirectionnel avec OffreAnalyser
    analyse = db.relationship(
    "OffreAnalyser",
    back_populates="offre",
    uselist=False,
    cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Offre {self.titre}>"
