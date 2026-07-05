from datetime import datetime, timezone
from config.database import db


class Offre(db.Model):
    __tablename__ = "offres"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(255), nullable=False)
    #entreprise = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=False)
    
    # Éléments indispensables pour l'upload du fichier PDF de l'offre
    nom_fichier = db.Column(db.String(255), nullable=False)
    chemin_fichier = db.Column(db.String(500), nullable=False)
    
    #contenu_texte = db.Column(db.Text, nullable=True)

    # Suivi temporel moderne en UTC
    date_creation = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    date_limite = db.Column(db.DateTime(timezone=True), nullable=False)

    #  clé étrangère pointe sur la table recruteurs
    recruteur_id = db.Column(
        db.Integer,
        db.ForeignKey("recruteurs.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Clé vers la table 'departements'
    departement_id = db.Column(
        db.Integer, 
        db.ForeignKey("departements.id", ondelete="CASCADE"), 
        nullable=False 
    )

    #  pointer  sur 'offres_publiees'
    recruteur = db.relationship(
        "Recruteur",
        back_populates="offres_publiees"
    )

    # Relation vers le Département
    departement = db.relationship(
        "Departement",
        back_populates="offres"
    )

    # Relation bidirectionnelle avec OffreAnalyser
    analyse = db.relationship(
        "OffreAnalyser",
        back_populates="offre",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Relation bidirectionnelle avec Candidature
    candidatures = db.relationship(
        "Candidature",
        back_populates="offre",
        cascade="all, delete-orphan"
    )

    @property
    def total_postulants(self):
        # Protection si la relation candidatures n'est pas encore initialisée
        return len(self.candidatures) if self.candidatures else 0
    
    # À ajouter dans votre classe Offre (models.py) si ce n'est pas déjà fait :
    @property
    def nom_entreprise(self):
        """Remonte dynamiquement le nom de l'entreprise sans colonne doublon"""
        return self.departement.entreprise.nom if (self.departement and self.departement.entreprise) else "Inconnue"

    
    def __repr__(self):
        return f"<Offre {self.titre}>"
