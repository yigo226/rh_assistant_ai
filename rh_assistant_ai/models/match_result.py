
from datetime import datetime, timezone
from config.database import db

class MatchResult(db.Model):
    __tablename__ = "match_results"

    id = db.Column(db.Integer, primary_key=True)

    # 🟢 CORRECTION 1 : Suppression physique de user_id pour éviter la redondance
    # L'ID du candidat est retrouvé proprement à travers la chaîne : MatchResult -> CVAnalyser -> CV -> Candidat

    cv_analyser_id = db.Column(
        db.Integer,
        db.ForeignKey("cv_analyses.id", ondelete="CASCADE"),
        nullable=False
    )

    offre_analyser_id = db.Column(
        db.Integer,
        db.ForeignKey("offre_analyses.id", ondelete="CASCADE"),
        nullable=False
    )

    score = db.Column(db.Float, nullable=False)
    matching_skills = db.Column(db.JSON, nullable=True)
    missing_skills = db.Column(db.JSON, nullable=True)
    extra_skills = db.Column(db.JSON, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # 🟢 CORRECTION 2 : Harmonisation des relations en mode bidirectionnel (back_populates)
    cv_analyser = db.relationship("CVAnalyser", back_populates="match_results", foreign_keys=[cv_analyser_id])
    offre_analyser = db.relationship("OffreAnalyser", back_populates="match_results", foreign_keys=[offre_analyser_id])
    
    #candidatures = db.relationship("Candidature", back_populates="details_matching", cascade="all, delete-orphan")

    # 🟢 AJOUT : Propriété magique pour remonter au candidat sans complexité
    @property
    def candidat(self):
        """Remonte automatiquement jusqu'à l'objet Candidat à travers l'analyse du CV"""
        if self.cv_analyser and self.cv_analyser.cv:
            return self.cv_analyser.cv.candidat
        return None

    def __repr__(self):
        return f"<MatchResult ID={self.id} Score={self.score}%>"


