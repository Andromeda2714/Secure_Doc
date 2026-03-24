from flask import Blueprint, render_template_string, session, redirect, url_for, request
from utils.db import get_db_connection

user_bp = Blueprint('user', __name__)

@user_bp.route("/user_dashboard")
def user_dashboard():
    if 'user' not in session or session['user']['role'] != 'User':
        return redirect(url_for('auth.login'))

    active_user = session['user']['username']

    # Initialize profile variables
    user_full = "Unknown"
    user_email = "Unknown"
    user_dob = "Unknown"
    user_docs = []
    notif_count = 0

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Fetch profile details for the Topbar Dropdown
        cursor.execute("SELECT fullname, email, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_dob = profile

        # Fetch document upload history for the table
        cursor.execute("SELECT id, doc_type, file_name, status, comments FROM documentupload WHERE username = %s ORDER BY id DESC", (active_user,))
        user_docs = cursor.fetchall()

        # Calculate notifications for Approved/Rejected docs
        for doc in user_docs:
            if doc[3] in ['Approved', 'Rejected']:
                notif_count += 1

    except Exception:
        pass

    # Build table rows
    rows = ""
    if user_docs:
        for doc in user_docs:
            doc_id, dtype, fname, status, comment = doc
            display_comment = comment if comment and comment.strip() else "-"
            rows += f"<tr><td>SYS-{doc_id}</td><td>{dtype}</td><td><a href='/uploads/{fname}' target='_blank' style='color:#516d8a; text-decoration:none;'>{fname}</a></td><td class='status-{status}'>{status}</td><td>{display_comment}</td></tr>"
    else:
        rows = "<tr><td colspan='5' style='text-align:center; padding:20px; color:#999;'>No documents found.</td></tr>"

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>User Workspace - SecureDoc Portal</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; }}

        /* Sidebar Navigation - Slate Blue Theme */
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 22px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 5px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background-color: #3e546a; border-left: 5px solid white; }}

        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; transition: 0.3s; }}
        .logout:hover {{ background-color: #2c3e50; }}

        /* Main Layout Styles */
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: #333; }}

        /* Topbar Utilities */
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .top-link {{ color: #64748b; text-decoration: none; font-weight: bold; font-size: 15px; transition: 0.3s; }}
        .top-link:hover {{ color: #516d8a; }}

        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; transition: 0.3s; }}
        .notif-badge {{ position: absolute; top: -5px; right: -8px; background-color: #e74c3c; color: white; font-size: 11px; font-weight: bold; padding: 2px 6px; border-radius: 50%; border: 2px solid white; }}

        /* Profile Dropdown Styling */
        .profile-menu {{ position: relative; display: inline-block; cursor: pointer; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .profile-dropdown {{
            display: none;
            position: absolute;
            right: 0;
            top: 45px;
            background-color: white;
            min-width: 260px;
            box-shadow: 0px 8px 16px rgba(0,0,0,0.15);
            z-index: 100;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #ddd;
        }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3e546a; color: white; padding: 15px; text-align: center; }}
        .profile-details {{ padding: 15px; text-align: left; }}
        .profile-details p {{ margin: 0 0 10px 0; font-size: 14px; color: #333; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        .profile-details strong {{ color: #516d8a; display: inline-block; width: 85px; }}

        /* Content Cards & Tables */
        .dashboard-body {{ padding: 40px; }}
        .card {{ background: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #516d8a; }}
        .card h3 {{ margin-top: 0; color: #333; font-size: 1.2rem; margin-bottom: 20px; }}

        input[type="text"], select, input[type="file"] {{ width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; background: #f9f9f9; }}
        .btn-upload {{ padding: 12px 25px; background-color: #516d8a; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; transition: 0.3s; }}
        .btn-upload:hover {{ background-color: #3e546a; }}

        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 14px 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background-color: #f8f9fa; color: #555; text-transform: uppercase; font-size: 12px; font-weight: 700; }}
        .status-Pending {{ color: #f39c12; font-weight: bold; }}
        .status-Approved {{ color: #27ae60; font-weight: bold; }}
        .status-Rejected {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>

    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/user_dashboard" class="active">My Dashboard</a></li>
            <li><a href="/my_submissions">My Submissions</a></li>
            <li><a href="/version_history">Version History</a></li>
            <li><a href="/support">Support</a></li>
            <li><a href="/faqs">FAQs</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2>User Workspace</h2>

            <div class="topbar-right">
                <a href="/support" class="top-link">Help</a>

                <div class="bell-wrapper" title="You have {notif_count} updates">
                    🔔
                    {'<span class="notif-badge">' + str(notif_count) + '</span>' if notif_count > 0 else ''}
                </div>

                <div class="profile-menu" onclick="document.getElementById('userDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="userDrop" class="profile-dropdown">
                        <div class="profile-header">
                            <h3 style="margin:0;">{user_full}</h3>
                            <p style="margin:5px 0 0 0; font-size:12px; opacity:0.8;">USER PROFILE</p>
                        </div>
                        <div class="profile-details">
                            <p><strong>Full Name:</strong> {user_full}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                            <p><strong>Username:</strong> {active_user}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="dashboard-body">
            <div class="card">
                <h3>Submit New Document</h3>
                <form action="/upload" method="POST" enctype="multipart/form-data">
                    <input type="text" name="username" value="{active_user}" readonly style="background:#eee; cursor:not-allowed;">
                    <select name="doc_type" required>
                        <option value="Compliance Form">Compliance Form</option>
                        <option value="Identification">Identification Document</option>
                        <option value="OPT Checklist">OPT Checklist</option>
                    </select>
                    <input type="file" name="document_file" required>
                    <button type="submit" class="btn-upload">Securely Upload File</button>
                </form>
            </div>

            <div class="card" style="border-top-color: #f39c12;">
                <h3>My Document Status</h3>
                <table>
                    <tr><th>Doc ID</th><th>Type</th><th>File Reference</th><th>Status</th><th>Verifier Feedback</th></tr>
                    {rows}
                </table>
            </div>
        </div>
    </div>

    <script>
        window.onclick = function(event) {{
            if (!event.target.closest('.profile-menu')) {{
                var dropdowns = document.getElementsByClassName("profile-dropdown");
                for (var i = 0; i < dropdowns.length; i++) {{
                    var openDropdown = dropdowns[i];
                    if (openDropdown.classList.contains('show')) {{
                        openDropdown.classList.remove('show');
                    }}
                }}
            }}
        }}
    </script>
</body>
</html>
""")

@user_bp.route("/my_submissions")
def my_submissions():
    if 'user' not in session or session['user']['role'] != 'User':
        return redirect(url_for('auth.login'))

    active_user = session['user']['username']

    user_full, user_email, user_dob = "Unknown", "Unknown", "Unknown"
    user_docs = []

    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT fullname, email, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile: user_full, user_email, user_dob = profile

        cursor.execute("SELECT id, doc_type, file_name, status, comments FROM documentupload WHERE username = %s ORDER BY id DESC", (active_user,))
        user_docs = cursor.fetchall()
    except Exception:
        pass

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>My Submissions - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; overflow: hidden; }}
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 22px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 5px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background-color: #3e546a; border-left: 5px solid white; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}

        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: #333; font-size: 1.5rem; }}

        /* Unified Topbar Alignment */
        .topbar-right {{ display: flex; align-items: center; gap: 20px; }}
        .top-link {{ color: #516d8a; text-decoration: none; font-weight: bold; font-size: 15px; }}
        .bell-icon {{ font-size: 20px; cursor: pointer; }}

        /* Fixed Dropdown Alignment */
        .profile-menu {{ position: relative; display: inline-block; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; cursor: pointer; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background: white; min-width: 260px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); z-index: 1000; border-radius: 8px; border: 1px solid #ddd; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3e546a; color: white; padding: 15px; text-align: center; border-radius: 8px 8px 0 0; }}
        .profile-details {{ padding: 15px; text-align: left; color: #333; }}
        .profile-details p {{ margin: 0 0 10px 0; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        .profile-details strong {{ color: #516d8a; width: 85px; display: inline-block; }}

        .card {{ background: white; padding: 30px; border-radius: 8px; margin: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #516d8a; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; color: #555; text-transform: uppercase; font-size: 12px; }}
        .status-Pending {{ color: #f39c12; font-weight: bold; }}
        .status-Approved {{ color: #27ae60; font-weight: bold; }}
        .status-Rejected {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/user_dashboard">Document Hub</a></li>
            <li><a href="/my_submissions" class="active">My Submissions</a></li>
            <li><a href="/version_history">Version History</a></li>
            <li><a href="/support">Support</a></li>
            <li><a href="/faqs">FAQs</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2>Submission Record</h2>
            <div class="topbar-right">
                <a href="/support" class="top-link">Help</a>
                <span class="bell-icon">🔔</span>
                <div class="profile-menu">
                    <div class="role-badge" onclick="document.getElementById('userDrop').classList.toggle('show')">{active_user}</div>
                    <div id="userDrop" class="profile-dropdown">
                        <div class="profile-header"><h3 style="margin:0;">{user_full}</h3><p style="margin:5px 0 0 0; font-size:11px; opacity:0.8;">USER PROFILE</p></div>
                        <div class="profile-details">
                            <p><strong>Full Name:</strong> {user_full}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                            <p><strong>User:</strong> {active_user}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="card">
            <table>
                <tr><th>Log ID</th><th>Category</th><th>File</th><th>Status</th><th>Notes</th></tr>
                {''.join([f"<tr><td>SYS-{d[0]}</td><td>{d[1]}</td><td><a href='/uploads/{d[2]}' style='color:#516d8a;'>{d[2]}</a></td><td class='status-{d[3]}'>{d[3]}</td><td>{d[4] if d[4] else '-'}</td></tr>" for d in user_docs]) if user_docs else "<tr><td colspan='5' style='text-align:center;'>No records found.</td></tr>"}
            </table>
        </div>
    </div>
    <script>window.onclick = function(e) {{ if (!e.target.closest('.profile-menu')) {{ var d = document.getElementById('userDrop'); if (d && d.classList.contains('show')) d.classList.remove('show'); }} }}</script>
</body>
</html>
""")

@user_bp.route("/version_history")
def version_history():
    if 'user' not in session or session['user']['role'] != 'User':
        return redirect(url_for('auth.login'))

    active_user = session['user']['username']

    user_full, user_email, user_dob = "Unknown", "Unknown", "Unknown"
    doc_history = {}

    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT fullname, email, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile: user_full, user_email, user_dob = profile

        cursor.execute("SELECT doc_type, file_name, status, comments FROM documentupload WHERE username = %s ORDER BY id ASC", (active_user,))
        for doc in cursor.fetchall():
            dtype = doc[0]
            if dtype not in doc_history: doc_history[dtype] = []
            doc_history[dtype].append(doc)
    except Exception:
        pass

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Version History - SecureDoc</title>
    <style>
        /* [Insert CSS from My Submissions here] */
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; overflow: hidden; }}
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 22px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 5px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background-color: #3e546a; border-left: 5px solid white; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: #333; font-size: 1.5rem; }}
        .topbar-right {{ display: flex; align-items: center; gap: 20px; }}
        .top-link {{ color: #516d8a; text-decoration: none; font-weight: bold; font-size: 15px; }}
        .bell-icon {{ font-size: 20px; cursor: pointer; }}
        .profile-menu {{ position: relative; display: inline-block; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; cursor: pointer; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background: white; min-width: 260px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); z-index: 1000; border-radius: 8px; border: 1px solid #ddd; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3e546a; color: white; padding: 15px; text-align: center; border-radius: 8px 8px 0 0; }}
        .profile-details {{ padding: 15px; text-align: left; color: #333; }}
        .profile-details p {{ margin: 0 0 10px 0; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        .profile-details strong {{ color: #516d8a; width: 85px; display: inline-block; }}
        .history-card {{ background: white; padding: 30px; border-radius: 8px; margin: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #516d8a; }}
        .version-badge {{ background: #eee; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; color: #555; text-transform: uppercase; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/user_dashboard">Document Hub</a></li>
            <li><a href="/my_submissions">My Submissions</a></li>
            <li><a href="/version_history" class="active">Version History</a></li>
            <li><a href="/support">Support</a></li>
            <li><a href="/faqs">FAQs</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>
    <div class="main-content">
        <div class="topbar">
            <h2>Version History</h2>
            <div class="topbar-right">
                <a href="/support" class="top-link">Help</a>
                <span class="bell-icon">🔔</span>
                <div class="profile-menu">
                    <div class="role-badge" onclick="document.getElementById('userDrop').classList.toggle('show')">{active_user}</div>
                    <div id="userDrop" class="profile-dropdown">
                        <div class="profile-header"><h3 style="margin:0;">{user_full}</h3><p>USER PROFILE</p></div>
                        <div class="profile-details">
                            <p><strong>Full Name:</strong> {user_full}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                             <p><strong>DOB:</strong> {user_dob}</p>
                            <p><strong>User:</strong> {active_user}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="dashboard-body">
            {"".join([f"<div class='history-card'><h3>{cat}</h3><table><tr><th>Iteration</th><th>File</th><th>Status</th></tr>" + "".join([f"<tr><td><span class='version-badge'>v1.0.{i+1}</span></td><td>{d[1]}</td><td>{d[2]}</td></tr>" for i, d in enumerate(docs)]) + "</table></div>" for cat, docs in doc_history.items()]) if doc_history else "<p style='margin:30px;'>No history found.</p>"}
        </div>
    </div>
    <script>window.onclick = function(e) {{ if (!e.target.closest('.profile-menu')) {{ var d = document.getElementById('userDrop'); if (d && d.classList.contains('show')) d.classList.remove('show'); }} }}</script>
</body>
</html>
""")

@user_bp.route("/support")
def support():
    if 'user' not in session or session['user']['role'] != 'User':
        return redirect(url_for('auth.login'))

    active_user = session['user']['username']

    user_full, user_email, user_dob = "Unknown", "Unknown", "Unknown"

    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT fullname, email, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile: user_full, user_email, user_dob = profile
    except Exception:
        pass

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Support - SecureDoc</title>
    <style>
        /* (Insert CSS from My Submissions) */
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; overflow: hidden; }}
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 22px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 5px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background-color: #3e546a; border-left: 5px solid white; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: #333; font-size: 1.5rem; }}
        .topbar-right {{ display: flex; align-items: center; gap: 20px; }}
        .top-link {{ color: #516d8a; text-decoration: none; font-weight: bold; font-size: 15px; }}
        .bell-icon {{ font-size: 20px; cursor: pointer; }}
        .profile-menu {{ position: relative; display: inline-block; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; cursor: pointer; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background: white; min-width: 260px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); z-index: 1000; border-radius: 8px; border: 1px solid #ddd; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3e546a; color: white; padding: 15px; text-align: center; border-radius: 8px 8px 0 0; }}
        .profile-details {{ padding: 15px; text-align: left; color: #333; }}
        .profile-details p {{ margin: 0 0 10px 0; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        .profile-details strong {{ color: #516d8a; width: 85px; display: inline-block; }}
        .contact-grid {{ display: flex; gap: 20px; padding: 30px; }}
        .contact-card {{ background: white; padding: 30px; border-radius: 8px; flex: 1; border-top: 5px solid #516d8a; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/user_dashboard">Document Hub</a></li>
            <li><a href="/my_submissions">My Submissions</a></li>
            <li><a href="/version_history">Version History</a></li>
            <li><a href="/support" class="active">Support</a></li>
            <li><a href="/faqs">FAQs</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>
    <div class="main-content">
        <div class="topbar">
            <h2>Support</h2>
            <div class="topbar-right">
                <span class="bell-icon">🔔</span>
                <div class="profile-menu">
                    <div class="role-badge" onclick="document.getElementById('userDrop').classList.toggle('show')">{active_user}</div>
                    <div id="userDrop" class="profile-dropdown">
                        <div class="profile-header"><h3>{user_full}</h3><p>USER PROFILE</p></div>
                        <div class="profile-details">
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                            <p><strong>User:</strong> {active_user}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="contact-grid">
            <div class="contact-card"><h3>Yamuna P.</h3><p>Engineer</p><a href="mailto:yamunadc20@gmail.com">yamunadc20@gmail.com</a></div>
            <div class="contact-card"><h3>Lakshmi B.</h3><p>Admin</p><a href="mailto:pasurlabhavani111@gmail.com">pasurlabhavani111@gmail.com</a></div>
        </div>
    </div>
    <script>window.onclick = function(e) {{ if (!e.target.closest('.profile-menu')) {{ var d = document.getElementById('userDrop'); if (d && d.classList.contains('show')) d.classList.remove('show'); }} }}</script>
</body>
</html>
""")

@user_bp.route("/faqs")
def faqs():
    if 'user' not in session or session['user']['role'] != 'User':
        return redirect(url_for('auth.login'))

    active_user = session['user']['username']

    user_full, user_email, user_dob = "Unknown", "Unknown", "Unknown"

    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT fullname, email, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_dob = profile
    except Exception:
        pass

    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FAQs - SecureDoc</title>
    <style>
        /* --- UNIFIED THEME COLORS --- */
        :root {{
            --primary-blue: #516d8a;
            --primary-hover: #3e546a;
            --bg-light: #f4f7f6;
            --text-dark: #333333;
        }}

        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: var(--bg-light); overflow: hidden; }}

        /* --- SIDEBAR --- */
        .sidebar {{ width: 250px; background: var(--primary-blue); color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: var(--primary-hover); text-align: center; font-weight: bold; font-size: 22px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 5px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background-color: var(--primary-hover); border-left: 5px solid white; }}
        .logout {{ padding: 15px 20px; background: var(--primary-hover); color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}

        /* --- MAIN CONTENT --- */
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar h2 {{ margin: 0; color: var(--text-dark); font-size: 1.5rem; }}

        .topbar-right {{ display: flex; align-items: center; gap: 20px; }}
        .top-link {{ color: var(--primary-blue); text-decoration: none; font-weight: bold; font-size: 15px; }}

        /* --- PROFILE DROPDOWN --- */
        .profile-menu {{ position: relative; display: inline-block; }}
        .role-badge {{ background: var(--primary-blue); color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; cursor: pointer; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background: white; min-width: 260px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); z-index: 1000; border-radius: 8px; border: 1px solid #ddd; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: var(--primary-hover); color: white; padding: 15px; text-align: center; border-radius: 8px 8px 0 0; }}
        .profile-details {{ padding: 15px; text-align: left; color: var(--text-dark); }}
        .profile-details p {{ margin: 0 0 10px 0; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        .profile-details strong {{ color: var(--primary-blue); width: 85px; display: inline-block; }}

        /* --- FAQ CARDS --- */
        .faq-card {{ background: white; border-radius: 8px; margin: 20px 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid var(--primary-blue); padding: 20px; }}
        .faq-card strong {{ color: var(--primary-blue); display: block; margin-bottom: 10px; font-size: 1.1rem; }}
        .faq-card p {{ margin: 0; color: #666; line-height: 1.5; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/user_dashboard">Document Hub</a></li>
            <li><a href="/my_submissions">My Submissions</a></li>
            <li><a href="/version_history">Version History</a></li>
            <li><a href="/support">Support</a></li>
            <li><a href="/faqs" class="active">FAQs</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2>FAQs</h2>
            <div class="topbar-right">
                <a href="/support" class="top-link">Help</a>
                <span style="font-size: 20px;">🔔</span>
                <div class="profile-menu">
                    <div class="role-badge" onclick="document.getElementById('userDrop').classList.toggle('show')">{active_user}</div>
                    <div id="userDrop" class="profile-dropdown">
                        <div class="profile-header">
                            <h3 style="margin:0;">{user_full}</h3>
                            <p style="margin:5px 0 0 0; font-size:11px; opacity:0.8;">USER PROFILE</p>
                        </div>
                        <div class="profile-details">
                            <p><strong>Full Name:</strong> {user_full}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                            <p><strong>User:</strong> {active_user}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="faq-card">
            <strong>Q: Processing time?</strong>
            <p>A: 24-48 business hours.</p>
        </div>
        <div class="faq-card">
            <strong>Q: Accepted formats?</strong>
            <p>A: PDF, JPG, PNG.</p>
        </div>
    </div>

    <script>
        window.onclick = function(e) {{
            if (!e.target.closest('.profile-menu')) {{
                var d = document.getElementById('userDrop');
                if (d && d.classList.contains('show')) d.classList.remove('show');
            }}
        }}
    </script>
</body>
</html>
""")