from flask import Blueprint, jsonify, request
from services.mysql_service import (
    get_transactions, get_loans, get_loan_contacts, get_loan_contact_details
)
from utils.jwt_handler import decode_token

dashboard_bp = Blueprint('dashboard', __name__)

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
    """Calculate current balance including all loan activities"""
    # Get all transactions
    transactions = get_transactions(user_id)
    
    # Get all loan contacts
    loan_contacts = get_loan_contacts(user_id)
    
    # Get old loans for backward compatibility
    old_loans = get_loans(user_id)
    
    # Calculate totals from transactions
    total_income = sum(float(t['amount']) for t in transactions if t['type'] == 'income')
    total_expenses = sum(float(t['amount']) for t in transactions if t['type'] == 'expense')
    
    # Calculate from loan contacts
    outstanding_given = 0
    outstanding_borrowed = 0
    
    for contact in loan_contacts:
        balance = float(contact.get('current_balance', 0))
        if balance > 0:
            outstanding_given += balance
        else:
            outstanding_borrowed += abs(balance)
    
    # Also include old loans for backward compatibility
    old_loan_given = sum(
        float(l['amount']) - float(l.get('paid_amount', 0)) 
        for l in old_loans 
        if l['type'] == 'given' and not l.get('is_paid', False)
    )
    old_loan_borrowed = sum(
        float(l['amount']) - float(l.get('paid_amount', 0)) 
        for l in old_loans 
        if l['type'] == 'borrowed' and not l.get('is_paid', False)
    )
    
    outstanding_given += old_loan_given
    outstanding_borrowed += old_loan_borrowed
    
    # Total Balance = Income - Expenses - Outstanding Given + Outstanding Borrowed
    total_balance = total_income - total_expenses - outstanding_given + outstanding_borrowed
    
    return {
        'total_balance': total_balance,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'outstanding_given': outstanding_given,
        'outstanding_borrowed': outstanding_borrowed,
    }


@dashboard_bp.route('', methods=['GET'])
def get_dashboard():
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    balance_data = calculate_balance(user_id)
    
    # Get all transactions
    transactions = get_transactions(user_id)
    
    # Get loan contacts
    loan_contacts = get_loan_contacts(user_id)
    loan_contacts_count = len(loan_contacts)
    
    # Monthly data for transactions
    monthly_data = {}
    for t in transactions:
        date_str = str(t['date'])
        month = date_str[:7]  # YYYY-MM
        if month not in monthly_data:
            monthly_data[month] = {'income': 0, 'expense': 0, 'loan_given': 0, 'loan_borrowed': 0}
        if t['type'] == 'income':
            monthly_data[month]['income'] += float(t['amount'])
        else:
            monthly_data[month]['expense'] += float(t['amount'])
    
    # Sort by month and take last 6 months
    sorted_months = sorted(monthly_data.keys())[-6:]
    monthly_list = [{'month': m, **monthly_data[m]} for m in sorted_months]
    
    # Recent transactions (last 10)
    sorted_transactions = sorted(transactions, key=lambda x: x['date'], reverse=True)[:10]
    for t in sorted_transactions:
        t['amount'] = float(t['amount'])
        # Convert date fields to string for JSON
        if t.get('date'):
            t['date'] = str(t['date'])
        if t.get('created_at'):
            t['created_at'] = str(t['created_at'])
    
    # Category-wise expense breakdown
    expense_by_category = {}
    income_by_category = {}
    for t in transactions:
        category = t.get('category', 'Other')
        amount = float(t['amount'])
        if t['type'] == 'expense':
            expense_by_category[category] = expense_by_category.get(category, 0) + amount
        else:
            income_by_category[category] = income_by_category.get(category, 0) + amount
    
    # Transaction counts
    total_transactions = len(transactions)
    income_transactions = [t for t in transactions if t['type'] == 'income']
    expense_transactions = [t for t in transactions if t['type'] == 'expense']
    total_income_count = len(income_transactions)
    total_expense_count = len(expense_transactions)
    
    # Average transaction values
    avg_income = balance_data['total_income'] / total_income_count if total_income_count > 0 else 0
    avg_expense = balance_data['total_expenses'] / total_expense_count if total_expense_count > 0 else 0
    
    # Calculate total loan activities
    total_loan_activities = sum(c.get('activity_count', 0) for c in loan_contacts)
    total_given_count = 0
    total_borrowed_count = 0
    
    return jsonify({
        'total_balance': balance_data['total_balance'],
        'total_income': balance_data['total_income'],
        'total_expenses': balance_data['total_expenses'],
        'loan_given': balance_data['outstanding_given'],
        'loan_borrowed': balance_data['outstanding_borrowed'],
        'total_loan_given': balance_data['outstanding_given'],
        'total_loan_borrowed': balance_data['outstanding_borrowed'],
        'monthly_data': monthly_list,
        'recent_transactions': sorted_transactions,
        # Additional analytics data
        'expense_by_category': expense_by_category,
        'income_by_category': income_by_category,
        'loan_contacts_count': loan_contacts_count,
        'total_transactions': total_transactions,
        'total_income_count': total_income_count,
        'total_expense_count': total_expense_count,
        'avg_income': avg_income,
        'avg_expense': avg_expense,
        'total_loan_activities': total_loan_activities,
        'total_given_count': total_given_count,
        'total_borrowed_count': total_borrowed_count,
    }), 200


@dashboard_bp.route('/balance', methods=['GET'])
def get_balance():
    """Get current balance for validation purposes"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    
    balance_data = calculate_balance(user_id)
    
    return jsonify({
        'balance': balance_data['total_balance'],
        'total_income': balance_data['total_income'],
        'total_expenses': balance_data['total_expenses'],
        'loan_given': balance_data['outstanding_given'],
        'loan_borrowed': balance_data['outstanding_borrowed']
    }), 200

