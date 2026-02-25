from flask import Blueprint, request, jsonify
import bcrypt
from services.mysql_service import create_user, get_user_by_email, get_user_by_id, update_user_name
from utils.jwt_handler import create_token, decode_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/validate', methods=['POST'])
def validate_token():
    """Validate the JWT token and return user info if valid"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'valid': False, 'message': 'No token provided'}), 401
    
    token = auth_header.split(' ')[1]
    payload = decode_token(token)
    
    if not payload:
        return jsonify({'valid': False, 'message': 'Invalid or expired token'}), 401
    
    user_id = payload.get('user_id')
    if not user_id:
        return jsonify({'valid': False, 'message': 'Invalid token payload'}), 401
    
    # Get user info from database
    try:
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'valid': False, 'message': 'User not found'}), 401
        
        return jsonify({
            'valid': True,
            'user_id': user_id,
            'name': user.get('name')
        }), 200
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)}), 401

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400
    
    if not name:
        return jsonify({'message': 'Name is required'}), 400
    
    try:
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({'message': 'Email already registered'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_id = create_user(email, password_hash, name)
        
        # Generate token
        token = create_token(user_id, email)
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user_id': user_id,
            'name': name
        }), 201
            
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400
    
    try:
        # Get user by email
        user = get_user_by_email(email)
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Generate token
        token = create_token(user['id'], email)
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user_id': user['id'],
            'name': user.get('name')
        }), 200
            
    except Exception as e:
        return jsonify({'message': str(e)}), 401

