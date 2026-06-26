from datetime import datetime, timezone
from config.database import db

class Candidature(db.Model):
    """
    Table centrale représentant un candidat ayant postulé ou été évalué 
    pour une offre spécifique. Elle centralise les scores et le suivi RH.
    """
    __tablename__ = "candidatures"

    id = db.Column(db.Integer, primary_key=True)
    
    # Suivi du processus de recrutement (Étape clé pour le recruteur)
    # Valeurs possibles : 'a_letude', 'entretien', 'retenu', 'refuse'
    statut = db.Column(db.String(30), default="a_letude", nullable=False)
    
    # Métriques issues de votre service de matching
    score = db.Column(db.Float, nullable=False)
    matching_skills = db.Column(db.JSON, nullable=True)
    missing_skills = db.Column(db.JSON, nullable=True)
    extra_skills = db.Column(db.JSON, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # LES TRIPLETS DE LIAISONS (Clés étrangères indispensables)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cv_analyser_id = db.Column(db.Integer, db.ForeignKey("cv_analyses.id", ondelete="CASCADE"), nullable=False)
    offre_analyser_id = db.Column(db.Integer, db.ForeignKey("offre_analyses.id", ondelete="CASCADE"), nullable=False)

    # Relations ORM pour naviguer facilement d'un objet à l'autre en Python
    candidat = db.relationship("User", foreign_keys=[user_id], backref="mes_postulations")
    cv_analyse = db.relationship("CVAnalyser", foreign_keys=[cv_analyser_id])
    offre_analyse = db.relationship("OffreAnalyser", foreign_keys=[offre_analyser_id])

    def __repr__(self):
        return f"<Candidature ID={self.id} Profil={self.user_id} -> OffreAnalyse={self.offre_analyser_id} Score={self.score}%>"
