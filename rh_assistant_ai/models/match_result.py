from datetime import datetime

from config.database import db


class MatchResult(db.Model):

    __tablename__ = "match_results"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    score = db.Column(
        db.Float,
        nullable=False
    )

    matching_skills = db.Column(
        db.Text,
        nullable=True
    )

    missing_skills = db.Column(
        db.Text,
        nullable=True
    )

    recommendation = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    cv_id = db.Column(
        db.Integer,
        db.ForeignKey("cvs.id"),
        nullable=False
    )

    offre_id = db.Column(
        db.Integer,
        db.ForeignKey("offres.id"),
        nullable=False
    )