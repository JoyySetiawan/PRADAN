from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from models import db, User, Task, ActivityLog
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pradan.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'pradan_secret_key_joy'

db.init_app(app)

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None

def can_edit_task(user, task):
    if user.role == 'owner': return True
    if task.creator.role == 'accounting': return user.role == 'accounting'
    if user.role == 'pm': return task.assigned_to == user.id
    return True

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        if User.query.filter_by(email=email).first():
            flash("Email sudah terdaftar!", "danger")
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password=hashed_pw, role=role, is_approved=False)
        db.session.add(new_user)
        db.session.commit()
        flash("Registrasi Berhasil! Tunggu persetujuan Owner.", "info")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Email atau Password salah!", "danger")
            return redirect(url_for('login'))
        if not user.is_approved:
            flash("Akun belum disetujui Owner.", "warning")
            return redirect(url_for('login'))
        session['user_id'] = user.id
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    total_pekerjaan = Task.query.count()
    sedang_dikerjakan = Task.query.filter_by(status='doing').count()
    total_karyawan = User.query.filter_by(is_approved=True).count()
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', user=user, total_pekerjaan=total_pekerjaan, sedang_dikerjakan=sedang_dikerjakan, total_karyawan=total_karyawan, logs=logs, User=User)

@app.route('/semuapekerjaan')
def semuapekerjaan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    todo = Task.query.filter_by(status='todo').all()
    doing = Task.query.filter_by(status='doing').all()
    done = Task.query.filter_by(status='done').all()
    users = User.query.filter_by(is_approved=True).all()
    return render_template('SemuaPekerjaan.html', user=user, todo=todo, doing=doing, done=done, users=users)

@app.route('/karyawan')
def karyawan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    semua_user = User.query.all()
    return render_template('karyawan.html', user=user, semua_user=semua_user)

@app.route('/approve-user/<int:user_id>')
def approve_user(user_id):
    curr = get_current_user()
    if not curr or curr.role != 'owner': return "Akses Ditolak", 403
    target = db.session.get(User, user_id)
    if target:
        target.is_approved = True
        db.session.commit()
        flash(f"Akun {target.name} disetujui!", "success")
    return redirect(url_for('karyawan'))

@app.route('/pengaturan')
def pengaturan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return render_template('pengaturan.html', user=user)

@app.route('/tambah-pekerjaan', methods=['POST'])
def tambah_pekerjaan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    new_task = Task(title=request.form.get('title'), created_by=user.id, assigned_to=int(request.form.get('assigned_to')), status='todo')
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('semuapekerjaan'))

@app.route('/api/tasks/<int:task_id>/edit', methods=['POST'])
def edit_task(task_id):
    user = get_current_user()
    task = db.session.get(Task, task_id)
    if not task or not can_edit_task(user, task): return jsonify({'error': 'Ditolak'}), 403
    task.status = request.json.get('status', task.status)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)