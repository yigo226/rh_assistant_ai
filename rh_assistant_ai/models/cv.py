
from datetime import datetime, timezone
from config.database import db

class CV(db.Model):
    __tablename__ = "cvs"

    id = db.Column(db.Integer, primary_key=True)
    nom_fichier = db.Column(db.String(255), nullable=False)
    chemin_fichier = db.Column(db.String(500), nullable=False)
    #contenu_texte = db.Column(db.Text, nullable=True)
    
    date_upload = db.Column(
        db.DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    est_actif = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    # 🟢 CORRECTION 1 : La clé étrangère pointe strictement sur la table candidats
    candidat_id = db.Column(
        db.Integer,
        db.ForeignKey("candidats.id", ondelete="CASCADE"),
        nullable=False,
        unique=False  # Permet de conserver l'historique de plusieurs fichiers par candidat
    )

    # 🟢 CORRECTION 2 : Remplacement de la relation User par la relation enfant Candidat (back_populates)
    candidat = db.relationship(
        "Candidat",
        back_populates="cvs"
    )

    candidatures = db.relationship("Candidature", back_populates="cv", cascade="all, delete-orphan")

    # Relation bidirectionnelle avec CVAnalyser
    analyse = db.relationship(
        "CVAnalyser",
        back_populates="cv",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CV {self.nom_fichier}>"
