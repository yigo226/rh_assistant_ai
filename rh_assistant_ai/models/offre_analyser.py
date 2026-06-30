from datetime import datetime, timezone
from config.database import db

class OffreAnalyser(db.Model):
    """
    Contient les informations extraites automatiquement d'une offre d'emploi.
    Une analyse est associée à une seule offre.
    """
    __tablename__ = "offre_analyses" # Correction du nom pour correspondre à cv_analyses

    id = db.Column(db.Integer, primary_key=True)

    # Harmonisation au format JSON pour stocker les listes de critères de l'offre
    skills = db.Column(db.JSON, nullable=True)
    diplomas = db.Column(db.JSON, nullable=True)
    experiences = db.Column(db.JSON, nullable=True)

    # Correction de la date
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Clé étrangère sécurisée avec suppression en cascade automatique
    offre_id = db.Column(
        db.Integer,
        db.ForeignKey("offres.id", ondelete="CASCADE"),
        nullable=False,
        unique=True # Une offre d'emploi n'a qu'une seule analyse de texte associée
    )

    # Ajout de la relation réciproque vers le modèle Offre 
    offre = db.relationship("Offre", back_populates="analyse")


    match_results = db.relationship(
        "MatchResult", 
        back_populates="offre_analyser", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<OffreAnalyser id={self.id} offre_id={self.offre_id}>"
