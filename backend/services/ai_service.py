from services.mysql_service import get_transactions

def analyze_spending_patterns(user_id):
    # Get transactions from MySQL
    transactions = get_transactions(user_id)
    
    if not transactions:
        return {
            'total_income': 0,
            'total_expenses': 0,
            'top_expense_category': None,
            'advice': "Start tracking your transactions to get personalized financial advice!"
        }
    
    total_income = sum(float(t['amount']) for t in transactions if t['type'] == 'income')
    total_expenses = sum(float(t['amount']) for t in transactions if t['type'] == 'expense')
    
    category_spending = {}
    for t in transactions:
        if t['type'] == 'expense':
            cat = t.get('category', 'Other')
            category_spending[cat] = category_spending.get(cat, 0) + float(t['amount'])
    
    top_category = max(category_spending, key=category_spending.get) if category_spending else None
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'top_expense_category': top_category,
        'category_spending': category_spending
    }

def generate_advice(user_id):
    analysis = analyze_spending_patterns(user_id)
    
    advices = []
    
    if analysis['total_expenses'] > analysis['total_income'] * 0.8:
        advices.append("Your expenses are quite high compared to income. Try to reduce unnecessary spending.")
    
    if analysis['top_expense_category']:
        cat = analysis['top_expense_category']
        if cat in ['Entertainment', 'Shopping']:
            advices.append(f"You seem to spend a lot on {cat}. Consider setting a budget for this category.")
    
    if analysis['total_income'] > 0:
        savings_rate = (analysis['total_income'] - analysis['total_expenses']) / analysis['total_income'] * 100
        if savings_rate < 10:
            advices.append("Your savings rate is low. Try to save at least 20% of your income.")
        elif savings_rate > 30:
            advices.append("Great job on saving! Consider investing some of your savings for better returns.")
    
    if not advices:
        advices.append("Keep up the good work! Continue tracking your finances regularly.")
    
    return " ".join(advices)

