from datetime import datetime, timezone
from config.database import db

from datetime import datetime, timezone
from config.database import db
from datetime import datetime, timezone
from config.database import db

# class Candidature(db.Model):
#     """
#     Représente l'action officielle du candidat qui valide son matching 
#     et postule auprès du recruteur pour une offre.
#     """
#     __tablename__ = "candidatures"

#     id = db.Column(db.Integer, primary_key=True)
    
#     # Valeurs de suivi RH : 'a_letude', 'entretien', 'retenu', 'refuse'
#     statut = db.Column(db.String(30), default="a_letude", nullable=False)
    
#     created_at = db.Column(
#         db.DateTime(timezone=True), 
#         default=lambda: datetime.now(timezone.utc), 
#         nullable=False
#     )

#     # 🟢 CORRECTION 1 : Remplacement de utilisateurs.id par candidats.id (liaison enfant stricte)
#     candidat_id = db.Column(
#         db.Integer, 
#         db.ForeignKey("candidats.id", ondelete="CASCADE"), 
#         nullable=False
#     )
    
#     # Identifiant de l'offre conservé pour indexation ultra-rapide des requêtes
#     offre_id = db.Column(
#         db.Integer, 
#         db.ForeignKey("offres.id", ondelete="CASCADE"), 
#         nullable=False
#     )
    
#     # Le pont vers les métriques privées de l'IA
#     match_result_id = db.Column(
#         db.Integer, 
#         db.ForeignKey("match_results.id", ondelete="CASCADE"), 
#         nullable=False
#     )

#     # 🟢 CORRECTION 2 : Transition complète des anciens backref vers des back_populates propres
#     candidat = db.relationship("Candidat", back_populates="candidatures", foreign_keys=[candidat_id])
#     offre = db.relationship("Offre", back_populates="candidatures", foreign_keys=[offre_id])
    
#     # Liaison bidirectionnelle avec le MatchResult
#     details_matching = db.relationship("MatchResult", back_populates="candidatures", foreign_keys=[match_result_id])

#     def __repr__(self):
#         return f"<Candidature ID={self.id} Candidat={self.candidat_id} Offre={self.offre_id} Statut={self.statut}>"

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

    # 🟢 Relations ORM bidirectionnelles
    offre = db.relationship("Offre", back_populates="candidatures", foreign_keys=[offre_id])
    cv = db.relationship("CV", back_populates="candidatures", foreign_keys=[cv_id])

    # 🟢 PROPRIÉTÉ MAGIQUE 1 : Remonte au candidat sans colonne physique redondante
    @property
    def candidat(self):
        """Retrouve le candidat propriétaire du CV attaché à cette candidature"""
        return self.cv.candidat if self.cv else None

    # 🟢 PROPRIÉTÉ MAGIQUE 2 : Retrouve le score IA sans stocker de clé supplémentaire
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
    
    # Informations de finalisation du contrat
    type_contrat = db.Column(db.String(50), nullable=False)       # CDI, CDD, Stage, Alternance
    salaire_propose = db.Column(db.Float, nullable=True)          
    date_debut = db.Column(db.Date, nullable=False)               

    # 🟢 LES DEUX SEULES CLÉS PHYSIQUES NÉCESSAIRES :
    # 1. On garde l'entreprise intacte pour filtrer le registre RH en un éclair
    entreprise_id = db.Column(db.Integer, db.ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False)
    
    # 2. Le nouveau lien direct vers la candidature officielle validée
    candidature_id = db.Column(db.Integer, db.ForeignKey("candidatures.id", ondelete="CASCADE"), nullable=False)

    # 🟢 Relations SQLAlchemy bidirectionnelles
    entreprise = db.relationship("Entreprise", back_populates="recrutements")
    candidature = db.relationship("Candidature")

    # 🟢 PROPRIÉTÉS VIRTUELLES (Pour naviguer facilement sans colonnes doublons)
    @property
    def candidat(self):
        """Remonte directement au candidat à travers la candidature"""
        return self.candidature.candidat if self.candidature else None

    @property
    def offre(self):
        """Remonte directement à l'offre à travers la candidature"""
        return self.candidature.offre if self.candidature else None

    @property
    def departement(self):
        """Remonte directement au département/service à travers l'offre de la candidature"""
        return self.candidature.offre.departement if (self.candidature and self.candidature.offre) else None

    @property
    def match_result(self):
        """Remonte directement aux scores de l'IA à travers la candidature"""
        return self.candidature.details_matching if self.candidature else None

    def __repr__(self):
        return f"<Recrutement ID={self.id} Entreprise={self.entreprise_id} Candidature={self.candidature_id}>"
