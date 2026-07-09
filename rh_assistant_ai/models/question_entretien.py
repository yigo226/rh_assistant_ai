from config.database import db

class QuestionEntretien(db.Model):

    __tablename__ = 'questions_entretien'

    id = db.Column(db.Integer, primary_key=True)

    # donner json contenant les 10 questions
    donnees_json = db.Column(db.Text, nullable=True)  # Stocke le JSON complet des questions générées


    # Clé étrangère connectée à la table offres
    offre_id = db.Column(db.Integer, db.ForeignKey('offres.id', ondelete='CASCADE'), nullable=False)
    
    # RECONSTRUCTION DE LA PROPRIÉTÉ MANQUANTE :
    offre = db.relationship('Offre', back_populates='questions')