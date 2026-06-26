from datetime import datetime, timezone

from models.user import User
from config.database import db


class Entreprise(db.Model):
    __tablename__ = "entreprises"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), unique=True, nullable=False)
    site_web = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Relations réciproques
    departements = db.relationship("Departement", backref="entreprise", cascade="all, delete-orphan")
    employes = db.relationship("User", foreign_keys="[User.entreprise_id]")

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
    offres = db.relationship("Offre", backref="departement")



def embaucher_candidat(id_candidat, id_departement, id_entreprise):
    candidat = User.query.get(id_candidat)
    
    if candidat:
        # Le candidat est rattaché à l'entreprise et au département cible
        candidat.entreprise_id = id_entreprise
        candidat.departement_id = id_departement
        
        # Optionnel : Vous pouvez changer son rôle en "employe" ou le laisser "candidat" 
        # selon la logique des permissions de votre application
        # candidat.role = "employe" 
        
        db.session.commit()
        print(f"{candidat.prenom} a été intégré au département avec succès !")
