from app.models.sentence_model import Sentence


def get_sentences(data):
    project_id = data['project_id']
    sentences = Sentence.query.filter_by(project_id=project_id).order_by(Sentence.id).all()
    return sentences


