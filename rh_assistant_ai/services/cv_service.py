from services.nlp.preprocessing import clean_text

from services.nlp.skill_extractor import extract_skills

from services.nlp.diploma_extractor import extract_diplomas

from services.nlp.experience_extractor import extract_experience


def analyze_cv(text):

    text = clean_text(text)

    skills = extract_skills(text)

    diplomas = extract_diplomas(text)

    experiences = extract_experience(text)

    return {
        "skills": skills,
        "diplomas": diplomas,
        "experiences": experiences
    }