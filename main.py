from flask import Flask, jsonify, send_from_directory, request, render_template, redirect, session, url_for, flash, send_file, abort, make_response
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import auth
import os, json, shutil, zipfile, io
from functools import wraps
from datetime import timedelta
from dotenv import load_dotenv


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect ("/login")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get("role") not in [1, 2]:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
csrf = CSRFProtect(app)
UPLOAD_FOLDER = 'shared_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')

if not os.path.exists('shared_files'):
    os.makedirs('shared_files')
if not os.path.exists('shared_files/public'):
    os.mkdir('shared_files/public')

def get_readable_size(size_in_bytes):
    for unit in ['Byte', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"

def get_user_storage_used(username):
    user_folder = os.path.join('shared_files', username)
    total = 0

    for root, dirs, files in os.walk(user_folder):
        for file in files:
            total += os.path.getsize(os.path.join(root, file))
    return total

def get_directory_contents(base_folder, subpath=""):

    target_folder = os.path.abspath(os.path.join(base_folder, subpath))
    absolute_base = os.path.abspath(base_folder)

    if not target_folder.startswith(absolute_base):
        return None, None

    if not os.path.exists(target_folder):
        return None, None

    folders = []
    files_data = []

    for item in os.listdir(target_folder):
        item_path = os.path.join(target_folder, item)
        if os.path.isdir(item_path):
            folders.append(item)
        elif os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            files_data.append({
                'name': item,
                'size': get_readable_size(size)
            })
            
    return folders, files_data

def is_safe_path(base_folder, subpath):

    target_folder = os.path.abspath(os.path.join(base_folder, subpath))
    absolute_base = os.path.abspath(base_folder)

    try:
        return os.path.commonpath([absolute_base, target_folder]) == absolute_base
    except ValueError:
        return False

def download_dir(target_user, name):
    if target_user == "":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files', session['username'])
        user_folder = os.path.join(base_user_folder, subpath, name)

    elif target_user == "public":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files', 'public')
        user_folder = os.path.join('shared_files/public', subpath, name)

    else:
        base_user_folder = os.path.join('shared_files', target_user)  
        user_folder = os.path.join('shared_files', target_user, name)

    if not is_safe_path(base_user_folder, name):
        abort(403)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(user_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, user_folder)
                zf.write(file_path, arcname)
    
    buffer.seek(0)
    return send_file(buffer, mimetype='application/zip', as_attachment=True, download_name=f"{name.split('/')[-1]}.zip")

def download_file(target_user, name):
    if target_user == "":
        subpath = request.form.get('subpath', '')
        user_folder = os.path.join('shared_files', session['username'], subpath)
        is_download = request.args.get("download") == "1"
        response = make_response(send_from_directory(user_folder, name, as_attachment=is_download))

    elif target_user == "public":
        subpath = request.form.get('subpath', '')
        public_folder = os.path.join('shared_files/public', subpath)
        is_download = request.args.get("download") == "1"
        response = make_response(send_from_directory(public_folder, name, as_attachment=is_download))

    else:
        user_folder = os.path.join('shared_files', target_user)
        is_download = request.args.get("download") == "1"
        response = make_response(send_from_directory(user_folder, name, as_attachment=is_download))

    if not is_download:
            response.headers['Content-Security-Policy'] = "default-src 'none'; sandbox"
    
            response.headers['X-Content-Type-Options'] = "nosniff"
    
    return response

def delete_file(title, name, target_user):
    if title == "public":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files/public')
        user_folder = os.path.join('shared_files/public', subpath)
        redirect_address = f"/public/browse/{subpath}" if subpath else "/public"

    elif title == "admin":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files', target_user)
        user_folder = os.path.join(base_user_folder, subpath)
        redirect_address =  f"/admin/view_user/{target_user}/browse/{subpath}" if subpath else f"/admin/view_user/{target_user}"
       
    elif title == "":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files', session['username'])
        user_folder = os.path.join(base_user_folder, subpath)
        redirect_address = f"/browse/{subpath}" if subpath else "/"

    if not is_safe_path(base_user_folder, subpath):
        abort(403)

    safe_name = secure_filename(name)
    file_path = os.path.join(user_folder, safe_name)
    
    if os.path.exists(file_path):
        os.remove(file_path)

    return redirect(redirect_address)

def delete_dir(target_user, name):
    if target_user == "":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files', session['username'])
        user_folder = os.path.join(base_user_folder, subpath)
        redirect_address = f"/browse/{subpath}" if subpath else "/"

    elif target_user == "public":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files/public')
        user_folder = os.path.join('shared_files/public', subpath)
        redirect_address = f"/public/browse/{subpath}" if subpath else "/public"

    elif target_user == "admin":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files', target_user)
        user_folder = os.path.join('shared_files', target_user, subpath)
        redirect_address =  f"/admin/view_user/{target_user}/browse/{subpath}" if subpath else f"/admin/view_user/{target_user}"
    else:
        abort(404)

    if not is_safe_path(base_user_folder, subpath):
        abort(403)

    safe_name = secure_filename(name)
    dir_path = os.path.join(user_folder, safe_name)

    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        shutil.rmtree(dir_path)

    return redirect(redirect_address)

def upload_file(title):

    if title == "public":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files', 'public')
        user_folder = os.path.join(base_user_folder, subpath)
        redirect_address = f"/public/browse/{subpath}" if subpath else "/public"
        limit = float('inf')
        used = 0
    elif title == "":
        subpath = request.form.get('subpath', '')
        base_user_folder = os.path.join('shared_files', session['username'])
        user_folder = os.path.join(base_user_folder, subpath)
        redirect_address = f"/browse/{subpath}" if subpath else "/"
        limit = auth.get_storage_limit(session['username'])
        used = get_user_storage_used(session['username'])
    else:
        abort(404)

    if not is_safe_path(base_user_folder, subpath):
        abort(403)

    file_size = request.content_length or 0

    if 'file' not in request.files:
        return "Dosya Seçilmedi", 400
    
    file = request.files['file']
    if file.filename != "":
        if used + file_size > limit:
            return jsonify({'error': 'storage_full'}), 413
            
        filename = secure_filename(file.filename)
        file.save(os.path.join(user_folder, filename))

    return redirect(redirect_address)

def add_dir(title):
    subpath = request.form.get('subpath', '')
    folder_name = request.form.get('folder_name', '')
    
    if title == "":
        base_user_folder = os.path.join('shared_files', session['username'])
        redirect_address = f"/browse/{subpath}" if subpath else "/"
    elif title == "public":
        base_user_folder = os.path.join('shared_files', 'public')
        redirect_address = f"/public/browse/{subpath}" if subpath else "/public"
    else:
        abort(404)

    if not is_safe_path(base_user_folder, subpath):
        abort(403)
    
    if folder_name:
        user_folder = os.path.join(base_user_folder, subpath)
        safe_name = secure_filename(folder_name)
        new_folder = os.path.join(user_folder, safe_name)
        os.makedirs(new_folder, exist_ok=True)
    
    return redirect(redirect_address)

@app.route("/")
@app.route("/browse/<path:subpath>")
@login_required
def home(subpath=""):

    user_base_folder = os.path.join('shared_files', session['username'])
    os.makedirs(user_base_folder, exist_ok=True)

    folders, files_data = get_directory_contents(user_base_folder, subpath)

    if folders is None:
        return redirect("/")

    storage_used = get_user_storage_used(session['username'])
    storage_limit = auth.get_storage_limit(session['username'])
    parent = '/'.join(subpath.split('/')[:-1])

    return render_template("index.html", files=files_data, folders=folders, subpath=subpath, 
                           parent=parent, storage_used=storage_used,
                           storage_used_str=get_readable_size(storage_used), 
                           storage_limit_str=get_readable_size(storage_limit),
                           storage_limit=storage_limit, 
                           storage_percent=min(int((storage_used / storage_limit) * 100), 100))

@app.route("/public")
@app.route("/public/browse/<path:subpath>")
@login_required
def public_browsing(subpath=""):

    public_base_folder = os.path.join('shared_files', 'public')

    folders, files_data = get_directory_contents(public_base_folder, subpath)

    if folders is None:
        return redirect("/public")

    storage_used = get_user_storage_used(session['username'])
    storage_limit = auth.get_storage_limit(session['username'])
    parent = '/'.join(subpath.split('/')[:-1])


    return render_template("public.html", files=files_data, folders=folders, subpath=subpath, 
                                   parent=parent, storage_used=storage_used,
                                   storage_used_str=get_readable_size(storage_used), 
                                   storage_limit_str=get_readable_size(storage_limit),
                                   storage_limit=storage_limit, 
                                   storage_percent=min(int((storage_used / storage_limit) * 100), 100), title="Ortak Alan")

@app.route("/login", methods=['GET', 'POST'])
def auth_check():
    if request.method == 'POST':
        username = request.form.get('username')
        passw = request.form.get('password')  

        if auth.check_user(username, passw):
            session['username'] = username

            user_role = auth.role_check(username)

            session["role"] = user_role

            session["is_admin"] = user_role in (1, 2)

            if request.form.get('remember'):
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False
            return redirect("/")
        else:
            flash("login_error", "error")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/admin")
@login_required
@admin_required
def admin():
    users = auth.get_all_users()
    users_data = []
    for user in users:
        used = get_user_storage_used(user['username'])
        users_data.append({
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'storage_limit': user['storage_limit'],
                'storage_used': used,
                'storage_percent': min(int((used / user['storage_limit']) * 100), 100),
                'storage_used_str': get_readable_size(used),
                'storage_limit_str': get_readable_size(user['storage_limit'])
            })

    total, used, free = shutil.disk_usage('shared_files')
    disk_info = {
        'total': get_readable_size(total),
        'used': get_readable_size(used),
        'free': get_readable_size(free)
    }

    return render_template("admin.html", users=users_data, disk_info=disk_info)

@app.route("/admin/view_user/<target_user>")
@app.route("/admin/view_user/<target_user>/browse/<path:subpath>")
@admin_required
def admin_view_user(target_user, subpath=""):

    target_base_folder = os.path.join('shared_files', target_user)

    if not os.path.exists(target_base_folder):
        flash("user_not_found", "error")
        return redirect("/admin")

    folders, files_data = get_directory_contents(target_base_folder, subpath)

    if folders is None:
        return redirect("/admin")

    storage_used = get_user_storage_used(target_user)
    storage_limit = auth.get_storage_limit(target_user)
    parent = '/'.join(subpath.split('/')[:-1])


    return render_template("index.html",
                           files=files_data, folders=folders, subpath=subpath, parent=parent,
                           storage_used=storage_used, storage_used_str=get_readable_size(storage_used),
                           storage_limit_str=get_readable_size(storage_limit), storage_limit=storage_limit,
                           storage_percent=min(int((storage_used / storage_limit) * 100), 100),
                           title=f"{target_user}", viewing_user=target_user)

@app.route("/admin/shared_files/<target_user>/<path:name>")
@admin_required
def admin_handle_file(target_user, name):
    return download_file(target_user, name)

@app.route("/admin/delete/<target_user>/<path:name>", methods=['POST'])
@admin_required
def admin_delete_file(target_user, name):
    delete_file("admin", name, target_user)

@app.route("/admin/delete_dir/<target_user>/<path:name>", methods=['POST'])
@admin_required
def admin_delete_dir(target_user, name):
    return delete_dir(target_user, name)

@app.route("/admin/download_dir/<target_user>/<path:name>", methods=['GET'])
@admin_required
def admin_download_dir(target_user, name):
    return download_dir(target_user, name)
        
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")

@app.route("/upload_file", methods=['POST'])
@login_required
def upload_personal_file():
    return upload_file("")

@app.route("/upload_public_file", methods=['POST'])
@admin_required
def upload_public_file():
    return upload_file("public")

@app.route("/toggle_favorite", methods=['POST'])
@login_required
def toggle_favorite():
    item_name = request.form.get('item_name')
    subpath = request.form.get('subpath', '')
    full_item_path = os.path.join(subpath, item_name).replace("\\", "/") if subpath else item_name

    if not is_safe_path(full_item_path, subpath):
            abort(403)
    
    is_added = auth.toggle_favorite(session['username'], full_item_path)
    if is_added:
        flash("add_favorites", "success")
    else:
        flash("remove_favorites", "success")
        
    if subpath:
        return redirect(f"/browse/{subpath}")
    return redirect("/")

@app.route("/favorites")
@login_required
def show_favorites():
    user_folder = os.path.join('shared_files', session['username'])
    favs = auth.get_user_favorites(session['username'])

    storage_used = get_user_storage_used(session['username'])
    storage_limit = auth.get_storage_limit(session['username'])
    
    fav_files = []
    for fav in favs:
        full_path = os.path.join(user_folder, fav)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            size = os.path.getsize(full_path)
            fav_files.append({
                'name': os.path.basename(fav),
                'full_path': fav, 
                'size': get_readable_size(size)
            })
    return render_template("index.html", files=fav_files, title="Yıldızlı Dosyalar", is_special_view=True, storage_used=storage_used,
    storage_used_str=get_readable_size(storage_used), storage_limit_str=get_readable_size(storage_limit), 
    storage_limit=storage_limit, storage_percent=min(int((storage_used / storage_limit) * 100), 100))

@app.route("/recent")
@login_required
def show_recent():
    user_folder = os.path.join('shared_files', session['username'])
    all_files = []

    storage_used = get_user_storage_used(session['username'])
    storage_limit = auth.get_storage_limit(session['username'])
    
    for root, dirs, files in os.walk(user_folder):
        for file in files:
            if file.startswith('.'): continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, user_folder).replace("\\", "/")
            all_files.append({
                'name': file,
                'full_path': rel_path,
                'mtime': os.path.getmtime(full_path),
                'size': get_readable_size(os.path.getsize(full_path))
            })
            
    all_files.sort(key=lambda x: x['mtime'], reverse=True)
    recent_files = all_files[:20]
    return render_template("index.html", files=recent_files, title="Son Eklenenler", is_special_view=True, storage_used=storage_used,storage_used_str=get_readable_size(storage_used),
    storage_limit_str=get_readable_size(storage_limit),
    storage_limit=storage_limit, storage_percent=min(int((storage_used / storage_limit) * 100), 100))

@app.route("/shared_files/<path:name>")
@login_required
def handle_file(name):
    return download_file("", name)

@app.route("/shared_files/public/<path:name>")
@login_required
def handle_public_file(name):
    return download_file("public", name)

@app.route("/download_dir/<path:name>", methods=['GET'])
@login_required
def download_personal_dir(name):
    return download_dir("", name)

@app.route("/download_public_dir/<path:name>", methods=['GET'])
@login_required
def download_public_dir(name):
    return download_dir("public", name)

@app.route("/delete/<path:name>", methods=['POST'])
@login_required
def delete_personal_file(name):
    return delete_file("", name, "")

@app.route("/delete_public_file/<path:name>", methods=['POST'])
@admin_required
def delete_public_file(name):
    return delete_file("public", name, "")

@app.route("/add_dir", methods=['POST'])
@login_required
def add_personal_dir():
    return add_dir("")

@app.route("/add_public_dir", methods=['POST'])
@admin_required
def add_public_dir():
    return add_dir("public")

@app.route("/delete_dir/<path:name>", methods=['POST'])
@login_required
def delete_personal_dir(name):
    return delete_dir("", name)

@app.route("/delete_public_dir/<path:name>", methods=['POST'])
@admin_required
def delete_public_dir(name):
    return delete_dir("public", name)

@app.route("/admin/delete_user/<username>", methods=['POST'])
@admin_required
def admin_delete_user(username):

    if username == session['username']:
        flash("delete_admin_self", "error")
        return redirect("/admin")

    if auth.role_check(username) == 2:
        flash("cannot_delete_host", "error")
        return redirect("/admin")

    if auth.role_check(username) == 1 and auth.role_check(session['username']) == 1:
        flash("cannot_delete_admin", "error")
        return redirect("/admin")
    
    auth.delete_user(username)

    user_folder = os.path.join("shared_files", username)

    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)
    return redirect("/admin")

@app.route("/admin/add_user", methods=["POST"])
@admin_required
def admin_add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = 1 if request.form.get('is_admin') else 0

    auth.add_user(username, password, is_admin)
    return redirect("/admin")

@app.route("/admin/toggle_admin/<username>", methods=['POST'])
@admin_required
def admin_toggle_admin(username):
    if session.get("role") != 2:
        return redirect("/")

    auth.toggle_admin(username)
    return redirect("/admin")

@app.route("/admin/set_limit/<username>", methods = ['POST'])
@admin_required
def admin_set_limit(username):
    limit_gb = float(request.form.get('limit_gb', 5))
    limit_bytes = int(limit_gb * 1024 * 1024 * 1024)

    auth.set_storage_limit(username, limit_bytes)

    return redirect("/admin")

app.run(debug=True, host='0.0.0.0', port=8080)
