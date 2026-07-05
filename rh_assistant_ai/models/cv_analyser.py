from datetime import datetime, timezone
from config.database import db

class CVAnalyser(db.Model):
    """
    Contient les informations extraites automatiquement d'un CV.
    Une analyse est associée à un seul CV.
    """
    __tablename__ = "cv_analyses"

    id = db.Column(db.Integer, primary_key=True)
    
    contenu_texte = db.Column(db.Text, nullable=True)

    competences = db.Column(db.JSON, nullable=True)
    diplomes = db.Column(db.JSON, nullable=True)
    experiences = db.Column(db.JSON, nullable=True)
    
    # Suivi temporel moderne en UTC
    created_at = db.Column(
        db.DateTime(timezone=True),
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

    match_results = db.relationship(
        "MatchResult", 
        back_populates="cv_analyser", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CVAnalyser id={self.id} cv_id={self.cv_id}>"
