from flask import Blueprint, render_template_string, session, redirect, url_for, request
from utils.db import get_db_connection

verifier_bp = Blueprint('verifier', __name__)

@verifier_bp.route("/verifier_dashboard")
def verifier_dashboard():
    if 'user' not in session or session['user']['role'] != 'Verifier':
        return redirect(url_for('auth.login'))
    
    active_user = session['user']['username']
    
    # Initialize profile variables
    user_full = "Unknown"
    user_email = "Unknown"
    user_role = "Verifier"
    user_dob = "Unknown"
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Fetch profile data
        cursor.execute("SELECT fullname, email, role, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile

        # Fetch pending documents
        cursor.execute("""
            SELECT d.id, u.username, u.fullname, u.dob, d.doc_type, d.file_name 
            FROM documentupload d 
            JOIN users u ON d.username = u.username 
            WHERE d.status = 'Pending'
        """)
        pending_docs = cursor.fetchall()
        
        # Fetch notification count
        cursor.execute("SELECT COUNT(*) FROM documentupload WHERE status = 'Pending'")
        notif_count = cursor.fetchone()[0]
        
        cursor.close()
    except Exception:
        pending_docs = []
        notif_count = 0
    
    # Build table rows
    rows = ""
    if pending_docs:
        from flask import url_for
        for doc in pending_docs:
            doc_id, uname, fullname, dob, dtype, fname = doc
            file_link = url_for('uploaded_file', filename=fname)
            rows += f"<tr><td>SYS-{doc_id}</td><td><b>{fullname}</b><br>{dob}</td><td>{dtype}</td><td><a href='{file_link}' target='_blank'>View</a></td><td><button type='button' onclick=\"openActionModal({doc_id})\" style='background:#516d8a;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;'>Review</button></td></tr>"
    else:
        rows = "<tr><td colspan='5' style='text-align: center; padding: 40px;'>No pending reviews.</td></tr>"
    
    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Verifier Dashboard - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; }}
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 4px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background-color: #3e546a; border-left: 4px solid white; padding-left: 16px; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .top-link {{ color: #64748b; text-decoration: none; font-weight: bold; font-size: 14px; transition: 0.3s; }}
        .top-link:hover {{ color: #516d8a; }}
        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; transition: 0.3s; }}
        .bell-wrapper:hover {{ transform: scale(1.1); }}
        .notif-badge {{ position: absolute; top: -5px; right: -8px; background-color: #e74c3c; color: white; font-size: 11px; font-weight: bold; padding: 2px 6px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
        .profile-menu {{ position: relative; display: inline-block; cursor: pointer; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background-color: white; min-width: 250px; box-shadow: 0px 8px 16px rgba(0,0,0,0.15); z-index: 100; border-radius: 8px; border: 1px solid #ddd; overflow: hidden; }}
        .profile-dropdown.show {{ display: block; }}
        .dashboard-body {{ padding: 40px; background: #f8f9fa; flex: 1; }}
        .card {{ background: white; padding: 30px; border-radius: 8px; border: 1px solid #e0e0e0; border-top: 4px solid #516d8a; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/verifier_dashboard" class="active">Pending Documents</a></li>
            <li><a href="/review_history">Review History</a></li>
            <li><a href="/compliance_repo">Compliance Repository</a></li>
            <li><a href="/verification_stats">Verification Stats</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2>Authorized Personnel Workspace</h2>
            <div class="topbar-right">
                <a href="/support_verifier" class="top-link">Support</a>
                <div class="bell-wrapper">
                    🔔
                    {'<span class="notif-badge">' + str(notif_count) + '</span>' if notif_count > 0 else ''}
                </div>
                <div class="profile-menu" onclick="document.getElementById('verifyDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="verifyDrop" class="profile-dropdown">
                        <div style="background: #3e546a; color: white; padding: 15px; text-align: center;">
                            <h3 style="margin:0;">{user_full}</h3>
                            <p style="margin:5px 0 0 0; font-size:12px;">{user_role}</p>
                        </div>
                        <div style="padding: 15px; color: #333;">
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
                <h3 style="margin-top:0;">Pending Document Approvals</h3>
                <table>
                    <tr><th>Doc ID</th><th>User Data</th><th>Type</th><th>File</th><th>Action</th></tr>
                    {rows}
                </table>
            </div>
        </div>
    </div>
    <div id="actionModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1000; justify-content:center; align-items:center;">
        <div style="background:white; padding:30px; border-radius:8px; box-shadow:0 4px 6px rgba(0,0,0,0.1); width:90%; max-width:500px;">
            <h3 style="margin-top:0;">Review Document</h3>
            <form method='post' action='/verify_action'>
                <input type='hidden' id='modalDocId' name='id' value=''>
                <div style="margin-bottom:15px;">
                    <label style="display:block; margin-bottom:5px; font-weight:bold;">Comments (optional):</label>
                    <textarea id='modalComment' name='comment' style='width:100%; min-height:100px; padding:8px; border:1px solid #ddd; border-radius:4px; font-family:Arial; font-size:14px;' placeholder='Enter your comments here...'></textarea>
                </div>
                <div style="display:flex; gap:10px; justify-content:flex-end;">
                    <button type='button' onclick="closeActionModal()" style='background:#999;color:#fff;border:none;padding:10px 20px;border-radius:4px;cursor:pointer;'>Cancel</button>
                    <button type='submit' name='action' value='Rejected' style='background:#e74c3c;color:#fff;border:none;padding:10px 20px;border-radius:4px;cursor:pointer;'>Reject</button>
                    <button type='submit' name='action' value='Approved' style='background:#2ecc71;color:#fff;border:none;padding:10px 20px;border-radius:4px;cursor:pointer;'>Approve</button>
                </div>
            </form>
        </div>
    </div>
    <script>
        function openActionModal(docId) {{
            document.getElementById('modalDocId').value = docId;
            document.getElementById('modalComment').value = '';
            document.getElementById('actionModal').style.display = 'flex';
        }}
        function closeActionModal() {{
            document.getElementById('actionModal').style.display = 'none';
        }}
        window.onclick = function(event) {{
            let modal = document.getElementById('actionModal');
            if (event.target === modal) {{
                closeActionModal();
            }}
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

@verifier_bp.route("/review_history")
def review_history():
    if 'user' not in session or session['user']['role'] != 'Verifier':
        return redirect(url_for('auth.login'))
    
    active_user = session['user']['username']
    
    # Initialize profile variables
    user_full = "Unknown"
    user_email = "Unknown"
    user_role = "Verifier"
    user_dob = "Unknown"
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Fetch profile data
        cursor.execute("SELECT fullname, email, role, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile
        
        # Fetch notification count
        cursor.execute("SELECT COUNT(*) FROM documentupload WHERE status = 'Pending'")
        notif_count = cursor.fetchone()[0]
        
        # Fetch processed documents
        query = """
            SELECT d.id, u.fullname, d.doc_type, d.status, d.comments 
            FROM documentupload d
            JOIN users u ON d.username = u.username
            WHERE d.status IN ('Approved', 'Rejected')
            ORDER BY d.id DESC
        """
        cursor.execute(query)
        reviewed_docs = cursor.fetchall()
        cursor.close()
    except Exception:
        reviewed_docs = []
        notif_count = 0
    
    # Build table rows
    rows = ""
    if reviewed_docs:
        for doc in reviewed_docs:
            doc_id, fullname, dtype, status, comment = doc
            rows += f"<tr><td>SYS-{doc_id}</td><td>{fullname}</td><td>{dtype}</td><td class='status-{status}'>{status}</td><td>{comment if comment else '-'}</td></tr>"
    else:
        rows = "<tr><td colspan='5' style='text-align:center; padding: 40px;'>No history available.</td></tr>"
    
    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Review History - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; }}
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 4px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background-color: #3e546a; border-left: 4px solid white; padding-left: 16px; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .top-link {{ color: #64748b; text-decoration: none; font-weight: bold; font-size: 14px; transition: 0.3s; }}
        .top-link:hover {{ color: #516d8a; }}
        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; transition: 0.3s; }}
        .bell-wrapper:hover {{ transform: scale(1.1); }}
        .notif-badge {{ position: absolute; top: -5px; right: -8px; background-color: #e74c3c; color: white; font-size: 11px; font-weight: bold; padding: 2px 6px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
        .profile-menu {{ position: relative; display: inline-block; cursor: pointer; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background-color: white; min-width: 250px; box-shadow: 0px 8px 16px rgba(0,0,0,0.15); z-index: 100; border-radius: 8px; border: 1px solid #ddd; overflow: hidden; }}
        .profile-dropdown.show {{ display: block; }}
        .dashboard-body {{ padding: 40px; background: #f8f9fa; flex: 1; }}
        .card {{ background: white; padding: 30px; border-radius: 8px; border: 1px solid #e0e0e0; border-top: 4px solid #516d8a; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .status-Approved {{ color: #27ae60; font-weight: bold; }}
        .status-Rejected {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/verifier_dashboard">Pending Documents</a></li>
            <li><a href="/review_history" class="active">Review History</a></li>
            <li><a href="/compliance_repo">Compliance Repository</a></li>
            <li><a href="/verification_stats">Verification Stats</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2>Authorized Personnel Workspace</h2>
            <div class="topbar-right">
                <a href="/support_verifier" class="top-link">Support</a>
                <div class="bell-wrapper">
                    🔔
                    {'<span class="notif-badge">' + str(notif_count) + '</span>' if notif_count > 0 else ''}
                </div>
                <div class="profile-menu" onclick="document.getElementById('verifyDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="verifyDrop" class="profile-dropdown">
                        <div style="background: #3e546a; color: white; padding: 15px; text-align: center;">
                            <h3 style="margin:0;">{user_full}</h3>
                            <p style="margin:5px 0 0 0; font-size:12px;">{user_role}</p>
                        </div>
                        <div style="padding: 15px; color: #333;">
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
                <h3 style="margin-top:0;">Past Review Actions</h3>
                <table>
                    <tr><th>Doc ID</th><th>User</th><th>Type</th><th>Status</th><th>Feedback</th></tr>
                    {rows}
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

@verifier_bp.route("/compliance_repo")
def compliance_repo():
    if 'user' not in session or session['user']['role'] != 'Verifier':
        return redirect(url_for('auth.login'))
    
    active_user = session['user']['username']
    
    # Initialize profile variables
    user_full = "Unknown"
    user_email = "Unknown"
    user_role = "Verifier"
    user_dob = "Unknown"
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Fetch profile data
        cursor.execute("SELECT fullname, email, role, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile
            
        # Fetch notification count
        cursor.execute("SELECT COUNT(*) FROM documentupload WHERE status = 'Pending'")
        notif_count = cursor.fetchone()[0]
        cursor.close()
    except Exception:
        notif_count = 0
    
    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Compliance Repository - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; }}
        
        /* Sidebar Styles */
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 4px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background-color: #3e546a; border-left: 4px solid white; padding-left: 16px; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; transition: 0.3s; }}

        /* Topbar & Icons */
        .main-content {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .top-link {{ color: #64748b; text-decoration: none; font-weight: bold; font-size: 14px; transition: 0.3s; }}
        .top-link:hover {{ color: #516d8a; }}
        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; transition: 0.3s; }}
        .bell-wrapper:hover {{ transform: scale(1.1); }}
        .notif-badge {{ position: absolute; top: -5px; right: -8px; background-color: #e74c3c; color: white; font-size: 11px; font-weight: bold; padding: 2px 6px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
        
        /* Profile Dropdown */
        .profile-menu {{ position: relative; display: inline-block; cursor: pointer; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background-color: white; min-width: 250px; box-shadow: 0px 8px 16px rgba(0,0,0,0.15); z-index: 100; border-radius: 8px; overflow: hidden; border: 1px solid #ddd; }}
        .profile-dropdown.show {{ display: block; }}
        .profile-header {{ background: #3e546a; color: white; padding: 15px; text-align: center; }}
        .profile-header h3 {{ margin: 0; font-size: 16px; }}
        .profile-header p {{ margin: 5px 0 0 0; font-size: 12px; text-transform: uppercase; }}
        .profile-details {{ padding: 15px; color: #333; }}
        .profile-details p {{ margin: 0 0 10px 0; font-size: 14px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        .profile-details strong {{ color: #516d8a; display: inline-block; width: 80px; }}

        /* Content Card */
        .dashboard-body {{ padding: 40px; background: #f8f9fa; flex: 1; }}
        .card {{ background: white; padding: 30px; border-radius: 8px; border: 1px solid #e0e0e0; border-top: 4px solid #516d8a; margin-bottom: 20px; }}
        .card h3 {{ color: #3e546a; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/verifier_dashboard">Pending Documents</a></li>
            <li><a href="/review_history">Review History</a></li>
            <li><a href="/compliance_repo" class="active">Compliance Repository</a></li>
            <li><a href="/verification_stats">Verification Stats</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2 style="margin: 0; color: #333;">Verification Guidelines</h2>
            <div class="topbar-right">
                <a href="/support_verifier" class="top-link">Support</a>
                <div class="bell-wrapper" title="Pending Reviews">
                    🔔
                    {'<span class="notif-badge">' + str(notif_count) + '</span>' if notif_count > 0 else ''}
                </div>
                
                <div class="profile-menu" onclick="document.getElementById('verifyDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="verifyDrop" class="profile-dropdown">
                        <div class="profile-header">
                            <h3>{user_full}</h3>
                            <p>{user_role}</p>
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
                <h3>Identification Guidelines</h3>
                <p>1. Must be a government-issued ID (Passport, Driver's License).<br>
                2. The name on the ID must match the System Data name.<br>
                3. The image must be clear and legible.</p>
            </div>
            
            <div class="card">
                <h3>Compliance Forms</h3>
                <p>1. Must be the most recent version of the compliance document.<br>
                2. User signatures must be present and dated.<br>
                3. Any incomplete fields result in immediate rejection with a comment.</p>
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

@verifier_bp.route("/verification_stats")
def verification_stats():
    if 'user' not in session or session['user']['role'] != 'Verifier':
        return redirect(url_for('auth.login'))
    
    active_user = session['user']['username']
    
    # Initialize profile variables
    user_full = "Unknown"
    user_email = "Unknown"
    user_role = "Verifier"
    user_dob = "Unknown"
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Fetch profile data
        cursor.execute("SELECT fullname, email, role, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile

        # Fetch system metrics
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'Approved' THEN 1 END) as approved,
                COUNT(CASE WHEN status = 'Rejected' THEN 1 END) as rejected
            FROM documentupload
        """)
        stats = cursor.fetchone()
        cursor.close()
        
        pending_count = stats[0] if stats[0] else 0
        approved_count = stats[1] if stats[1] else 0
        rejected_count = stats[2] if stats[2] else 0
    except Exception:
        pending_count = approved_count = rejected_count = 0
    
    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Verification Stats - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; }}
        
        /* Sidebar Styles */
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 4px solid transparent; transition: 0.3s; }}
        .nav-links li a:hover, .nav-links li a.active {{ background: #3e546a; border-left: 4px solid white; padding-left: 16px; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; transition: 0.3s; }}

        /* Topbar & Profile Styles */
        .main-content {{ flex: 1; display: flex; flex-direction: column; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .top-link {{ color: #64748b; text-decoration: none; font-weight: bold; font-size: 14px; transition: 0.3s; }}
        .bell-wrapper {{ position: relative; cursor: pointer; font-size: 20px; }}
        .notif-badge {{ position: absolute; top: -5px; right: -8px; background-color: #e74c3c; color: white; font-size: 11px; font-weight: bold; padding: 2px 6px; border-radius: 50%; border: 2px solid white; }}
        
        .profile-menu {{ position: relative; display: inline-block; cursor: pointer; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background-color: white; min-width: 250px; box-shadow: 0px 8px 16px rgba(0,0,0,0.15); border-radius: 8px; border: 1px solid #ddd; overflow: hidden; z-index: 100; }}
        .profile-dropdown.show {{ display: block; }}

        /* Stats Content */
        .dashboard-body {{ padding: 40px; background: #f8f9fa; flex: 1; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
        .stat-card {{ background: white; padding: 30px; border-radius: 8px; text-align: center; border: 1px solid #e0e0e0; border-top: 4px solid #516d8a; }}
        .stat-card .number {{ font-size: 48px; font-weight: bold; color: #3e546a; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/verifier_dashboard">Pending Documents</a></li>
            <li><a href="/review_history">Review History</a></li>
            <li><a href="/compliance_repo">Compliance Repository</a></li>
            <li><a href="/verification_stats" class="active">Verification Stats</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2 style="margin: 0; color: #333;">System Metrics</h2>
            <div class="topbar-right">
                <a href="/support_verifier" class="top-link">Support</a>
                <div class="bell-wrapper">
                    🔔 {'<span class="notif-badge">' + str(pending_count) + '</span>' if pending_count > 0 else ''}
                </div>
                
                <div class="profile-menu" onclick="document.getElementById('verifyDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="verifyDrop" class="profile-dropdown">
                        <div style="background: #3e546a; color: white; padding: 15px; text-align: center;">
                            <h3 style="margin:0;">{user_full}</h3>
                            <p style="margin:5px 0 0 0; font-size:12px;">{user_role}</p>
                        </div>
                        <div style="padding: 15px; color: #333;">
                            <p><strong>Username:</strong> {active_user}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="dashboard-body">
            <div class="stats-grid">
                <div class="stat-card" style="border-top-color: #f39c12;">
                    <h3>Pending Reviews</h3>
                    <div class="number">{pending_count}</div>
                </div>
                <div class="stat-card" style="border-top-color: #27ae60;">
                    <h3>Approved</h3>
                    <div class="number">{approved_count}</div>
                </div>
                <div class="stat-card" style="border-top-color: #e74c3c;">
                    <h3>Rejected</h3>
                    <div class="number">{rejected_count}</div>
                </div>
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

@verifier_bp.route("/support_verifier")
def support_verifier():
    if 'user' not in session or session['user']['role'] != 'Verifier':
        return redirect(url_for('auth.login'))
    
    active_user = session['user']['username']
    
    # Initialize profile variables
    user_full = "Unknown"
    user_email = "Unknown"
    user_role = "Verifier"
    user_dob = "Unknown"
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Fetch profile data
        cursor.execute("SELECT fullname, email, role, dob FROM users WHERE username = %s", (active_user,))
        profile = cursor.fetchone()
        if profile:
            user_full, user_email, user_role, user_dob = profile
        
        # Fetch notification count
        cursor.execute("SELECT COUNT(*) FROM documentupload WHERE status = 'Pending'")
        notif_count = cursor.fetchone()[0]
        cursor.close()
    except Exception:
        notif_count = 0
    
    return render_template_string(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Verifier Support - SecureDoc</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f7f6; }}
        .sidebar {{ width: 250px; background: #516d8a; color: white; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 20px; background: #3e546a; text-align: center; font-weight: bold; font-size: 20px; margin: 0; }}
        .nav-links {{ list-style: none; padding: 0; margin: 0; flex: 1; }}
        .nav-links li a {{ display: block; padding: 15px 20px; color: #ecf0f1; text-decoration: none; border-left: 4px solid transparent; }}
        .nav-links li a:hover {{ background-color: #3e546a; border-left: 4px solid white; }}
        .logout {{ padding: 15px 20px; background: #3e546a; color: white; text-align: center; text-decoration: none; font-weight: bold; margin-top: auto; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; }}
        .topbar {{ background: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .topbar-right {{ display: flex; align-items: center; gap: 25px; }}
        .top-link {{ color: #516d8a; text-decoration: none; font-weight: bold; font-size: 14px; }}
        .bell-wrapper {{ position: relative; font-size: 20px; cursor: pointer; }}
        .notif-badge {{ position: absolute; top: -5px; right: -8px; background-color: #e74c3c; color: white; font-size: 11px; font-weight: bold; padding: 2px 6px; border-radius: 50%; border: 2px solid white; }}
        .profile-menu {{ position: relative; cursor: pointer; }}
        .role-badge {{ background: #516d8a; color: white; padding: 8px 18px; border-radius: 20px; font-size: 14px; font-weight: bold; }}
        .profile-dropdown {{ display: none; position: absolute; right: 0; top: 45px; background-color: white; min-width: 250px; box-shadow: 0px 8px 16px rgba(0,0,0,0.15); border-radius: 8px; border: 1px solid #ddd; overflow: hidden; z-index: 100; }}
        .profile-dropdown.show {{ display: block; }}
        .dashboard-body {{ padding: 40px; background: #f8f9fa; flex: 1; }}
        .contact-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; max-width: 800px; }}
        .contact-card {{ background: white; padding: 40px 30px; border-radius: 8px; border: 1px solid #e0e0e0; border-top: 4px solid #516d8a; text-align: center; }}
        .contact-card h3 {{ color: #3e546a; margin-top: 0; }}
        .contact-card p.title {{ color: #7f8c8d; font-size: 14px; text-transform: uppercase; }}
        .contact-card a {{ color: #516d8a; text-decoration: none; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 class="sidebar-header">SecureDoc Portal</h2>
        <ul class="nav-links">
            <li><a href="/verifier_dashboard">Pending Documents</a></li>
            <li><a href="/review_history">Review History</a></li>
            <li><a href="/compliance_repo">Compliance Repository</a></li>
            <li><a href="/verification_stats">Verification Stats</a></li>
        </ul>
        <a href="/logout" class="logout">Secure Logout</a>
    </div>

    <div class="main-content">
        <div class="topbar">
            <h2>Technical Support</h2>
            <div class="topbar-right">
                <a href="/support_verifier" class="top-link">Support</a>
                <div class="bell-wrapper">
                    🔔 {'<span class="notif-badge">' + str(notif_count) + '</span>' if notif_count > 0 else ''}
                </div>
                <div class="profile-menu" onclick="document.getElementById('verifyDrop').classList.toggle('show')">
                    <div class="role-badge">{active_user}</div>
                    <div id="verifyDrop" class="profile-dropdown">
                        <div style="background: #3e546a; color: white; padding: 15px; text-align: center;">
                            <h3 style="margin:0;">{user_full}</h3>
                        </div>
                        <div style="padding: 15px; color: #333;">
                            <p><strong>Username:</strong> {active_user}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>DOB:</strong> {user_dob}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="dashboard-body">
            <div class="contact-grid">
                <div class="contact-card">
                    <h3>Yamuna Paarvendhan</h3>
                    <p class="title">Engineer</p>
                    <a href="mailto:yamunadc20@gmail.com">✉️ yamunadc20@gmail.com</a>
                </div>
                <div class="contact-card">
                    <h3>Lakshmi Bhavani Pasurla</h3>
                    <p class="title">Administrator</p>
                    <a href="mailto:pasurlabhavani111@gmail.com">✉️ pasurlabhavani111@gmail.com</a>
                </div>
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