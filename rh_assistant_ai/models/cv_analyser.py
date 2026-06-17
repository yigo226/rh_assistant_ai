from datetime import datetime

from config.database import db

class CVAnalyser(db.Model):

    """
    Contient les informations extraites automatiquement d'un CV.
    Une analyse est associée à un seul CV.
    """

    __tablename__ = "cv_analyses"

    # Identifiant unique de l'analyse
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Liste des compétences détectées
    skills = db.Column(
        db.JSON,
        nullable=True
    )

    # Liste des diplômes détectés
    diplomas = db.Column(
        db.JSON,
        nullable=True
    )

    # Liste des expériences détectées
    experiences = db.Column(
        db.JSON,
        nullable=True
    )

    # Score global de l'analyse (optionnel)
    score = db.Column(
        db.Float,
        nullable=True
    )

    # Date de création de l'analyse
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Clé étrangère vers le CV analysé
    cv_id = db.Column(
        db.Integer,
        db.ForeignKey("cvs.id"),
        nullable=False
    )

    # Relation avec le CV
    cv = db.relationship(
        "CV",
        back_populates="analyse"
    )
    