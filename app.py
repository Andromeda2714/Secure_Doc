"""
Flask Application - Secure Document Verification System
Modularized blueprint-based architecture with role-based authorization
"""
import os
from datetime import datetime
import mysql.connector
from flask import Flask, session, redirect, url_for, request, send_from_directory, g, flash
from routes import auth_bp, admin_bp, verifier_bp, user_bp
from utils.db import get_db_connection, close_db_connection, DATABASE_CONFIG

# Initialize Flask App
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(verifier_bp)
app.register_blueprint(user_bp)

# Database initialization
def init_db():
    """Initialize database tables using a direct (non-pooled) connection"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fullname VARCHAR(255),
                email VARCHAR(255) UNIQUE,
                dob DATE,
                username VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                role VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create documentupload table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentupload (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255),
                doc_type VARCHAR(100),
                file_name VARCHAR(255),
                status VARCHAR(50) DEFAULT 'Pending',
                comments TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database initialization warning: {e}")
        print("App will start but database features may not work")

# Teardown function for database cleanup
@app.teardown_appcontext
def teardown_db(exception=None):
    """Return pooled connection at request end"""
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

# Shared utility routes (not specific to any role)
@app.route("/upload", methods=["POST"])
def upload():
    """Document upload endpoint"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    user = session['user']
    doc_type = request.form.get('doc_type')
    file = request.files.get('document_file')
    if file and doc_type:
        filename = file.filename
        file.save(os.path.join('uploads', filename))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO documentupload (username, doc_type, file_name) VALUES (%s, %s, %s)',
                       (user['username'], doc_type, filename))
        conn.commit()
        cursor.close()
        flash('Upload successful')
    return redirect(url_for('user.user_dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory('uploads', filename)

@app.route("/verify_action", methods=["POST"])
def verify_action():
    """Verify (approve/reject) document action"""
    if 'user' not in session or session['user']['role'] != 'Verifier':
        return redirect(url_for('auth.login'))
    doc_id = request.form.get('id')
    action = request.form.get('action')
    comment = request.form.get('comment', '')
    if doc_id and action:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE documentupload SET status = %s, comments = %s WHERE id = %s',
                       (action, comment, doc_id))
        conn.commit()
        cursor.close()
    return redirect(url_for('verifier.verifier_dashboard'))

if __name__ == "__main__":
    # Create uploads directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Run app
    app.run(host="0.0.0.0", port=3000, debug=True, use_reloader=False)
