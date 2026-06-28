from datetime import datetime, timezone
from config.database import db

from datetime import datetime, timezone
from config.database import db

class Candidature(db.Model):
    """
    Représente l'action officielle du candidat qui valide son matching 
    et postule auprès du recruteur pour une offre.
    """
    __tablename__ = "candidatures"

    id = db.Column(db.Integer, primary_key=True)
    
    # Le suivi RH 
    # Valeurs : 'a_letude', 'entretien', 'retenu', 'refuse'
    statut = db.Column(db.String(30), default="a_letude", nullable=False)
    
    created_at = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Clés étrangères indispensables pour cibler le contexte
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    offre_id = db.Column(db.Integer, db.ForeignKey("offres.id", ondelete="CASCADE"), nullable=False)
    
    # LE PONT RELATIONNEL : Permet au recruteur de remonter aux données de matching privées
    match_result_id = db.Column(
        db.Integer, 
        db.ForeignKey("match_results.id", ondelete="CASCADE"), 
        nullable=False
    )

    # Relations de lecture pour naviguer facilement en Python
    candidat = db.relationship("User", foreign_keys=[user_id], backref="candidatures")
    offre = db.relationship("Offre", foreign_keys=[offre_id], backref="candidatures")
    details_matching = db.relationship("MatchResult", foreign_keys=[match_result_id])

    def __repr__(self):
        return f"<Candidature ID={self.id} User={self.user_id} Offre={self.offre_id} Statut={self.statut}>"


class LesRecrutEntreprise(db.Model):
    __tablename__ = "les_recrut_entreprise"

    id = db.Column(db.Integer, primary_key=True)
    date_recrutement = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    #  NOUVEAUX CHAMPS COMPREHENSIFS
    type_contrat = db.Column(db.String(50), nullable=False)       # CDI, CDD, Stage, Alternance
    salaire_propose = db.Column(db.Float, nullable=True)          # Salaire brut annuel ou mensuel
    date_debut = db.Column(db.Date, nullable=False)               # Date de début de contrat
    
    # Liaisons contextuelles existantes
    entreprise_id = db.Column(db.Integer, db.ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False)
    offre_id = db.Column(db.Integer, db.ForeignKey("offres.id", ondelete="CASCADE"), nullable=False)
    candidat_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_result_id = db.Column(db.Integer, db.ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True)

    # Relations de confort
    entreprise = db.relationship("Entreprise")
    offre = db.relationship("Offre")
    candidat = db.relationship("User")
