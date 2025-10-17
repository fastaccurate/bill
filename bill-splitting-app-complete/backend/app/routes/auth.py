from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models.user import User
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    # Remove all non-digit characters
    phone_digits = re.sub(r'[^0-9]', '', phone)
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(phone_digits) <= 15

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['email', 'phone_number', 'full_name', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        email = data['email'].lower().strip()
        phone_number = data['phone_number'].strip()
        full_name = data['full_name'].strip()
        password = data['password']

        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        # Validate phone number
        if not validate_phone(phone_number):
            return jsonify({'error': 'Invalid phone number format'}), 400

        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400

        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == email) | (User.phone_number == phone_number)
        ).first()

        if existing_user:
            if existing_user.email == email:
                return jsonify({'error': 'Email already registered'}), 409
            else:
                return jsonify({'error': 'Phone number already registered'}), 409

        # Create new user
        user = User(
            email=email,
            phone_number=phone_number,
            full_name=full_name
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Generate tokens
        tokens = user.generate_tokens()

        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400

        email = data['email'].lower().strip()
        password = data['password']

        # Find user
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401

        # Generate tokens
        tokens = user.generate_tokens()

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 404

        # Generate new access token
        access_token = create_access_token(identity=user.id)

        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'user': user.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name'].strip()

        if 'phone_number' in data:
            phone_number = data['phone_number'].strip()
            if not validate_phone(phone_number):
                return jsonify({'error': 'Invalid phone number format'}), 400

            # Check if phone number is already taken by another user
            existing_user = User.query.filter(
                User.phone_number == phone_number,
                User.id != user.id
            ).first()

            if existing_user:
                return jsonify({'error': 'Phone number already in use'}), 409

            user.phone_number = phone_number

        db.session.commit()

        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        # Validate required fields
        if not all(k in data for k in ['current_password', 'new_password']):
            return jsonify({'error': 'Current password and new password are required'}), 400

        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401

        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400

        # Check if new password is different from current
        if user.check_password(data['new_password']):
            return jsonify({'error': 'New password must be different from current password'}), 400

        # Update password
        user.set_password(data['new_password'])
        db.session.commit()

        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (in a real app, you'd want to blacklist the token)"""
    return jsonify({'message': 'Logged out successfully'}), 200

# Helper route to check if email/phone exists (for frontend validation)
@auth_bp.route('/check-availability', methods=['POST'])
def check_availability():
    """Check if email or phone number is available"""
    try:
        data = request.get_json()

        result = {'available': True}

        if 'email' in data:
            email = data['email'].lower().strip()
            if User.query.filter_by(email=email).first():
                result['available'] = False
                result['field'] = 'email'
                result['message'] = 'Email already registered'

        elif 'phone_number' in data:
            phone = data['phone_number'].strip()
            if User.query.filter_by(phone_number=phone).first():
                result['available'] = False
                result['field'] = 'phone_number'
                result['message'] = 'Phone number already registered'

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
