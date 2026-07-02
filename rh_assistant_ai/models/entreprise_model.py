from datetime import datetime, timezone

from models.utilisateur import Utilisateur
from config.database import db

class Entreprise(db.Model):
    __tablename__ = "entreprises"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), unique=True, nullable=False)
    site_web = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # 1. Vos départements/services
    departements = db.relationship("Departement", backref="entreprise", cascade="all, delete-orphan")
    
    # 2. Vos collaborateurs RH existants (Vos recruteurs connectés)
    employes = db.relationship("Recruteur", back_populates="entreprise")

    # 3.  RELATION DISTINCTE : Le registre des recrutements IA validés
    # On la nomme "recrutements" pour qu'elle ne vienne pas écraser vos recruteurs
    recrutements = db.relationship("LesRecrutEntreprise", back_populates="entreprise", cascade="all, delete-orphan")
   
    # Dans la classe Entreprise
    @property
    def recrutements(self):
        """
        Va chercher dynamiquement tous les recrutements conclus pour cette entreprise 
        en passant par les départements et les offres.
        """
        from models import LesRecrutEntreprise, Candidature, Offre, Departement # À adapter selon vos imports
        
        return LesRecrutEntreprise.query\
            .join(Candidature)\
            .join(Offre)\
            .join(Departement)\
            .filter(Departement.entreprise_id == self.id)\
            .all()


class Departement(db.Model):
    __tablename__ = "departements"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False) # ex: "R&D", "Ressources Humaines"
    
    # Clé étrangère vers l'entreprise
    entreprise_id = db.Column(db.Integer, 
                                db.ForeignKey("entreprises.id", 
                                ondelete="CASCADE"), 
                                nullable=False)

    # Relation vers les offres
    offres = db.relationship("Offre", back_populates="departement")


def embaucher_candidat(id_candidat, id_departement, id_entreprise):
    candidat = Utilisateur.query.get(id_candidat)
    
    if candidat:
        # Le candidat est rattaché à l'entreprise et au département cible
        candidat.entreprise_id = id_entreprise
        candidat.departement_id = id_departement
        
        db.session.commit()
        print(f"{candidat.prenom} a été intégré au département avec succès !")
