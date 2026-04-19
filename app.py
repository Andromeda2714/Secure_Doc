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
                phone_number VARCHAR(20),
                username VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                role VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add phone_number column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)")
            conn.commit()
        except:
            pass  # Column already exists
        
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
        import os
        file.save(os.path.join('uploads', filename))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO documentupload (username, doc_type, file_name) VALUES (%s, %s, %s)',
                       (user['username'], doc_type, filename))
        
        # Add a notification for verifiers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100),
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE
        )""")
        msg = f"New document ({doc_type}) uploaded by {user['username']}."
        cursor.execute("INSERT INTO notifications (username, message) VALUES ('role_verifier', %s)", (msg,))
        cursor.execute("INSERT INTO notifications (username, message) VALUES ('role_admin', %s)", (msg,))
        
        conn.commit()
        cursor.close()
        from flask import flash
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
        
        # Add a notification for the user
        cursor.execute("SELECT username, doc_type FROM documentupload WHERE id = %s", (doc_id,))
        doc_info = cursor.fetchone()
        if doc_info:
            username = doc_info[0] if type(doc_info) == tuple else doc_info['username']
            doc_type = doc_info[1] if type(doc_info) == tuple else doc_info['doc_type']
            msg = f"Your {doc_type} has been {action}."
            if comment:
                msg += f" Comments: {comment}"
            
            # Ensure notifications table exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100),
                message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE
            )""")
            
            cursor.execute("INSERT INTO notifications (username, message) VALUES (%s, %s)", (username, msg))

        conn.commit()
        cursor.close()
    return redirect(url_for('verifier.verifier_dashboard'))

@app.route('/api/notifications')
def get_notifications():
    if 'user' not in session:
        return {'notifications': []}
        
    username = session['user']['username']
    role = session['user']['role']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ensure notifications table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100),
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_read BOOLEAN DEFAULT FALSE
    )""")
    
    # Users see their own, Admins and Verifiers might see system alerts or their own. 
    # Since prompt says "work for user, admin and verifier", we will fetch notifications aimed at their username
    # or general ones (like username 'all')
    if role == 'Verifier':
        cursor.execute("SELECT * FROM notifications WHERE username = %s OR username = 'all' OR username = 'role_verifier' ORDER BY created_at DESC LIMIT 10", (username,))
    elif role == 'Admin':
        cursor.execute("SELECT * FROM notifications WHERE username = %s OR username = 'all' OR username = 'role_admin' ORDER BY created_at DESC LIMIT 10", (username,))
    elif role == 'User':
        cursor.execute("SELECT * FROM notifications WHERE username = %s OR username = 'all' OR username = 'role_user' ORDER BY created_at DESC LIMIT 10", (username,))
    else:
        cursor.execute("SELECT * FROM notifications WHERE username = %s OR username = 'all' ORDER BY created_at DESC LIMIT 10", (username,))
    notifs = cursor.fetchall()
    
    # Format datetime for JSON serialization
    for n in notifs:
        if n.get('created_at'):
            n['created_at'] = n['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    
    unread_count = sum(1 for n in notifs if not n.get('is_read'))
    
    conn.commit()
    cursor.close()
    
    return {'notifications': notifs, 'unread_count': unread_count}

@app.route('/api/notifications/read', methods=['POST'])
def mark_notifications_read():
    if 'user' not in session:
        return {'success': False}
    username = session['user']['username']
    role = session['user']['role']
    conn = get_db_connection()
    cursor = conn.cursor()
    if role == 'Verifier':
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE username = %s OR username = 'all' OR username = 'role_verifier'", (username,))
    elif role == 'Admin':
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE username = %s OR username = 'all' OR username = 'role_admin'", (username,))
    elif role == 'User':
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE username = %s OR username = 'all' OR username = 'role_user'", (username,))
    else:
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE username = %s OR username = 'all'", (username,))
    conn.commit()
    cursor.close()
    return {'success': True}

@app.after_request
def inject_notification_script(response):
    if response.direct_passthrough:
        return response
    if response.content_type == 'text/html; charset=utf-8':
        html = response.get_data(as_text=True)
        if 'bell-wrapper' in html:
            script = """
            <style>
                .notif-dropdown-menu { display: none; position: absolute; right: 0; top: 40px; background: white; width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 8px; z-index: 1000; color: #333; overflow: hidden; font-family: 'Segoe UI', Arial, sans-serif; cursor: default; }
                .notif-dropdown-menu.show { display: block; }
                .notif-header { padding: 12px; background: #516d8a; color: white; font-weight: bold; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
                .notif-item { padding: 12px; border-bottom: 1px solid #f1f1f1; font-size: 13px; line-height: 1.4; transition: background 0.2s; white-space: normal; text-align: left; }
                .notif-item:hover { background: #f9f9f9; }
                .notif-item.unread { background: #fdf5e6; font-weight: bold; }
                .notif-time { font-size: 11px; color: #888; margin-top: 4px; font-weight: normal; }
                .notif-mark-read { font-size: 12px; color: white; cursor: pointer; text-decoration: underline; background: none; border: none; padding: 0; font-family: inherit; }
                .notif-badge-dynamic { position: absolute; top: -5px; right: -8px; background: #e74c3c; color: white; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.2); display: none; }
            </style>
            <script>
                document.addEventListener('DOMContentLoaded', () => {
                    const bells = document.querySelectorAll('.bell-wrapper');
                    if (bells.length === 0) return;
                    
                    const bell = bells[0];
                    
                    // Clean up the old badge but keep the bell icon visible
                    const oldBadge = bell.querySelector('.notif-badge');
                    if (oldBadge) { oldBadge.remove(); }
                    
                    // Create new dynamic badge
                    const badge = document.createElement('span');
                    badge.className = 'notif-badge-dynamic';
                    bell.appendChild(badge);
                    
                    // Create dropdown menu
                    const dropdown = document.createElement('div');
                    dropdown.className = 'notif-dropdown-menu';
                    dropdown.id = 'notifDropdown';
                    bell.appendChild(dropdown);
                    
                    // Fetch notifications
                    fetch('/api/notifications')
                        .then(r => r.json())
                        .then(data => {
                            if (data.unread_count > 0) {
                                badge.textContent = data.unread_count;
                                badge.style.display = 'block';
                            }
                            
                            let html = '<div class="notif-header"><span>Notifications</span><button class="notif-mark-read" onclick="markRead(event)">Mark read</button></div>';
                            
                            if (data.notifications && data.notifications.length > 0) {
                                data.notifications.forEach(n => {
                                    let unreadClass = n.is_read ? '' : 'unread';
                                    html += '<div class="notif-item ' + unreadClass + '">' + n.message + '<div class="notif-time">' + n.created_at + '</div></div>';
                                });
                            } else {
                                html += '<div class="notif-item" style="text-align:center; color:#999; padding: 20px;">No notifications yet</div>';
                            }
                            dropdown.innerHTML = html;
                        });
                        
                    bell.addEventListener('click', (e) => {
                        e.stopPropagation();
                        dropdown.classList.toggle('show');
                    });
                    
                    document.addEventListener('click', (e) => {
                        if (!bell.contains(e.target)) {
                            dropdown.classList.remove('show');
                        }
                    });
                });
                
                function markRead(e) {
                    e.stopPropagation();
                    fetch('/api/notifications/read', {method: 'POST'})
                        .then(r => r.json())
                        .then(() => {
                            const badge = document.querySelector('.notif-badge-dynamic');
                            if(badge) badge.style.display = 'none';
                            const items = document.querySelectorAll('.notif-item.unread');
                            items.forEach(item => item.classList.remove('unread'));
                        });
                }
            </script>
            """
            html = html.replace('</body>', script + '</body>')
            response.set_data(html)
    return response

if __name__ == "__main__":
    # Create uploads directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Run app
    app.run(host="0.0.0.0", port=3000, debug=True, use_reloader=False)
