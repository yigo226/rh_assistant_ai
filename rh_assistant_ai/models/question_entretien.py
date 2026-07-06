from config.database import db

class QuestionEntretien(db.Model):

    __tablename__ = 'questions_entretien'

    id = db.Column(db.Integer, primary_key=True)

    # Données de la question
    categorie = db.Column(db.String(50), nullable=True)  # Par exemple : "Compétences", "Expérience", "Culture d'entreprise"

    # UN SEUL CHAMP qui contient tout le JSON d'un coup (les 10 questions)
    donnees_json = db.Column(db.Text, nullable=True)  # Stocke le JSON complet des questions générées

    texte_question = db.Column(db.Text, nullable=True)  # Optionnel, peut être rempli à partir du JSON si nécessaire

    # Clé étrangère connectée à la table offres
    offre_id = db.Column(db.Integer, db.ForeignKey('offres.id', ondelete='CASCADE'), nullable=False)
    
    # RECONSTRUCTION DE LA PROPRIÉTÉ MANQUANTE :
    # C'est cette ligne exacte qui manquait et qui provoquait votre crash !
    offre = db.relationship('Offre', back_populates='questions')