import datetime
import re

from flask import jsonify
from sqlalchemy import func

from app.models.annotation_model import Annotation
from app.models.user_model import User

from .. import db
from ..models.project_model import Project
import xml.etree.ElementTree as ET
import html
import re
import datetime
from ..models.sentence_model import Sentence

    # def create_project(data, current_user):
    #     new_project = Project(
    #         title=data['title'],
    #         description=data['description'],
    #         language=data['language'],
    #         file_text=data['file_text'],
    #         uploaded_by=current_user,
    #         uploaded_on=datetime.datetime.now()
    #     )

    #     db.session.add(new_project)
    #     db.session.flush()
    #     sentences = split_into_sentences(data['file_text'])
    #     for sentence_text in sentences:
    #         sentence = Sentence(content=sentence_text.strip(), project_id=new_project.id, is_annotated=False)
    #         db.session.add(sentence)

    #     db.session.commit()
    #     return new_project


import xml.etree.ElementTree as ET
import html
import re
import datetime

def create_project(data, current_user):
    print("Creating Project...")  # Debugging

    new_project = Project(
        title=data.get('title', 'Untitled Project'),
        description=data.get('description', ''),
        language=data.get('language', 'Unknown'),
        file_text=data.get('file_text', ''),  # Storing the raw content
        uploaded_by=current_user,
        uploaded_on=datetime.datetime.now()
    )

    db.session.add(new_project)
    db.session.flush()  # Get new_project.id before committing

    file_text = data['file_text'].strip()

    # Check if input is XML or plain text
    is_xml = file_text.startswith("<") and file_text.endswith(">")

    sentence_counter = 1  # Start numbering from 1 for this project

    if is_xml:
        print("Detected XML input.")  # Debugging
        try:
            root = ET.fromstring(file_text)  # Parse XML
            print("XML Parsed Successfully.")  # Debugging

            # Check if this is the NEW format (Root is <project>)
            if root.tag == "project":
                print("Processing NEW Annotated XML format.")  # Debugging
                sentences_root = root.find("./sentences")

                if sentences_root is None:
                    raise ValueError("Invalid XML: <sentences> tag missing inside <project>.")

                for sentence_elem in sentences_root.findall(".//sentence"):
                    raw_text = sentence_elem.get("text", "").strip()
                    is_annotated = sentence_elem.get("isAnnotated") == "True"

                    print(f"Processing Sentence {sentence_counter}: {raw_text}")

                    sentence = Sentence(
                        sentence_number=sentence_counter,  # Ensure numbering within the project
                        content=raw_text,
                        is_annotated=is_annotated,
                        project_id=new_project.id
                    )
                    db.session.add(sentence)
                    db.session.flush()  # Ensure sentence.id is generated

                    annotations_elem = sentence_elem.find("annotations")
                    if annotations_elem is not None:
                        for annotation_elem in annotations_elem.findall("annotation"):
                            annotation_id = annotation_elem.get("id")
                            annotated_word = annotation_elem.get("word_phrase")
                            annotation_type = annotation_elem.get("annotation")
                            annotated_by = annotation_elem.get("annotated_by")
                            annotated_on = annotation_elem.get("annotated_on")

                            print(f"Saving Annotation ID {annotation_id}: {annotation_type} -> {annotated_word}")

                            annotation_record = Annotation(
                                word_phrase=annotated_word,
                                annotation=annotation_type,
                                annotated_by=annotated_by,
                                annotated_on=datetime.datetime.strptime(annotated_on, "%Y-%m-%d"),
                                sentence_id=sentence.id,  # Link to newly assigned ID
                                project_id=new_project.id
                            )
                            db.session.add(annotation_record)

                    sentence_counter += 1  # Increment for the next sentence in this project

            else:
                # OLD LOGIC: Process existing XML format
                print("Processing OLD XML format.")  # Debugging
                for sentence_elem in root.findall(".//sentence"):
                    raw_text = sentence_elem.get("text", "").strip()
                    is_annotated = sentence_elem.get("isAnnotated") == "True"

                    print(f"Processing Sentence {sentence_counter}: {raw_text}")

                    decoded_text = html.unescape(raw_text)
                    annotations = []

                    def annotation_extractor(match):
                        annotation_type = match.group(1)
                        attributes = match.group(2)
                        annotated_word = html.unescape(match.group(3))

                        annotation_attrs = dict(re.findall(r'(\w+)="(.*?)"', attributes))
                        annotations.append({
                            'type': annotation_type,
                            'text': annotated_word,
                            'attributes': annotation_attrs
                        })

                        print(f"Extracted Annotation: {annotation_type} -> {annotated_word}")
                        return annotated_word

                    clean_text = re.sub(r'<(\w+)(.*?)>(.*?)</\1>', annotation_extractor, decoded_text)
                    print(f"Cleaned Sentence {sentence_counter}: {clean_text}")

                    sentence = Sentence(
                        sentence_number=sentence_counter,
                        content=clean_text,
                        is_annotated=is_annotated,
                        project_id=new_project.id
                    )
                    db.session.add(sentence)
                    db.session.flush()

                    if is_annotated:
                        for annotation in annotations:
                            annotation_id = annotation['attributes'].get('ID')
                            annotation_type = annotation['type']
                            annotation_subtype = annotation['attributes'].get('TYPE', '')
                            annotated_word = annotation['text']

                            print(f"Saving Annotation ID {annotation_id}: {annotation_type} ({annotation_subtype}) -> {annotated_word}")

                            annotation_record = Annotation(
                                word_phrase=annotated_word,
                                annotation=f"{annotation_type} ({annotation_subtype})",
                                annotated_by=current_user,
                                annotated_on=datetime.datetime.now(),
                                sentence_id=sentence.id,
                                project_id=new_project.id
                            )
                            db.session.add(annotation_record)

                    sentence_counter += 1  # Increment for next sentence

        except ET.ParseError as e:
            db.session.rollback()
            print(f"XML Parsing Error: {str(e)}")  # Debugging
            return jsonify({'message': 'Invalid XML format'}), 400
        except Exception as e:
            db.session.rollback()
            print(f"Unexpected Error: {str(e)}")  # Debugging
            return jsonify({'message': f'An error occurred: {str(e)}'}), 500


    else:
        print("Detected Plain Text input.")  # Debugging
        sentences = split_into_sentences(file_text)

        sentence_counter = 1  # Ensure numbering starts from 1 for each new project

        for sentence_text in sentences:  
            clean_text = sentence_text.strip()
            print(f"Saving Sentence {sentence_counter}: {clean_text}")

            sentence = Sentence(
                sentence_number=sentence_counter,  # Assign sequential number
                content=clean_text,
                is_annotated=False,
                project_id=new_project.id
            )
            db.session.add(sentence)

            sentence_counter += 1 

    db.session.commit()
    print("Project Successfully Created!")  # Debugging
    return new_project


def delete_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return {"error": "Project not found"}, 404

    try:
        # Delete annotations associated with each sentence in the project
        sentences = Sentence.query.filter_by(project_id=project_id).all()
        for sentence in sentences:
            # Delete annotations associated with the sentence
            Annotation.query.filter_by(sentence_id=sentence.id).delete()

        # Delete sentences associated with the project
        Sentence.query.filter_by(project_id=project_id).delete()

        # Finally, delete the project
        db.session.delete(project)
        db.session.commit()
        
        return {"message": "Project deleted successfully"}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500


def split_into_sentences(text):
    if not text:
        return []

    # Split the text by full stop or '|', filter out any empty sentences
    sentences = [s.strip() for s in re.findall(r'[^।|?!]+[.।|?!]', text)]

    return sentences
def get_projects_by_language(language):
    project = Project.query.filter_by(language=language).order_by(Project.id .desc()).all()
    return project


def get_projects():
    project = Project.query.filter_by().order_by(Project.id.desc()).all()
    return project



def get_projects_with_annotation_counts():
    # Subquery to count annotated sentences for each project
    annotated_subquery, unannotated_subquery = get_annotation_subquery()
    # Main query to get projects with annotated and unannotated counts
    projects = db.session.query(
        Project,
        func.coalesce(annotated_subquery.c.annotated_count, 0).label('annotated_sentences'),
        func.coalesce(unannotated_subquery.c.unannotated_count, 0).label('unannotated_sentences')
    ).outerjoin(
        annotated_subquery, Project.id == annotated_subquery.c.project_id
    ).outerjoin(
        unannotated_subquery, Project.id == unannotated_subquery.c.project_id
    ).order_by(Project.id.desc()).all()  # Note the correction here
    return projects


def get_projects_with_annotation_counts_with_language(language):
    # Subquery to count annotated sentences for each project
    annotated_subquery, unannotated_subquery = get_annotation_subquery()
    # Main query to get projects with annotated and unannotated counts
    projects = db.session.query(
        Project,
        func.coalesce(annotated_subquery.c.annotated_count, 0).label('annotated_sentences'),
        func.coalesce(unannotated_subquery.c.unannotated_count, 0).label('unannotated_sentences')
    ).outerjoin(
        annotated_subquery, Project.id == annotated_subquery.c.project_id
    ).outerjoin(
        unannotated_subquery, Project.id == unannotated_subquery.c.project_id
    ).filter(Project.language == language).order_by(Project.id.desc()).all()  # Note the correction here
    return projects

def get_annotation_subquery():
    annotated_subquery = db.session.query(
        Sentence.project_id,
        func.count('*').label('annotated_count')
    ).filter_by(is_annotated=True).group_by(Sentence.project_id).subquery()

    # Subquery to count unannotated sentences for each project
    unannotated_subquery = db.session.query(
        Sentence.project_id,
        func.count('*').label('unannotated_count')
    ).filter_by(is_annotated=False).group_by(Sentence.project_id).subquery()
    return annotated_subquery, unannotated_subquery


def assign_user_to_project(project_id, user_id):
    # Fetch the project and user from the database
    project = Project.query.get(project_id)
    if not project:
        return {"error": "Project not found"}, 404

    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    # Update project assignment
    project.assigned_to = user.name  # You could store user.name or user.id here
    project.is_assigned = True

    db.session.commit()

    return {"message": f"Project assigned to {user.name}"}, 200


def is_user_assigned_to_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return {"error": "Project not found"}, 404

    return {
        "is_assigned": project.is_assigned,
        "assigned_to": project.assigned_to
    }, 200


def update_project_title(project_id, new_title):
    # Fetch the project by ID
    project = Project.query.get(project_id)
    if not project:
        return {"error": "Project not found"}, 404

    # Update the title
    project.title = new_title

    try:
        db.session.commit()
        return {"message": "Project title updated successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500
