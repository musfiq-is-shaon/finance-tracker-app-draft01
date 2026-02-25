import mysql.connector
from mysql.connector import pooling
from config import Config

# Connection pool
_pool = None

def get_connection():
    """Get a connection from the pool"""
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="finance_tracker_pool",
                pool_size=5,
                pool_reset_session=True,
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE,
                autocommit=False
            )
        except mysql.connector.Error as e:
            print(f"Error creating connection pool: {e}")
            raise
    return _pool.get_connection()

def init_database():
    """Initialize the database - create tables if they don't exist"""
    # First connect without database to create it
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS finance_tracker")
    cursor.close()
    conn.close()
    
    # Then connect to the database and create tables
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type ENUM('income', 'expense') NOT NULL,
            amount DECIMAL(15, 2) NOT NULL,
            category VARCHAR(100) NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Loans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type ENUM('given', 'borrowed') NOT NULL,
            person_name VARCHAR(255) NOT NULL,
            phone_number VARCHAR(50),
            amount DECIMAL(15, 2) NOT NULL,
            paid_amount DECIMAL(15, 2) DEFAULT 0,
            description TEXT,
            date DATE NOT NULL,
            is_paid BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Loan contacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_contacts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            phone_number VARCHAR(50),
            email VARCHAR(255),
            initial_balance DECIMAL(15, 2) DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Loan activities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_activities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            contact_id INT NOT NULL,
            activity_type ENUM('given', 'borrowed', 'payment_received', 'payment_made') NOT NULL,
            amount DECIMAL(15, 2) NOT NULL,
            balance_after DECIMAL(15, 2) NOT NULL,
            description TEXT,
            activity_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (contact_id) REFERENCES loan_contacts(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes (MySQL syntax)
    try:
        cursor.execute("CREATE INDEX idx_transactions_user_id ON transactions(user_id)")
    except:
        pass  # Index may already exist
    try:
        cursor.execute("CREATE INDEX idx_transactions_date ON transactions(date)")
    except:
        pass
    try:
        cursor.execute("CREATE INDEX idx_loans_user_id ON loans(user_id)")
    except:
        pass
    try:
        cursor.execute("CREATE INDEX idx_loan_contacts_user_id ON loan_contacts(user_id)")
    except:
        pass
    try:
        cursor.execute("CREATE INDEX idx_loan_activities_contact_id ON loan_activities(contact_id)")
    except:
        pass
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized successfully!")

# ==================== USER OPERATIONS ====================

def create_user(email, password_hash, name=None):
    """Create a new user"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (%s, %s, %s)",
            (email, password_hash, name)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email):
    """Get user by email"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
        return result
    finally:
        cursor.close()
        conn.close()

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, email, name, created_at FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        return result
    finally:
        cursor.close()
        conn.close()

def update_user_name(user_id, name):
    """Update user name"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()

# ==================== TRANSACTION OPERATIONS ====================

def get_transactions(user_id):
    """Get all transactions for a user"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM transactions WHERE user_id = %s ORDER BY date DESC, created_at DESC",
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_transaction_by_id(transaction_id, user_id):
    """Get a single transaction"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def create_transaction(user_id, data):
    """Create a new transaction"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """INSERT INTO transactions (user_id, type, amount, category, description, date)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, data['type'], data['amount'], data['category'], 
             data.get('description'), data['date'])
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def update_transaction(transaction_id, user_id, data):
    """Update a transaction"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE transactions 
               SET type = %s, amount = %s, category = %s, description = %s, date = %s
               WHERE id = %s AND user_id = %s""",
            (data['type'], data['amount'], data['category'], 
             data.get('description'), data['date'], transaction_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def delete_transaction(transaction_id, user_id):
    """Delete a transaction"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

# ==================== LOAN OPERATIONS ====================

def get_loans(user_id):
    """Get all loans for a user"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM loans WHERE user_id = %s ORDER BY date DESC",
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_loan_by_id(loan_id, user_id):
    """Get a single loan"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM loans WHERE id = %s AND user_id = %s",
            (loan_id, user_id)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def create_loan(user_id, data):
    """Create a new loan"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """INSERT INTO loans (user_id, type, person_name, phone_number, amount, paid_amount, description, date)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, data['type'], data['person_name'], data.get('phone_number'),
             data['amount'], data.get('paid_amount', 0), data.get('description'), data['date'])
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def update_loan(loan_id, user_id, data):
    """Update a loan"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE loans 
               SET type = %s, person_name = %s, phone_number = %s, amount = %s, 
                   paid_amount = %s, description = %s, date = %s, is_paid = %s
               WHERE id = %s AND user_id = %s""",
            (data['type'], data['person_name'], data.get('phone_number'), data['amount'],
             data.get('paid_amount', 0), data.get('description'), data['date'], 
             data.get('is_paid', False), loan_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def delete_loan(loan_id, user_id):
    """Delete a loan"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM loans WHERE id = %s AND user_id = %s",
            (loan_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

# ==================== LOAN CONTACTS OPERATIONS ====================

def get_loan_contacts(user_id):
    """Get all loan contacts for a user"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM loan_contacts WHERE user_id = %s ORDER BY updated_at DESC",
            (user_id,)
        )
        contacts = cursor.fetchall()
        
        # Get latest balance for each contact
        for contact in contacts:
            cursor.execute(
                """SELECT balance_after FROM loan_activities 
                   WHERE contact_id = %s ORDER BY created_at DESC LIMIT 1""",
                (contact['id'],)
            )
            balance_result = cursor.fetchone()
            contact['current_balance'] = balance_result['balance_after'] if balance_result else 0
            
            # Get activity count
            cursor.execute(
                "SELECT COUNT(*) as count FROM loan_activities WHERE contact_id = %s",
                (contact['id'],)
            )
            count_result = cursor.fetchone()
            contact['activity_count'] = count_result['count'] if count_result else 0
        
        return contacts
    finally:
        cursor.close()
        conn.close()

def get_loan_contact_by_id(contact_id, user_id):
    """Get a single loan contact"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM loan_contacts WHERE id = %s AND user_id = %s",
            (contact_id, user_id)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def create_loan_contact(user_id, data):
    """Create a new loan contact"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """INSERT INTO loan_contacts (user_id, name, phone_number, email, initial_balance, notes)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, data['name'], data.get('phone_number'), data.get('email'),
             data.get('initial_balance', 0), data.get('notes'))
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def update_loan_contact(contact_id, user_id, data):
    """Update a loan contact"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE loan_contacts 
               SET name = %s, phone_number = %s, email = %s, notes = %s
               WHERE id = %s AND user_id = %s""",
            (data.get('name'), data.get('phone_number'), data.get('email'),
             data.get('notes'), contact_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def delete_loan_contact(contact_id, user_id):
    """Delete a loan contact and all related activities"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Delete activities first
        cursor.execute(
            "DELETE FROM loan_activities WHERE contact_id = %s AND user_id = %s",
            (contact_id, user_id)
        )
        # Delete contact
        cursor.execute(
            "DELETE FROM loan_contacts WHERE id = %s AND user_id = %s",
            (contact_id, user_id)
        )
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()

# ==================== LOAN ACTIVITIES OPERATIONS ====================

def get_loan_activities(contact_id, user_id):
    """Get all activities for a loan contact"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT * FROM loan_activities 
               WHERE contact_id = %s AND user_id = %s 
               ORDER BY activity_date DESC, created_at DESC""",
            (contact_id, user_id)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def create_loan_activity(user_id, contact_id, data):
    """Create a new loan activity"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get previous balance
        cursor.execute(
            """SELECT balance_after FROM loan_activities 
               WHERE contact_id = %s ORDER BY created_at DESC LIMIT 1""",
            (contact_id,)
        )
        result = cursor.fetchone()
        previous_balance = float(result['balance_after']) if result else 0
        
        # Calculate new balance
        amount = float(data['amount'])
        activity_type = data['activity_type']
        
        if activity_type == 'given':
            new_balance = previous_balance + amount
        elif activity_type == 'borrowed':
            new_balance = previous_balance - amount
        elif activity_type == 'payment_received':
            new_balance = previous_balance - amount
        elif activity_type == 'payment_made':
            new_balance = previous_balance + amount
        else:
            raise ValueError(f"Invalid activity type: {activity_type}")
        
        # Insert activity
        cursor.execute(
            """INSERT INTO loan_activities 
               (user_id, contact_id, activity_type, amount, balance_after, description, activity_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, contact_id, activity_type, amount, new_balance,
             data.get('description'), data.get('activity_date'))
        )
        
        # Update contact timestamp
        cursor.execute(
            "UPDATE loan_contacts SET updated_at = NOW() WHERE id = %s",
            (contact_id,)
        )
        
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def delete_loan_activity(activity_id, contact_id, user_id):
    """Delete a loan activity and recalculate balances"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get the activity to delete
        cursor.execute(
            "SELECT * FROM loan_activities WHERE id = %s AND contact_id = %s AND user_id = %s",
            (activity_id, contact_id, user_id)
        )
        activity = cursor.fetchone()
        if not activity:
            return False
        
        # Delete the activity
        cursor.execute(
            "DELETE FROM loan_activities WHERE id = %s",
            (activity_id,)
        )
        
        # Get remaining activities and recalculate balances
        cursor.execute(
            """SELECT * FROM loan_activities 
               WHERE contact_id = %s ORDER BY activity_date ASC, created_at ASC""",
            (contact_id,)
        )
        remaining = cursor.fetchall()
        
        balance = 0
        for a in remaining:
            activity_type = a['activity_type']
            amount = float(a['amount'])
            
            if activity_type == 'given':
                balance = balance + amount
            elif activity_type == 'borrowed':
                balance = balance - amount
            elif activity_type == 'payment_received':
                balance = balance - amount
            elif activity_type == 'payment_made':
                balance = balance + amount
            
            cursor.execute(
                "UPDATE loan_activities SET balance_after = %s WHERE id = %s",
                (balance, a['id'])
            )
        
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()

def get_loan_contact_details(contact_id, user_id):
    """Get detailed info for a loan contact"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get contact
        cursor.execute(
            "SELECT * FROM loan_contacts WHERE id = %s AND user_id = %s",
            (contact_id, user_id)
        )
        contact = cursor.fetchone()
        if not contact:
            return None
        
        # Get summary stats
        cursor.execute(
            """SELECT 
               COALESCE(SUM(CASE WHEN activity_type = 'given' THEN amount ELSE 0 END), 0) as total_given,
               COALESCE(SUM(CASE WHEN activity_type = 'borrowed' THEN amount ELSE 0 END), 0) as total_borrowed,
               COALESCE(SUM(CASE WHEN activity_type = 'payment_received' THEN amount ELSE 0 END), 0) as total_paid_to_you,
               COALESCE(SUM(CASE WHEN activity_type = 'payment_made' THEN amount ELSE 0 END), 0) as total_you_paid
               FROM loan_activities WHERE contact_id = %s""",
            (contact_id,)
        )
        stats = cursor.fetchone()
        
        # Get current balance
        cursor.execute(
            """SELECT balance_after FROM loan_activities 
               WHERE contact_id = %s ORDER BY created_at DESC LIMIT 1""",
            (contact_id,)
        )
        balance_result = cursor.fetchone()
        current_balance = float(balance_result['balance_after']) if balance_result else 0
        
        # Get activity count
        cursor.execute(
            "SELECT COUNT(*) as count FROM loan_activities WHERE contact_id = %s",
            (contact_id,)
        )
        count_result = cursor.fetchone()
        
        return {
            **contact,
            'current_balance': current_balance,
            'total_given': float(stats['total_given']),
            'total_borrowed': float(stats['total_borrowed']),
            'total_paid_to_you': float(stats['total_paid_to_you']),
            'total_you_paid': float(stats['total_you_paid']),
            'activity_count': count_result['count'] if count_result else 0
        }
    finally:
        cursor.close()
        conn.close()

