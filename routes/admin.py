from flask import Blueprint, render_template_string, session, redirect, url_for, request, flash, jsonify
from utils.db import get_db_connection
from datetime import datetime
import mysql.connector

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return redirect(url_for('auth.login'))

    active_user = session['user']['username']
    user_full = 'Unknown'
    user_email = 'Unknown'
    user_role = 'Admin'
    user_dob = 'Unknown'
    total_users = total_docs = pending_count = 0

    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute('SELECT fullname, email, role, dob FROM users WHERE username = %s', (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM documentupload')
        total_docs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM documentupload WHERE status = 'Pending'")
        pending_count = cursor.fetchone()[0]

        cursor.close()
    except Exception:
        pass

    badge_html = f'<span class="notif-badge">{pending_count}</span>' if pending_count > 0 else ''

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f9fd; }}
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3f5371; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 5px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background: #3f5371; border-left: 5px solid white; }}
        .logout {{ padding: 15px 20px; background: #3f5371; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: #333; }}
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; }}
        .notif-badge {{ position: absolute; top: -6px; right: -7px; background: #e74c3c; color: white; font-size: 11px; padding: 2px 6px; border-radius: 50%; border: 2px solid white; }}
        .profile-menu {{ position: relative; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background: white; border: 1px solid #ddd; border-radius: 8px; min-width: 230px; box-shadow: 0 8px 16px rgba(0,0,0,0.15); z-index: 100; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3f5371; color: white; padding: 15px; text-align: center; }}
        .profile-details {{ padding: 15px; }}
        .profile-details p {{ margin: 4px 0; font-size: 14px; }}
        .dashboard-body {{ padding: 30px; background: #edf4fb; flex: 1; }}
        .stats-grid {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; border-radius: 8px; padding: 20px; flex: 1; box-shadow: 0 2px 6px rgba(0,0,0,0.05); border-top: 4px solid #516d8a; }}
        .stat-card h1 {{ margin: 0; color: #243e61; }}
        .stat-card p {{ margin: 6px 0 0; color: #7d8ca3; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">SecureDoc Admin</div>
        <ul class="nav-links">
            <li><a href="/admin_dashboard" class="active">System Overview</a></li>
            <li><a href="/user_management">User Management</a></li>
            <li><a href="/deactivation_center">Deactivation Center</a></li>
            <li><a href="/compliance_manager">Compliance Manager</a></li>
            <li><a href="/audit">Audit Trails</a></li>
        </ul>
        <a class="logout" href="/logout">Secure Logout</a>
    </div>
    <div class="main-content">
        <div class="topbar">
            <h2>Administrator Dashboard</h2>
            <div class="topbar-right">
                <div class="bell-wrapper">🔔{badge_html}</div>
                <div class="profile-menu" onclick="document.getElementById('adminDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="adminDrop" class="profile-dropdown">
                        <div class="profile-header"><h3 style="margin:0">{user_full}</h3></div>
                        <div class="profile-details">
                            <p>Username: {active_user}</p>
                            <p>Email: {user_email}</p>
                            <p>DOB: {user_dob}</p>
                            <p>Role: {user_role}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="dashboard-body">
            <div class="stats-grid">
                <div class="stat-card"><p>Registered Users</p><h1>{total_users}</h1></div>
                <div class="stat-card"><p>Total Documents</p><h1>{total_docs}</h1></div>
                <div class="stat-card"><p>Pending Validations</p><h1>{pending_count}</h1></div>
            </div>
        </div>
    </div>
    <script>
        window.onclick = function(event) {{
            if (!event.target.closest('.profile-menu')) {{
                var dropdown = document.getElementById('adminDrop');
                if (dropdown && dropdown.classList.contains('show')) dropdown.classList.remove('show');
            }}
        }}
    </script>
</body>
</html>
""")

@admin_bp.route('/user_management', methods=['GET', 'POST'])
def user_management():
    if 'user' not in session or session['user']['role'] != 'Admin':
        return redirect(url_for('auth.login'))

    active_user = session['user']['username']
    if request.method == 'POST':
        new_user = request.form.get('new_user')
        new_full = request.form.get('new_full')
        new_email = request.form.get('new_email')
        new_password = request.form.get('new_password')
        new_dob = request.form.get('new_dob')
        new_role = request.form.get('new_role')
        if new_user and new_full and new_email and new_password and new_dob and new_role:
            try:
                db = get_db_connection()
                cursor = db.cursor()
                cursor.execute('INSERT INTO users (fullname, email, dob, username, password, role) VALUES (%s, %s, %s, %s, %s, %s)',
                               (new_full, new_email, new_dob, new_user, new_password, new_role))
                db.commit()
                cursor.close()
                flash('User added successfully')
            except mysql.connector.IntegrityError:
                flash('Username or email already exists')
            except Exception:
                flash('Error adding user')
        else:
            flash('All fields are required')
        return redirect(url_for('admin.user_management'))

    user_full, user_email, user_role, user_dob = 'Unknown', 'Unknown', 'Admin', 'Unknown'
    user_rows = ''
    pending_count = 0
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute('SELECT fullname, email, role, dob FROM users WHERE username = %s', (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile

        cursor.execute('SELECT username, fullname, email, role, dob FROM users')
        all_users = cursor.fetchall()
        for u in all_users:
            uname, fname, email, role, dob = u
            user_rows += f"<tr><td>{uname}</td><td>{fname}</td><td>{email}</td><td>{dob}</td><td><b>{role}</b></td></tr>"

        cursor.execute("SELECT COUNT(*) FROM documentupload WHERE status = 'Pending'")
        pending_count = cursor.fetchone()[0]
        cursor.close()
    except Exception:
        pass

    badge_html = f'<span class="notif-badge">{pending_count}</span>' if pending_count > 0 else ''

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>User Management - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f9fd; }}
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3f5371; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 5px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background: #3f5371; border-left: 5px solid white; }}
        .logout {{ padding: 15px 20px; background: #3f5371; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: #333; }}
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; }}
        .notif-badge {{ position: absolute; top: -6px; right: -7px; background: #e74c3c; color: white; font-size: 11px; padding: 2px 6px; border-radius: 50%; border: 2px solid white; }}
        .profile-menu {{ position: relative; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background: white; border: 1px solid #ddd; border-radius: 8px; min-width: 230px; box-shadow: 0 8px 16px rgba(0,0,0,0.15); z-index: 100; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3f5371; color: white; padding: 15px; text-align: center; }}
        .profile-details {{ padding: 15px; }}
        .profile-details p {{ margin: 4px 0; font-size: 14px; }}
        .dashboard-body {{ padding: 30px; background: #edf4fb; flex: 1; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); }}
        .registration-form {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
        .form-group {{ display: flex; flex-direction: column; }}
        .form-group label {{ font-size: 12px; font-weight: bold; color: #516d8a; margin-bottom: 5px; }}
        .form-group input, .form-group select {{ padding: 10px; border: 1px solid #ccc; border-radius: 4px; }}
        .btn-add {{ background: #27ae60; color: white; padding: 10px 12px; border: none; border-radius: 4px; cursor: pointer; }}
        .btn-add:hover {{ background: #219150; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f0f3fb; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">SecureDoc Admin</div>
        <ul class="nav-links">
            <li><a href="/admin_dashboard">System Overview</a></li>
            <li><a href="/user_management" class="active">User Management</a></li>
            <li><a href="/deactivation_center">Deactivation Center</a></li>
            <li><a href="/compliance_manager">Compliance Manager</a></li>
            <li><a href="/audit">Audit Trails</a></li>
        </ul>
        <a class="logout" href="/logout">Secure Logout</a>
    </div>
    <div class="main-content">
        <div class="topbar">
            <h2>User Management</h2>
            <div class="topbar-right">
                <div class="bell-wrapper">🔔{badge_html}</div>
                <div class="profile-menu" onclick="document.getElementById('adminDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="adminDrop" class="profile-dropdown">
                        <div class="profile-header"><h3 style="margin:0">{user_full}</h3></div>
                        <div class="profile-details">
                            <p>Username: {active_user}</p>
                            <p>Email: {user_email}</p>
                            <p>DOB: {user_dob}</p>
                            <p>Role: {user_role}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="dashboard-body">
            <div class="card">
                <h3 style="margin-top:0">Register New System User</h3>
                <form method="POST" class="registration-form">
                    <div class="form-group"><label>Username</label><input type="text" name="new_user" placeholder="e.g. johndoe123"></div>
                    <div class="form-group"><label>Full Name</label><input type="text" name="new_full" placeholder="e.g. John Doe"></div>
                    <div class="form-group"><label>Email Address</label><input type="email" name="new_email" placeholder="e.g. john@example.com"></div>
                    <div class="form-group"><label>Password</label><input type="password" name="new_password" placeholder="••••••••"></div>
                    <div class="form-group"><label>Date of Birth</label><input type="date" name="new_dob"></div>
                    <div class="form-group"><label>System Role</label><select name="new_role"><option value="User">Standard User</option><option value="Verifier">Verifier</option><option value="Admin">Administrator</option></select></div>
                    <div class="form-group full-width"><button type="submit" class="btn-add">Add New User</button></div>
                </form>
            </div>
            <div class="card">
                <h3>Registered System Users</h3>
                <table><thead><tr><th>Username</th><th>Full Name</th><th>Email</th><th>DOB</th><th>Role</th></tr></thead><tbody>{user_rows}</tbody></table>
            </div>
        </div>
    </div>
    <script>
        window.onclick = function(event) {{
            if (!event.target.closest('.profile-menu')) {{
                var dropdown = document.getElementById('adminDrop');
                if (dropdown && dropdown.classList.contains('show')) dropdown.classList.remove('show');
            }}
        }}
    </script>
</body>
</html>
""")

    if 'user' not in session or session['user']['role'] != 'Admin':
        return redirect(url_for('auth.login'))
    
    active_user = session['user']['username']
    
    # Handle POST request for adding new user
    if request.method == 'POST':
        new_user = request.form.get('new_user')
        new_full = request.form.get('new_full')
        new_email = request.form.get('new_email')
        new_password = request.form.get('new_password')
        new_dob = request.form.get('new_dob')
        new_role = request.form.get('new_role')
        
        if new_user and new_full and new_email and new_password and new_dob and new_role:
            try:
                db = get_db_connection()
                cursor = db.cursor()
                cursor.execute('INSERT INTO users (fullname, email, dob, username, password, role, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                               (new_full, new_email, new_dob, new_user, new_password, new_role, datetime.now()))
                db.commit()
                cursor.close()
                flash('User added successfully')
            except mysql.connector.IntegrityError:
                flash('Username or email already exists')
            except Exception as e:
                flash('Error adding user')
        else:
            flash('All fields are required')
        
        return redirect(url_for('admin.user_management'))
    
    # Initialize variables for GET request
    user_full = "Unknown"
    user_email = "Unknown"
    user_role = "Admin"
    user_dob = "Unknown"
    pending_count = 0
    user_rows = ""
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # 1. Fetch Admin Profile for the dropdown
        cursor.execute("SELECT fullname, email, role, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile
    
        # 2. Fetch all registered users for the table
        cursor.execute("SELECT username, fullname, email, role, dob FROM users")
        all_users = cursor.fetchall()
        
        # 3. Fetch Pending count for the notification bell
        cursor.execute("SELECT COUNT(*) FROM documentupload WHERE status = 'Pending'")
        pending_count = cursor.fetchone()[0]
        
        cursor.close()
        
        for user in all_users:
            uname, fname, email, role, dob = user
            user_rows += f"<tr><td>{uname}</td><td>{fname}</td><td>{email}</td><td>{dob}</td><td><b>{role}</b></td></tr>"
    except Exception:
        all_users = []
        pending_count = 0
    
    # 4. PRE-CALCULATE THE BADGE HTML (Fixes the text-render error)
    badge_html = ""
    if pending_count > 0:
        badge_html = f'<span class="notif-badge">{pending_count}</span>'
    
    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>User Management - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; }}
        
        /* Sidebar Styles */
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 4px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background: #3e546a; border-left: 4px solid white; padding-left: 25px; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}

        /* Main Content & Topbar */
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: #333; }}
        
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; transition: 0.3s; }}
        .notif-badge {{ position: absolute; top: -5px; right: -8px; background: #e74c3c; color: white; font-size: 11px; padding: 2px 6px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}

        /* Profile Dropdown */
        .profile-menu {{ position: relative; display: inline-block; cursor: pointer; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background-color: white; min-width: 250px; box-shadow: 0px 8px 16px rgba(0,0,0,0.15); z-index: 100; border-radius: 8px; overflow: hidden; border: 1px solid #ddd; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3e546a; color: white; padding: 15px; text-align: center; }}
        .profile-details {{ padding: 15px; color: #333; }}
        .profile-details p {{ margin: 0 0 10px 0; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}

        /* Form & Table Styles */
        .dashboard-body {{ padding: 40px; background: #f8f9fa; flex: 1; }}
        .card {{ background: white; padding: 25px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 25px; border-top: 4px solid #516d8a; }}
        .registration-form {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
        .form-group {{ display: flex; flex-direction: column; }}
        .form-group label {{ font-size: 12px; font-weight: bold; color: #516d8a; margin-bottom: 5px; text-transform: uppercase; }}
        .form-group input, .form-group select {{ padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }}
        .full-width {{ grid-column: span 2; }}
        .btn-add {{ background: #27ae60; color: white; padding: 12px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 10px; }}
        .btn-add:hover {{ background: #219150; }}

        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 14px; }}
        th {{ background: #f8f9fa; color: #555; text-transform: uppercase; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">SecureDoc Admin</div>
        <ul class="nav-links">
            <li><a href="/admin_dashboard">System Overview</a></li>
            <li><a href="/user_management" class="active">User Management</a></li>
            <li><a href="/deactivation_center">Deactivation Center</a></li>
            <li><a href="/compliance_manager">Compliance Manager</a></li>
            <li><a href="/audit">Audit Trails</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2>User Management</h2>
            <div class="topbar-right">
                <div class="bell-wrapper">
                    🔔
                    {badge_html}
                </div>
                
                <div class="profile-menu" onclick="document.getElementById('adminDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="adminDrop" class="profile-dropdown">
                        <div class="profile-header">
                            <h3 style="margin:0;">{user_full}</h3>
                            <p style="margin:5px 0 0 0; font-size:12px; opacity:0.9;">ADMINISTRATOR</p>
                        </div>
                        <div class="profile-details">
                            <p><strong>Username:</strong> {active_user}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="dashboard-body">
            <div class="card">
                <h3 style="margin-top:0;">Register New System User</h3>
                <form method="POST" class="registration-form">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" name="new_user" placeholder="e.g. johndoe123">
                    </div>
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" name="new_full" placeholder="e.g. John Doe">
                    </div>
                    <div class="form-group">
                        <label>Email Address</label>
                        <input type="email" name="new_email" placeholder="e.g. john@example.com">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="new_password" placeholder="••••••••">
                    </div>
                    <div class="form-group">
                        <label>Date of Birth</label>
                        <input type="date" name="new_dob">
                    </div>
                    <div class="form-group">
                        <label>System Role</label>
                        <select name="new_role">
                            <option value="User">Standard User</option>
                            <option value="Verifier">Verifier</option>
                            <option value="Admin">Administrator</option>
                        </select>
                    </div>
                    <div class="full-width">
                        <button type="submit" class="btn-add">Add New User</button>
                    </div>
                </form>
            </div>

            <div class="card">
                <h3>Registered System Users</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Full Name</th>
                            <th>Email</th>
                            <th>DOB</th>
                            <th>Role</th>
                        </tr>
                    </thead>
                    <tbody>
                        {user_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        window.onclick = function(event) {{
            if (!event.target.closest('.profile-menu')) {{
                let dropdowns = document.getElementsByClassName("profile-dropdown");
                for (let i = 0; i < dropdowns.length; i++) {{
                    if (dropdowns[i].classList.contains('show')) dropdowns[i].classList.remove('show');
                }}
            }}
        }}
    </script>
</body>
</html>
""")


@admin_bp.route("/toggle_user_status", methods=["POST"])
def toggle_user_status():
    if "user" not in session or session["user"]["role"] != "Admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    data = request.get_json()
    username = data.get("username")
    action = data.get("action")

    if not username or action not in ["deactivate", "reactivate"]:
        return jsonify({"success": False, "message": "Invalid request"}), 400

    try:
        db = get_db_connection()
        cursor = db.cursor()
        new_role = "Deactivated" if action == "deactivate" else "User"
        cursor.execute("UPDATE users SET role = %s WHERE username = %s", (new_role, username))
        db.commit()
        cursor.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/deactivation_center")
def deactivation_center():
    if "user" not in session or session["user"]["role"] != "Admin":
        return redirect(url_for("auth.login"))

    active_user = session["user"]["username"]
    user_full = "Unknown"
    user_email = "Unknown"
    user_role = "Admin"
    user_dob = "Unknown"
    system_users = []
    pending_count = 0

    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Fetch admin profile
        cursor.execute("SELECT fullname, email, role, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile

        # Fetch pending count for notification
        cursor.execute("SELECT COUNT(*) FROM documentupload WHERE status = 'Pending'")
        pending_count = cursor.fetchone()[0]

        # Fetch all users except current admin
        cursor.execute("SELECT username, fullname, email, role FROM users WHERE username != %s", (active_user,))
        system_users = cursor.fetchall()
        
        cursor.close()
    except Exception:
        pass

    # Build badge HTML
    badge_html = f'<span class="notif-badge">{pending_count}</span>' if pending_count > 0 else ''
    
    # Build user rows HTML
    user_rows = ""
    for user in system_users:
        uname, fname, email, role = user
        status = "Active" if role != "Deactivated" else "Deactivated"
        action_btn = "Deactivate" if role != "Deactivated" else "Reactivate"
        action_cmd = "deactivate" if role != "Deactivated" else "reactivate"
        user_rows += f"<tr><td>{uname}</td><td>{fname}</td><td>{role}</td><td><form action='/toggle_user_status' method='POST' style='margin:0;'><input type='hidden' name='username' value='{uname}'><input type='hidden' name='action' value='{action_cmd}'><button type='submit' class='btn-deactivate' onclick=\"return confirm('Are you sure you want to {action_cmd} {uname}?');\">{action_btn}</button></form></td></tr>"

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Deactivation Center - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; }}
        
        /* Sidebar Styles */
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 4px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background: #3e546a; border-left: 4px solid white; padding-left: 25px; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}

        /* Main Content & Topbar */
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: #333; }}
        
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; transition: 0.3s; }}
        .notif-badge {{ position: absolute; top: -5px; right: -8px; background: #e74c3c; color: white; font-size: 11px; padding: 2px 6px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}

        /* Profile Dropdown */
        .profile-menu {{ position: relative; display: inline-block; cursor: pointer; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background-color: white; min-width: 250px; box-shadow: 0px 8px 16px rgba(0,0,0,0.15); z-index: 100; border-radius: 8px; overflow: hidden; border: 1px solid #ddd; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3e546a; color: white; padding: 15px; text-align: center; }}
        .profile-details {{ padding: 15px; color: #333; }}
        .profile-details p {{ margin: 0 0 10px 0; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}

        /* Table & Cards */
        .dashboard-body {{ padding: 40px; background: #f8f9fa; flex: 1; }}
        .card {{ background: white; padding: 30px; border-radius: 8px; border: 1px solid #e0e0e0; border-top: 4px solid #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; color: #555; text-transform: uppercase; font-size: 12px; }}
        
        .btn-deactivate {{ background: #e74c3c; color: white; padding: 6px 12px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; transition: 0.3s; }}
        .btn-deactivate:hover {{ background: #c0392b; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">SecureDoc Admin</div>
        <ul class="nav-links">
            <li><a href="/admin_dashboard">System Overview</a></li>
            <li><a href="/user_management">User Management</a></li>
            <li><a href="/deactivation_center" class="active">Deactivation Center</a></li>
            <li><a href="/compliance_manager">Compliance Manager</a></li>
            <li><a href="/audit">Audit Trails</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2>Account Deactivation Center</h2>
            <div class="topbar-right">
                <div class="bell-wrapper">
                    🔔
                    {badge_html}
                </div>
                
                <div class="profile-menu" onclick="document.getElementById('adminDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="adminDrop" class="profile-dropdown">
                        <div class="profile-header">
                            <h3 style="margin:0;">{user_full}</h3>
                            <p style="margin:5px 0 0 0; font-size:12px; opacity:0.9;">ADMINISTRATOR</p>
                        </div>
                        <div class="profile-details">
                            <p><strong>Username:</strong> {active_user}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="dashboard-body">
            <div class="card">
                <h3 style="margin-top: 0; color: #e74c3c;">System Access Control</h3>
                <p style="color: #666; font-size: 14px;">Warning: Deactivating a user will immediately revoke their access to all portals. This action is logged in the Audit Trail.</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Full Name</th>
                            <th>Role</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {user_rows if system_users else '<tr><td colspan="4" style="text-align:center; padding: 20px;">No other active users found.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        window.onclick = function(event) {{
            if (!event.target.closest('.profile-menu')) {{
                let dropdowns = document.getElementsByClassName("profile-dropdown");
                for (let i = 0; i < dropdowns.length; i++) {{
                    if (dropdowns[i].classList.contains('show')) {{
                        dropdowns[i].classList.remove('show');
                    }}
                }}
            }}
        }}
    </script>
</body>
</html>
""")


@admin_bp.route("/compliance_manager")
def compliance_manager():
    if "user" not in session or session["user"]["role"] != "Admin":
        return redirect(url_for("auth.login"))

    active_user = session["user"]["username"]
    user_full = "Unknown"
    user_email = "Unknown"
    user_role = "Admin"
    user_dob = "Unknown"
    pending_count = 0

    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Fetch admin profile
        cursor.execute("SELECT fullname, email, role, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile

        # Fetch pending count
        cursor.execute("SELECT COUNT(*) FROM documentupload WHERE status = 'Pending'")
        pending_count = cursor.fetchone()[0]
        
        cursor.close()
    except Exception:
        pass

    # Build badge HTML
    badge_html = f'<span class="notif-badge">{pending_count}</span>' if pending_count > 0 else ''

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Compliance Manager - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; }}
        
        /* Sidebar Styles - Grayish Blue */
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 4px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background: #3e546a; border-left: 4px solid white; padding-left: 25px; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}

        /* Main Content & Topbar */
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: #333; }}
        
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; transition: 0.3s; }}
        .notif-badge {{ position: absolute; top: -5px; right: -8px; background: #e74c3c; color: white; font-size: 11px; padding: 2px 6px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}

        /* Profile Dropdown */
        .profile-menu {{ position: relative; display: inline-block; cursor: pointer; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background-color: white; min-width: 250px; box-shadow: 0px 8px 16px rgba(0,0,0,0.15); z-index: 100; border-radius: 8px; overflow: hidden; border: 1px solid #ddd; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3e546a; color: white; padding: 15px; text-align: center; }}
        .profile-details {{ padding: 15px; color: #333; }}
        .profile-details p {{ margin: 0 0 10px 0; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}

        /* Manager Content */
        .dashboard-body {{ padding: 40px; background: #f8f9fa; flex: 1; }}
        .card {{ background: white; padding: 30px; border-radius: 8px; border: 1px solid #e0e0e0; border-top: 4px solid #516d8a; margin-bottom: 25px; }}
        .card h3 {{ color: #3e546a; margin-top: 0; }}
        textarea {{ width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; margin: 10px 0; resize: vertical; }}
        .btn-update {{ background: #516d8a; color: white; padding: 10px 20px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }}
        .btn-update:hover {{ background: #3e546a; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">SecureDoc Admin</div>
        <ul class="nav-links">
            <li><a href="/admin_dashboard">System Overview</a></li>
            <li><a href="/user_management">User Management</a></li>
            <li><a href="/deactivation_center">Deactivation Center</a></li>
            <li><a href="/compliance_manager" class="active">Compliance Manager</a></li>
            <li><a href="/audit">Audit Trails</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2>Compliance Standards Manager</h2>
            <div class="topbar-right">
                <div class="bell-wrapper">
                    🔔
                    {badge_html}
                </div>
                
                <div class="profile-menu" onclick="document.getElementById('adminDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="adminDrop" class="profile-dropdown">
                        <div class="profile-header">
                            <h3 style="margin:0;">{user_full}</h3>
                            <p style="margin:5px 0 0 0; font-size:12px; opacity:0.9;">ADMINISTRATOR</p>
                        </div>
                        <div class="profile-details">
                            <p><strong>Username:</strong> {active_user}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="dashboard-body">
            <div class="card">
                <h3>Global Identification Standards</h3>
                <p style="font-size: 14px; color: #666;">This content is displayed to Verifiers during document review.</p>
                <form action="/update_compliance" method="POST">
                    <textarea name="id_guidelines">1. Must be a government-issued ID (Passport, Driver's License).
2. The name on the ID must match the System Data name.
3. The image must be clear and legible.</textarea>
                    <button type="submit" class="btn-update">Update ID Guidelines</button>
                </form>
            </div>

            <div class="card">
                <h3>Form Compliance Rules</h3>
                <form action="/update_compliance" method="POST">
                    <textarea name="form_guidelines">1. Must be the most recent version of the compliance document.
2. User signatures must be present and dated.
3. Any incomplete fields result in immediate rejection.</textarea>
                    <button type="submit" class="btn-update">Update Form Rules</button>
                </form>
            </div>
        </div>
    </div>

    <script>
        window.onclick = function(event) {{
            if (!event.target.closest('.profile-menu')) {{
                let dropdowns = document.getElementsByClassName("profile-dropdown");
                for (let i = 0; i < dropdowns.length; i++) {{
                    if (dropdowns[i].classList.contains('show')) {{
                        dropdowns[i].classList.remove('show');
                    }}
                }}
            }}
        }}
    </script>
</body>
</html>
""")


@admin_bp.route("/audit")
def audit():
    if "user" not in session or session["user"]["role"] != "Admin":
        return redirect(url_for("auth.login"))

    active_user = session["user"]["username"]
    audit_records = []

    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Fetch audit trail records
        cursor.execute("SELECT id, username, doc_type, file_name, status FROM documentupload ORDER BY id DESC")
        audit_records = cursor.fetchall()
        
        cursor.close()
    except Exception:
        pass

    # Build audit rows HTML with status badges
    audit_rows = ""
    for row in audit_records:
        doc_id, uname, dtype, fname, status = row
        status_class = f"status-{status}"
        badge = f'<span class="status-badge {status_class}">{status}</span>'
        doc_link = f'<a href="/uploads/{fname}" target="_blank" style="color: #2980b9; text-decoration: none; font-weight: bold;">View Document</a>'
        audit_rows += f"<tr><td>SYS-{doc_id}</td><td><b>{uname}</b></td><td>{dtype}</td><td>{doc_link}</td><td>{badge}</td></tr>"

    if not audit_records:
        audit_rows = "<tr><td colspan='5' style='text-align: center; color: #7f8c8d;'>No records found in the system.</td></tr>"

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>System Audit Trail - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 40px; display: flex; flex-direction: column; align-items: center; }}
        .header {{ text-align: center; margin-bottom: 30px; color: #2c3e50; }}
        .audit-container {{ background: white; width: 90%; max-width: 1000px; padding: 30px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); border-top: 5px solid #2980b9; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #2980b9; color: white; }}
        tr:hover {{ background-color: #ecf0f1; }}
        .status-badge {{ padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; color: white; }}
        .status-Pending {{ background: #f39c12; }}
        .status-Approved {{ background: #27ae60; }}
        .status-Rejected {{ background: #e74c3c; }}
        .back-btn {{ display: inline-block; margin-bottom: 20px; padding: 10px 20px; background: #2c3e50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; transition: 0.2s; }}
        .back-btn:hover {{ background: #34495e; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Centralized System Audit Trail</h1>
        <p>Live tracking of all document submissions and compliance verification statuses.</p>
    </div>

    <div class="audit-container">
        <a href="/admin_dashboard" class="back-btn">&larr; Back to Admin Portal</a>
        
        <table>
            <tr>
                <th>Log ID</th>
                <th>Uploaded By</th>
                <th>Document Type</th>
                <th>File Reference</th>
                <th>Verification Status</th>
            </tr>
            {audit_rows}
        </table>
    </div>
</body>
</html>
""")
