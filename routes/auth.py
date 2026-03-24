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
            cursor.close()
            if user:
                session['user'] = user
                if user['role'] == 'Admin':
                    return redirect(url_for('admin.admin_dashboard'))
                elif user['role'] == 'Verifier':
                    return redirect(url_for('verifier.verifier_dashboard'))
                else:
                    return redirect(url_for('user.user_dashboard'))
            else:
                flash('Invalid credentials')
                return redirect(url_for('auth.login'))
    return send_from_directory('static', 'login.html')

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        dob = request.form.get('dob')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        if fullname and email and dob and username and password and role:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (fullname, email, dob, username, password, role) VALUES (%s, %s, %s, %s, %s, %s)',
                               (fullname, email, dob, username, password, role))
                conn.commit()
                flash('Registration successful')
                return redirect(url_for('auth.login'))
            except mysql.connector.IntegrityError:
                flash('Username or email already exists')
            finally:
                cursor.close()
    return send_from_directory('static', 'register.html')


@auth_bp.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login'))
