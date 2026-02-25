-- =====================================================
-- MYSQL SCHEMA FOR FINANCE TRACKER APP
-- =====================================================

-- Create database
CREATE DATABASE IF NOT EXISTS finance_tracker;
USE finance_tracker;

-- =====================================================
-- USERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
);

-- =====================================================
-- TRANSACTIONS TABLE
-- =====================================================
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
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_transactions_user_id (user_id),
    INDEX idx_transactions_date (date),
    INDEX idx_transactions_type (type),
    INDEX idx_transactions_category (category)
);

-- =====================================================
-- LOANS TABLE (Legacy - for backward compatibility)
-- =====================================================
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
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_loans_user_id (user_id),
    INDEX idx_loans_date (date),
    INDEX idx_loans_type (type),
    INDEX idx_loans_is_paid (is_paid)
);

-- =====================================================
-- LOAN CONTACTS TABLE (Person-centric loan system)
-- =====================================================
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
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_loan_contacts_user_id (user_id)
);

-- =====================================================
-- LOAN ACTIVITIES TABLE
-- =====================================================
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
    FOREIGN KEY (contact_id) REFERENCES loan_contacts(id) ON DELETE CASCADE,
    INDEX idx_loan_activities_user_id (user_id),
    INDEX idx_loan_activities_contact_id (contact_id),
    INDEX idx_loan_activities_date (activity_date)
);

-- =====================================================
-- VIEW: Loan Contact with Balance
-- =====================================================
-- Note: MySQL doesn't support CTEs in the same way, we'll handle this in application code

-- =====================================================
-- STORED PROCEDURES (Optional - can also be handled in Python)
-- =====================================================

DELIMITER //

-- Procedure to add loan activity
CREATE PROCEDURE IF NOT EXISTS add_loan_activity(
    IN p_user_id INT,
    IN p_contact_id INT,
    IN p_activity_type VARCHAR(50),
    IN p_amount DECIMAL(15, 2),
    IN p_description TEXT,
    IN p_activity_date DATE
)
BEGIN
    DECLARE v_previous_balance DECIMAL(15, 2) DEFAULT 0;
    DECLARE v_new_balance DECIMAL(15, 2);
    
    -- Get previous balance
    SELECT COALESCE(
        (SELECT balance_after 
         FROM loan_activities 
         WHERE contact_id = p_contact_id 
         ORDER BY created_at DESC 
         LIMIT 1), 0
    ) INTO v_previous_balance;
    
    -- Calculate new balance based on activity type
    CASE p_activity_type
        WHEN 'given' THEN
            SET v_new_balance = v_previous_balance + p_amount;
        WHEN 'borrowed' THEN
            SET v_new_balance = v_previous_balance - p_amount;
        WHEN 'payment_received' THEN
            SET v_new_balance = v_previous_balance - p_amount;
        WHEN 'payment_made' THEN
            SET v_new_balance = v_previous_balance + p_amount;
        ELSE
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid activity type';
    END CASE;
    
    -- Insert activity
    INSERT INTO loan_activities (
        user_id,
        contact_id,
        activity_type,
        amount,
        balance_after,
        description,
        activity_date
    ) VALUES (
        p_user_id,
        p_contact_id,
        p_activity_type,
        p_amount,
        v_new_balance,
        p_description,
        p_activity_date
    );
    
    -- Update contact's updated_at
    UPDATE loan_contacts 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = p_contact_id;
    
END //

DELIMITER ;

