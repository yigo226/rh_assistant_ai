from datetime import datetime

from config.database import db


class Offre(db.Model):

    __tablename__ = "offres"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    titre = db.Column(
        db.String(255),
        nullable=False
    )

    entreprise = db.Column(
        db.String(255),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    contenu_texte = db.Column(
        db.Text,
        nullable=True
    )

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "offres",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<Offre {self.titre}>"