from flask import Blueprint, request, jsonify
from services.mysql_service import (
    get_loans, get_loan_by_id, create_loan, 
    update_loan, delete_loan, get_transactions
)
from utils.jwt_handler import decode_token
from datetime import datetime

loan_bp = Blueprint('loans', __name__)

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


def calculate_balance(user_id):
    """Calculate current balance including loans"""
    # Get all transactions
    transactions = get_transactions(user_id)
    
    # Get all unpaid loans
    loans = get_loans(user_id)
    unpaid_loans = [l for l in loans if not l.get('is_paid', False)]
    
    # Calculate totals
    total_income = sum(float(t['amount']) for t in transactions if t['type'] == 'income')
    total_expenses = sum(float(t['amount']) for t in transactions if t['type'] == 'expense')
    
    total_loan_given = sum(
        float(l['amount']) - float(l.get('paid_amount', 0)) 
        for l in unpaid_loans 
        if l['type'] == 'given'
    )
    total_loan_borrowed = sum(
        float(l['amount']) - float(l.get('paid_amount', 0)) 
        for l in unpaid_loans 
        if l['type'] == 'borrowed'
    )
    
    # Total Money = Income - Expenses + Borrowed - Given
    return total_income - total_expenses + total_loan_borrowed - total_loan_given


@loan_bp.route('', methods=['GET'])
def get_all_loans():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    loans = get_loans(user_id)
    
    # Convert Decimal and date to JSON-serializable formats
    for loan in loans:
        loan['amount'] = float(loan['amount'])
        loan['paid_amount'] = float(loan.get('paid_amount', 0))
        # Convert date fields to string
        if loan.get('date'):
            loan['date'] = str(loan['date'])
        if loan.get('created_at'):
            loan['created_at'] = str(loan['created_at'])
        if loan.get('updated_at'):
            loan['updated_at'] = str(loan['updated_at'])
    
    return jsonify({'loans': loans}), 200

@loan_bp.route('', methods=['POST'])
def add_loan():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    loan_type = data.get('type')
    amount = float(data.get('amount', 0))
    
    # Check balance for "loan given" - cannot give more than current balance
    if loan_type == 'given':
        current_balance = calculate_balance(user_id)
        if amount > current_balance:
            return jsonify({
                'message': 'Insufficient balance to give this loan',
                'current_balance': current_balance,
                'required': amount
            }), 400
    
    loan_data = {
        'type': loan_type,
        'person_name': data.get('person_name'),
        'phone_number': data.get('phone_number'),
        'amount': amount,
        'paid_amount': data.get('paid_amount', 0),
        'description': data.get('description'),
        'date': parse_date(data.get('date')),
        'is_paid': data.get('is_paid', False)
    }
    
    try:
        loan_id = create_loan(user_id, loan_data)
        loan = get_loan_by_id(loan_id, user_id)
        loan['amount'] = float(loan['amount'])
        loan['paid_amount'] = float(loan.get('paid_amount', 0))
        # Convert date fields to string for JSON
        if loan.get('date'):
            loan['date'] = str(loan['date'])
        if loan.get('created_at'):
            loan['created_at'] = str(loan['created_at'])
        if loan.get('updated_at'):
            loan['updated_at'] = str(loan['updated_at'])
        return jsonify({'message': 'Loan added', 'loan': loan}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@loan_bp.route('/<int:loan_id>', methods=['PUT'])
def update_loan_route(loan_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    # Parse date to MySQL format if provided
    if 'date' in data:
        data['date'] = parse_date(data.get('date'))
    
    try:
        success = update_loan(loan_id, user_id, data)
        if success:
            loan = get_loan_by_id(loan_id, user_id)
            if loan:
                loan['amount'] = float(loan['amount'])
                loan['paid_amount'] = float(loan.get('paid_amount', 0))
                # Convert date fields to string for JSON
                if loan.get('date'):
                    loan['date'] = str(loan['date'])
                if loan.get('created_at'):
                    loan['created_at'] = str(loan['created_at'])
                if loan.get('updated_at'):
                    loan['updated_at'] = str(loan['updated_at'])
                return jsonify({'message': 'Loan updated', 'loan': loan}), 200
        return jsonify({'message': 'Failed to update loan'}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@loan_bp.route('/<int:loan_id>', methods=['DELETE'])
def delete_loan_route(loan_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        success = delete_loan(loan_id, user_id)
        if success:
            return jsonify({'message': 'Loan deleted'}), 200
        return jsonify({'message': 'Loan not found'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 400

