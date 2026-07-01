from datetime import datetime, timezone
from config.database import db

class OffreAnalyser(db.Model):
    """
    Contient les informations extraites automatiquement d'une offre d'emploi.
    Une analyse est associée à une seule offre.
    """
    __tablename__ = "offre_analyses" # Correction du nom pour correspondre à cv_analyses

    id = db.Column(db.Integer, primary_key=True)

    competences = db.Column(db.JSON, nullable=True)
    diplomes = db.Column(db.JSON, nullable=True)
    experiences = db.Column(db.JSON, nullable=True)

    # Suivi temporel moderne en UTC
    date_creation = db.Column(
        db.DateTime(timezone=True),
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

    offre = db.relationship("Offre", back_populates="analyse")

    match_results = db.relationship(
        "MatchResult", 
        back_populates="offre_analyser", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AnalyseOffre id={self.id} offre_id={self.offre_id}>"
