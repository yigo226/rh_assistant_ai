
from datetime import datetime, timezone
from config.database import db

class MatchResult(db.Model):
    __tablename__ = "match_results"

    id = db.Column(db.Integer, primary_key=True)

    # Liaisons physiques existantes
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

    # 🟢 COMPLETION & TRADUCTION : Les 3 dimensions du matching (Compétences, Diplômes, Expériences)
    
    # 1. Le bloc Compétences
    competences_validees = db.Column(db.JSON, nullable=True) # matching_skills
    competences_manquantes = db.Column(db.JSON, nullable=True) # missing_skills
    competences_bonus = db.Column(db.JSON, nullable=True) # extra_skills

    # 2. Le bloc Diplômes (🟢 Ajouté)
    diplomes_valides = db.Column(db.JSON, nullable=True)
    diplomes_manquants = db.Column(db.JSON, nullable=True)

    # 3. Le bloc Expériences (🟢 Ajouté)
    experiences_validees = db.Column(db.JSON, nullable=True)
    experiences_manquantes = db.Column(db.JSON, nullable=True)
    
    # Métriques globales
    score = db.Column(db.Float, nullable=False)
    recommandation = db.Column(db.Text, nullable=True) # recommendation
    
    date_creation = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relations de lecture bidirectionnelles (Mises à jour avec le nouveau nom de classe back_populates)
    cv_analyser = db.relationship("CVAnalyser", back_populates="match_results", foreign_keys=[cv_analyser_id])
    offre_analyser = db.relationship("OffreAnalyser", back_populates="match_results", foreign_keys=[offre_analyser_id])

    # Propriété virtuelle pour remonter au candidat sans redondance
    @property
    def candidat(self):
        """Remonte automatiquement jusqu'à l'objet Candidat à travers l'analyse du CV"""
        if self.cv_analyser and self.cv_analyser.cv:
            return self.cv_analyser.cv.candidat
        return None

    def __repr__(self):
        return f"<ResultatMatch ID={self.id} Score={self.score}%>"
