"""Authentication routes (Login, Register, Logout)"""
import mysql.connector
from flask import Blueprint, request, redirect, url_for, flash, send_from_directory, session
from utils.db import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/")
def index():
    return send_from_directory('static', 'index.html')

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
            user = cursor.fetchone()
            
            if user:
                cursor.close()
                session['user'] = user
                if user['role'] == 'Admin':
                    return redirect(url_for('admin.admin_dashboard'))
                elif user['role'] == 'Verifier':
                    return redirect(url_for('verifier.verifier_dashboard'))
                else:
                    return redirect(url_for('user.user_dashboard'))
            else:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100),
                    message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE
                )""")
                msg = f"SECURITY BREACH: Failed login attempt for username '{username}'."
                cursor.execute("INSERT INTO notifications (username, message) VALUES ('role_admin', %s)", (msg,))
                conn.commit()
                cursor.close()
                flash('Invalid credentials')
                return redirect(url_for('auth.login'))
    return send_from_directory('static', 'login.html')

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        dob = request.form.get('dob')
        phone_number = request.form.get('phone_number')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        if fullname and email and dob and phone_number and username and password and role:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (fullname, email, dob, phone_number, username, password, role) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                               (fullname, email, dob, phone_number, username, password, role))
                
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100),
                    message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE
                )""")
                msg = f"New user registered: {fullname} ({username}) as {role}."
                cursor.execute("INSERT INTO notifications (username, message) VALUES ('role_admin', %s)", (msg,))
                
                conn.commit()
                flash('Registration successful')
                return redirect(url_for('auth.login'))
            except mysql.connector.IntegrityError:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100),
                    message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE
                )""")
                msg = f"SECURITY BREACH: Duplicate registration attempt for '{username}' or '{email}'."
                cursor.execute("INSERT INTO notifications (username, message) VALUES ('role_admin', %s)", (msg,))
                conn.commit()
                flash('Username or email already exists')
            finally:
                cursor.close()
    return send_from_directory('static', 'register.html')


@auth_bp.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.index'))
