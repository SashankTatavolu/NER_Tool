from datetime import timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from ..models.user_model import User

from ..services.user_service import create_user, check_user, get_users_by_organisation, reset_password, send_reset_otp, verify_otp
from ..schemas.user_schema import user_schema
from ..models.sentence_model import Sentence

user_blueprint = Blueprint('user_blueprint', __name__)

@user_blueprint.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    user = create_user(data)
    return user_schema.jsonify(user)

# @user_blueprint.route('/login', methods=['POST'])
# def login_user():
#     data = request.get_json()
#     user = check_user(data['email'], data['password'])
#     if user:
#         expires = timedelta(minutes=30)
#         access_token = create_access_token(identity=data['email'], expires_delta=expires)
#         return jsonify(access_token=access_token, role=user.role), 200
#     else:
#         return jsonify({"message": "Invalid email or password"}), 401


@user_blueprint.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    user = check_user(data['email'], data['password'])
    if user:
        expires = timedelta(minutes=30)
        access_token = create_access_token(identity=data['email'], expires_delta=expires)
        return jsonify(
            access_token=access_token,
            role=user.role,
            organisation=user.organisation  # Assuming a relationship to Organization
        ), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401


@user_blueprint.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@user_blueprint.route('/organisation/<string:organisation>', methods=['GET'])
@jwt_required()  
def get_users_by_org(organisation):
    # Fetch users by organization
    users = get_users_by_organisation(organisation)

    if not users:
        return jsonify({"message": "No users found for this organisation"}), 404

    filtered_users = []

    for user in users:
        # Check if the user is assigned any sentences
        assigned_sentences = Sentence.query.filter_by(user_id=user.id).all()

        if not assigned_sentences:
            # User is not assigned to any sentence, add to list
            filtered_users.append({"id": user.id, "name": user.name})
        else:
            # Check if all assigned sentences are completed (is_annotated = True)
            all_completed = all(sentence.is_annotated for sentence in assigned_sentences)

            if all_completed:
                filtered_users.append({"id": user.id, "name": user.name})

    if not filtered_users:
        return jsonify({"message": "No available users"}), 404

    return jsonify(filtered_users)  # No tuple, just jsonify response



@user_blueprint.route('/send-reset-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')

    if send_reset_otp(email):
        return jsonify({"message": "OTP sent to email"}), 200
    return jsonify({"error": "User not found"}), 404

@user_blueprint.route('/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if verify_otp(email, otp):
        return jsonify({"message": "OTP verified successfully"}), 200
    return jsonify({"error": "Invalid OTP"}), 400

@user_blueprint.route('/reset-password', methods=['POST'])
def reset_user_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')

    if reset_password(email, new_password):
        return jsonify({"message": "Password reset successful"}), 200
    return jsonify({"error": "User not found"}), 404