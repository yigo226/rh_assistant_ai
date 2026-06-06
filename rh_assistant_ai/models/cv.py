from datetime import datetime

from config.database import db


class CV(db.Model):

    __tablename__ = "cvs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nom_fichier = db.Column(
        db.String(255),
        nullable=False
    )

    chemin_fichier = db.Column(
        db.String(500),
        nullable=False
    )

    contenu_texte = db.Column(
        db.Text,
        nullable=True
    )

    date_upload = db.Column(
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
            "cvs",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<CV {self.nom_fichier}>"