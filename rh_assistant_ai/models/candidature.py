from datetime import datetime, timezone
from config.database import db


class Candidature(db.Model):
    """
    Représente l'action officielle d'un candidat qui postule à une offre 
    d'emploi spécifique en y attachant un de ses CV.
    """
    __tablename__ = "candidatures"

    id = db.Column(db.Integer, primary_key=True)
    
    # Suivi RH : 'a_letude', 'entretien', 'retenu', 'refuse'
    statut = db.Column(db.String(30), default="a_letude", nullable=False)
    
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # 1. Le lien direct vers l'offre (Indispensable pour le tableau du recruteur)
    offre_id = db.Column(
        db.Integer, 
        db.ForeignKey("offres.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # 2. Le lien direct vers le CV soumis (Permet de retrouver le candidat et l'historique)
    cv_id = db.Column(
        db.Integer, 
        db.ForeignKey("cvs.id", ondelete="CASCADE"), 
        nullable=False
    )

    # Relations bidirectionnelles
    offre = db.relationship("Offre", back_populates="candidatures", foreign_keys=[offre_id])
    cv = db.relationship("CV", back_populates="candidatures", foreign_keys=[cv_id])

    entretiens = db.relationship(
        "Entretien",
        back_populates="candidature",
        cascade="all, delete-orphan",
        order_by="Entretien.date_creation.desc()" # Le dernier planifié apparaît en premier
    )


    # Remonte au candidat sans colonne physique redondante
    @property
    def candidat(self):
        """Retrouve le candidat propriétaire du CV attaché à cette candidature"""
        return self.cv.candidat if self.cv else None

    # Retrouve le score IA sans stocker de clé supplémentaire
    @property
    def details_matching(self):
        """Retrouve le résultat du matching IA entre ce CV et cette offre"""
        if self.cv and self.cv.analyse and self.offre and self.offre.analyse:
            from models import MatchResult
            return MatchResult.query.filter_by(
                cv_analyser_id=self.cv.analyse.id,
                offre_analyser_id=self.offre.analyse.id
            ).first()
        return None

    def __repr__(self):
        return f"<Candidature ID={self.id} Offre={self.offre_id} Statut={self.statut}>"


class LesRecrutEntreprise(db.Model):
    __tablename__ = "les_recrut_entreprise"

    id = db.Column(db.Integer, primary_key=True)
    date_recrutement = db.Column(
        db.DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    
    # Détails du contrat conclu
    type_contrat = db.Column(db.String(50), nullable=False) # CDI, CDD, etc.
    salaire_propose = db.Column(db.Float, nullable=True)          
    date_debut = db.Column(db.Date, nullable=False)               

    candidature_id = db.Column(
        db.Integer, 
        db.ForeignKey("candidatures.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )

    # Relation SQLAlchemy vers la candidature
    candidature = db.relationship("Candidature", backref=db.backref("recrutement", uselist=False))

    @property
    def offre(self):
        return self.candidature.offre if self.candidature else None

    @property
    def departement(self):
        return self.candidature.offre.departement if (self.candidature and self.candidature.offre) else None

    @property
    def entreprise(self):
        return self.candidature.offre.departement.entreprise if (self.candidature and self.candidature.offre and self.candidature.offre.departement) else None

    @property
    def candidat(self):
        return self.candidature.cv.candidat if (self.candidature and self.candidature.cv) else None

    @property
    def match_result(self):
        return self.candidature.details_matching if self.candidature else None


class Entretien(db.Model):
    __tablename__ = "entretiens"

    id = db.Column(db.Integer, primary_key=True)
    
    # Éléments temporels et logistiques collectés
    date_rendezvous = db.Column(db.Date, nullable=False)
    heure_rendezvous = db.Column(db.Time, nullable=False)
    lieu = db.Column(db.String(255), nullable=False) # Bureau physique ou lien Teams/Zoom
    
    # Suivi de la session d'entretien : 'planifie', 'effectue', 'annule', 'reporte'
    statut_entretien = db.Column(db.String(30), default="planifie", nullable=False)
    
    # Commentaire ou note du recruteur (ex: "Entretien technique 1er tour")
    notes = db.Column(db.Text, nullable=True)
    
    date_creation = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # LIAISON CLÉ UNIQUE : Relié à la candidature
    candidature_id = db.Column(
        db.Integer,
        db.ForeignKey("candidatures.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relation ORM pour naviguer facilement
    candidature = db.relationship("Candidature", back_populates="entretiens")

    def __repr__(self):
        return f"<Entretien ID={self.id} Date={self.date_rendezvous} Statut={self.statut_entretien}>"
