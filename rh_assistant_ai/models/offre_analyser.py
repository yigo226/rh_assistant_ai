from datetime import datetime

from config.database import db


class OffreAnalyser(db.Model):

    __tablename__ = "offre_analysis"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    skills = db.Column(
        db.Text,
        nullable=True
    )

    diplomas = db.Column(
        db.Text,
        nullable=True
    )

    experiences = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    offre_id = db.Column(
        db.Integer,
        db.ForeignKey("offres.id"),
        nullable=False
    )