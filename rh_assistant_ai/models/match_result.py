from datetime import datetime

from config.database import db


class MatchResult(db.Model):

    __tablename__ = "match_results"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    cv_analyser_id = db.Column(
        db.Integer,
        db.ForeignKey("cv_analyses.id"),
        nullable=False
    )

    offre_analyser_id = db.Column(
        db.Integer,
        db.ForeignKey("offre_analyses.id"),
        nullable=False
    )

    score = db.Column(
        db.Float,
        nullable=False
    )

    matching_skills = db.Column(
        db.JSON,
        nullable=True
    )

    missing_skills = db.Column(
        db.JSON,
        nullable=True
    )

    extra_skills = db.Column(
        db.JSON,
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

    user = db.relationship("User", foreign_keys=[user_id])
    cv_analyser = db.relationship("CVAnalyser", foreign_keys=[cv_analyser_id])
    offre_analyser = db.relationship("OffreAnalyser", foreign_keys=[offre_analyser_id])


