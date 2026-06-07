from datetime import datetime

from config.database import db


class CVAnalysis(db.Model):

    __tablename__ = "cv_analyses"

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

    score = db.Column(
        db.Float,
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

    cv = db.relationship(
        "CV",
        backref=db.backref(
            "analyses",
            lazy=True
        )
    )