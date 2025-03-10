from datetime import datetime, timedelta
import random
import uuid

from flask_mail import Message
from .. import db, bcrypt
from ..models.user_model import User
from ..models.sentence_model import Sentence
from .. import mail  # Import Flask-Mail



def create_user(data):
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(name=data['name'], email=data['email'], password=hashed_password, language=data['language'],
                    role=data['role'],organisation=data['organisation'] )
    db.session.add(new_user)
    db.session.commit()
    return new_user


def check_user(email, password):
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        return user
    return None


def get_user_language(email):
    user = User.query.filter_by(email=email).first()
    return user.language


def get_user_role(email):
    user = User.query.filter_by(email=email).first()
    return user.role

def get_users_by_organisation(organisation):
    users = User.query.filter_by(organisation=organisation).filter(User.role != 'Admin').all()
    return users

def assign_sentences_custom(project_id, assignment_dict):
    """
    Assigns specific sentences from a project to users based on a custom distribution.

    :param project_id: ID of the project whose sentences are being assigned.
    :param assignment_dict: Dictionary {user_id: [sentence_id1, sentence_id2, ...]} defining sentence IDs for each user.
    :return: A message indicating success or failure.
    """
    # Fetch all unassigned sentences belonging to the given project
    available_sentences = {s.id: s for s in Sentence.query.filter_by(project_id=project_id, user_id=None).all()}
    
    # Collect all requested sentence IDs
    requested_sentence_ids = {sid for sids in assignment_dict.values() for sid in sids}
    
    # Check if all requested IDs exist and are unassigned
    invalid_ids = requested_sentence_ids - available_sentences.keys()
    if invalid_ids:
        return {"message": f"Invalid or already assigned sentence IDs: {list(invalid_ids)}"}

    # Assign sentences based on request
    for user_id, sentence_ids in assignment_dict.items():
        for sentence_id in sentence_ids:
            if sentence_id in available_sentences:
                available_sentences[sentence_id].user_id = user_id  # Assign to user

    db.session.commit()
    return {"message": f"Sentences for project {project_id} assigned successfully."}

otp_storage = {}

def generate_otp():
    return str(random.randint(100000, 999999))  # 6-digit OTP

def send_reset_otp(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return None  # User not found

    otp = generate_otp()
    otp_storage[email] = otp  # Store OTP temporarily

    # Customize the email content
    subject = "Password Reset OTP - NER Annotation Tool"
    body = f"""
    Hello {user.name},  

    You have requested to reset your password for the **NER Annotation Tool**.  
    Your OTP for password reset is: **{otp}**  

    Please enter this OTP in the app to verify your identity.  
    If you did not request this, please ignore this email.  

    Regards,  
    NER Annotation Tool Support Team  
    """

    # Send OTP via Email
    msg = Message(subject, sender="noreply@nertool.com", recipients=[email])
    msg.body = body
    mail.send(msg)

    return True

def verify_otp(email, otp):
    return otp_storage.get(email) == otp  # Check OTP

def reset_password(email, new_password):
    user = User.query.filter_by(email=email).first()
    if user:
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        return True
    return False