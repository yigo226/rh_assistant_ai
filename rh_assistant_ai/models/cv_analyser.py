from datetime import datetime, timezone
from config.database import db

class CVAnalyser(db.Model):
    """
    Contient les informations extraites automatiquement d'un CV.
    Une analyse est associée à un seul CV.
    """
    __tablename__ = "cv_analyses"

    id = db.Column(db.Integer, primary_key=True)

    # Utilisation de JSON pour stocker de vraies listes Python proprement
    skills = db.Column(db.JSON, nullable=True)
    diplomas = db.Column(db.JSON, nullable=True)
    experiences = db.Column(db.JSON, nullable=True)
    
    score = db.Column(db.Float, nullable=True)

    # Correction de la date avec le fuseau horaire UTC moderne
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Clé étrangère sécurisée avec suppression en cascade automatique
    cv_id = db.Column(
        db.Integer,
        db.ForeignKey("cvs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True # Garantit la relation stricte 1-à-1 avec le CV
    )

    # Relation bidirectionnelle avec le modèle CV
    cv = db.relationship("CV", back_populates="analyse")

    def __repr__(self):
        return f"<CVAnalyser id={self.id} cv_id={self.cv_id}>"
