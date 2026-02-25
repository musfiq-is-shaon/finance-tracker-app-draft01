from flask import Blueprint, request, jsonify
from services.mysql_service import (
    get_transactions, get_transaction_by_id, create_transaction, 
    update_transaction, delete_transaction, get_loans
)
from utils.jwt_handler import decode_token
from datetime import datetime

transaction_bp = Blueprint('transactions', __name__)

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


@transaction_bp.route('', methods=['GET'])
def get_all_transactions():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get all transactions
    transactions = get_transactions(user_id)
    
    # Apply filters
    if category:
        transactions = [t for t in transactions if t['category'] == category]
    if start_date:
        transactions = [t for t in transactions if str(t['date']) >= start_date]
    if end_date:
        transactions = [t for t in transactions if str(t['date']) <= end_date]
    
    # Convert Decimal and date to JSON-serializable formats
    for t in transactions:
        t['amount'] = float(t['amount'])
        # Convert date to ISO8601 string
        if t.get('date'):
            t['date'] = str(t['date'])
        if t.get('created_at'):
            t['created_at'] = str(t['created_at'])
        if t.get('updated_at'):
            t['updated_at'] = str(t['updated_at'])
    
    return jsonify({'transactions': transactions}), 200

@transaction_bp.route('', methods=['POST'])
def add_transaction():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    transaction_type = data.get('type')
    amount = float(data.get('amount', 0))
    
    # Check balance for expenses
    if transaction_type == 'expense':
        current_balance = calculate_balance(user_id)
        if amount > current_balance:
            return jsonify({
                'message': 'Insufficient balance',
                'current_balance': current_balance,
                'required': amount
            }), 400
    
    transaction_data = {
        'type': transaction_type,
        'amount': amount,
        'category': data.get('category'),
        'description': data.get('description', ''),
        'date': parse_date(data.get('date'))
    }
    
    try:
        transaction_id = create_transaction(user_id, transaction_data)
        transaction = get_transaction_by_id(transaction_id, user_id)
        transaction['amount'] = float(transaction['amount'])
        # Convert date fields to string for JSON
        if transaction.get('date'):
            transaction['date'] = str(transaction['date'])
        if transaction.get('created_at'):
            transaction['created_at'] = str(transaction['created_at'])
        if transaction.get('updated_at'):
            transaction['updated_at'] = str(transaction['updated_at'])
        return jsonify({'message': 'Transaction added', 'transaction': transaction}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@transaction_bp.route('/<int:transaction_id>', methods=['PUT'])
def update_transaction_route(transaction_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    # Parse date to MySQL format if provided
    if 'date' in data:
        data['date'] = parse_date(data.get('date'))
    
    try:
        success = update_transaction(transaction_id, user_id, data)
        if success:
            transaction = get_transaction_by_id(transaction_id, user_id)
            if transaction:
                transaction['amount'] = float(transaction['amount'])
                # Convert date fields to string for JSON
                if transaction.get('date'):
                    transaction['date'] = str(transaction['date'])
                if transaction.get('created_at'):
                    transaction['created_at'] = str(transaction['created_at'])
                if transaction.get('updated_at'):
                    transaction['updated_at'] = str(transaction['updated_at'])
                return jsonify({'message': 'Transaction updated', 'transaction': transaction}), 200
        return jsonify({'message': 'Failed to update transaction'}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@transaction_bp.route('/<int:transaction_id>', methods=['DELETE'])
def delete_transaction_route(transaction_id):
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    try:
        success = delete_transaction(transaction_id, user_id)
        if success:
            return jsonify({'message': 'Transaction deleted'}), 200
        return jsonify({'message': 'Transaction not found'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 400

