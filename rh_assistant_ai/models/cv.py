from datetime import datetime, timezone
from config.database import db

class CV(db.Model):
    __tablename__ = "cvs"

    id = db.Column(db.Integer, primary_key=True)
    nom_fichier = db.Column(db.String(255), nullable=False)
    chemin_fichier = db.Column(db.String(500), nullable=False)
    contenu_texte = db.Column(db.Text, nullable=True)
    
    date_upload = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # 1. UNIQUE=TRUE empêche la base de données d'accepter deux fois le même user_id
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=False  
    )

    # 2. USELIST=FALSE transforme la liste d'objets en un objet unique côté Python
    user = db.relationship(
        "User",
        backref=db.backref(
            "cv", # Renommé en "cv" (au singulier) pour correspondre à la logique
            lazy=True,
            uselist=False, 
            cascade="all, delete-orphan"
        )
    )

    # relation bidirectionnel avec CVAnalyser
    analyse = db.relationship(
        "CVAnalyser",
        back_populates="cv",
        uselist=False,
        cascade="all, delete-orphan"
    )

    est_actif = db.Column(
        db.Boolean,
        default= True,
        nullable= False
    )

    def __repr__(self):
        return f"<CV {self.nom_fichier}>"
