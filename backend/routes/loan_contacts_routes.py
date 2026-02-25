from flask import Blueprint, request, jsonify
from services.mysql_service import (
    get_loan_contacts, get_loan_contact_by_id, create_loan_contact,
    update_loan_contact, delete_loan_contact, get_loan_activities,
    create_loan_activity, delete_loan_activity, get_loan_contact_details
)
from utils.jwt_handler import decode_token
from datetime import datetime

loan_contacts_bp = Blueprint('loan_contacts', __name__)

def parse_date(date_value):
    """Parse date from various formats to YYYY-MM-DD format for MySQL"""
    if not date_value:
        return None
    
    # If already a string in correct format
    if isinstance(date_value, str):
        # Try parsing ISO8601 format (e.g., "2026-02-25T00:00:00.000")
        try:
            dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        # Try parsing just date part from ISO8601
        if 'T' in date_value:
            return date_value.split('T')[0]
        
        # Return as-is if already in correct format
        return date_value
    
    return str(date_value)

def get_user_from_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        return payload.get('user_id') if payload else None
    except:
        return None


@loan_contacts_bp.route('', methods=['GET'])
def get_contacts():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    contacts = get_loan_contacts(user_id)
    
    # Convert Decimal to float for JSON serialization
    for contact in contacts:
        contact['id'] = int(contact['id'])
        contact['user_id'] = int(contact['user_id'])
        contact['initial_balance'] = float(contact.get('initial_balance', 0))
        contact['current_balance'] = float(contact.get('current_balance', 0))
        contact['activity_count'] = int(contact.get('activity_count', 0))
    
    return jsonify({'contacts': contacts}), 200


@loan_contacts_bp.route('', methods=['POST'])
def create_contact():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    # Check if contact with same name exists
    contacts = get_loan_contacts(user_id)
    existing = next((c for c in contacts if c['name'].lower() == data.get('name', '').lower()), None)
    if existing:
        return jsonify({'message': 'Contact with this name already exists', 'contact': existing}), 409
    
    contact_data = {
        'name': data.get('name'),
        'phone_number': data.get('phone_number'),
        'email': data.get('email'),
        'notes': data.get('notes'),
        'initial_balance': data.get('initial_balance', 0)
    }
    
    try:
        contact_id = create_loan_contact(user_id, contact_data)
        contact = get_loan_contact_by_id(contact_id, user_id)
        return jsonify({'message': 'Contact created', 'contact': contact}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 400


@loan_contacts_bp.route('/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    contact = get_loan_contact_details(contact_id, user_id)
    if not contact:
        return jsonify({'message': 'Contact not found'}), 404
    
    # Convert Decimal to float
    contact['id'] = int(contact['id'])
    contact['user_id'] = int(contact['user_id'])
    contact['initial_balance'] = float(contact.get('initial_balance', 0))
    contact['current_balance'] = float(contact.get('current_balance', 0))
    contact['total_given'] = float(contact.get('total_given', 0))
    contact['total_borrowed'] = float(contact.get('total_borrowed', 0))
    contact['total_paid_to_you'] = float(contact.get('total_paid_to_you', 0))
    contact['total_you_paid'] = float(contact.get('total_you_paid', 0))
    contact['activity_count'] = int(contact.get('activity_count', 0))
    
    # Get activities
    activities = get_loan_activities(contact_id, user_id)
    for activity in activities:
        activity['id'] = int(activity['id'])
        activity['user_id'] = int(activity['user_id'])
        activity['contact_id'] = int(activity['contact_id'])
        activity['amount'] = float(activity['amount'])
        activity['balance_after'] = float(activity['balance_after'])
        # Convert date fields to string for JSON
        if activity.get('activity_date'):
            activity['activity_date'] = str(activity['activity_date'])
        if activity.get('created_at'):
            activity['created_at'] = str(activity['created_at'])
        if activity.get('updated_at'):
            activity['updated_at'] = str(activity['updated_at'])
    
    return jsonify({
        'contact': contact,
        'activities': activities
    }), 200


@loan_contacts_bp.route('/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    # Check ownership
    existing = get_loan_contact_by_id(contact_id, user_id)
    if not existing:
        return jsonify({'message': 'Contact not found'}), 404
    
    try:
        success = update_loan_contact(contact_id, user_id, data)
        if success:
            contact = get_loan_contact_by_id(contact_id, user_id)
            return jsonify({'message': 'Contact updated', 'contact': contact}), 200
        return jsonify({'message': 'Failed to update contact'}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 400


@loan_contacts_bp.route('/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    # Check ownership
    existing = get_loan_contact_by_id(contact_id, user_id)
    if not existing:
        return jsonify({'message': 'Contact not found'}), 404
    
    try:
        delete_loan_contact(contact_id, user_id)
        return jsonify({'message': 'Contact deleted'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400


@loan_contacts_bp.route('/<int:contact_id>/activities', methods=['GET'])
def get_activities(contact_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    # Verify ownership
    contact = get_loan_contact_by_id(contact_id, user_id)
    if not contact:
        return jsonify({'message': 'Contact not found'}), 404
    
    activities = get_loan_activities(contact_id, user_id)
    
    # Convert Decimal and date to JSON-serializable formats
    for activity in activities:
        activity['id'] = int(activity['id'])
        activity['user_id'] = int(activity['user_id'])
        activity['contact_id'] = int(activity['contact_id'])
        activity['amount'] = float(activity['amount'])
        activity['balance_after'] = float(activity['balance_after'])
        # Convert date fields to string for JSON
        if activity.get('activity_date'):
            activity['activity_date'] = str(activity['activity_date'])
        if activity.get('created_at'):
            activity['created_at'] = str(activity['created_at'])
        if activity.get('updated_at'):
            activity['updated_at'] = str(activity['updated_at'])
    
    return jsonify({'activities': activities}), 200


@loan_contacts_bp.route('/<int:contact_id>/activities', methods=['POST'])
def add_activity(contact_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    activity_type = data.get('activity_type')
    amount = float(data.get('amount', 0))
    
    if amount <= 0:
        return jsonify({'message': 'Amount must be greater than 0'}), 400
    
    if activity_type not in ['given', 'borrowed', 'payment_received', 'payment_made']:
        return jsonify({'message': 'Invalid activity type'}), 400
    
    # Verify contact ownership
    contact = get_loan_contact_by_id(contact_id, user_id)
    if not contact:
        return jsonify({'message': 'Contact not found'}), 404
    
    activity_data = {
        'activity_type': activity_type,
        'amount': amount,
        'description': data.get('description'),
        'activity_date': parse_date(data.get('activity_date') or data.get('date'))
    }
    
    try:
        activity_id = create_loan_activity(user_id, contact_id, activity_data)
        
        # Get updated contact details
        contact = get_loan_contact_details(contact_id, user_id)
        new_balance = float(contact['current_balance']) if contact else 0
        
        return jsonify({
            'message': 'Activity added',
            'activity_id': activity_id,
            'new_balance': new_balance
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 400


@loan_contacts_bp.route('/<int:contact_id>/activities/<int:activity_id>', methods=['DELETE'])
def delete_activity(contact_id, activity_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    # Verify contact ownership
    contact = get_loan_contact_by_id(contact_id, user_id)
    if not contact:
        return jsonify({'message': 'Contact not found'}), 404
    
    try:
        delete_loan_activity(activity_id, contact_id, user_id)
        
        # Get new balance
        contact = get_loan_contact_details(contact_id, user_id)
        new_balance = float(contact['current_balance']) if contact else 0
        
        return jsonify({'message': 'Activity deleted', 'new_balance': new_balance}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

