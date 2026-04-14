from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from models import db, User, Task, ActivityLog
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pradan.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'pradan_joy_secret'

db.init_app(app)

# --- HELPER FUNCTIONS ---
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None

# --- AUTHENTICATION ---
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- MAIN ROUTES (NAVIGASI) ---
@app.route('/')
def home():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    
    total_pekerjaan = Task.query.count()
    sedang_dikerjakan = Task.query.filter_by(status='doing').count()
    total_karyawan = User.query.filter_by(is_approved=True).count()
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           user=user, 
                           total_pekerjaan=total_pekerjaan, 
                           sedang_dikerjakan=sedang_dikerjakan, 
                           total_karyawan=total_karyawan, 
                           logs=logs)

@app.route('/semuapekerjaan')
def semuapekerjaan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    todo = Task.query.filter_by(status='todo').all()
    doing = Task.query.filter_by(status='doing').all()
    done = Task.query.filter_by(status='done').all()
    users = User.query.filter_by(is_approved=True).all()
    return render_template('SemuaPekerjaan.html', user=user, todo=todo, doing=doing, done=done, users=users)

@app.route('/pekerjaan-aktif')
def pekerjaan_aktif():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    tasks = Task.query.filter_by(status='doing').all()
    return render_template('pekerjaan_aktif.html', user=user, tasks=tasks)

@app.route('/karyawan')
def karyawan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    semua_user = User.query.all()
    return render_template('karyawan.html', user=user, semua_user=semua_user)

@app.route('/klien')
def klien():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return render_template('klien.html', user=user)

@app.route('/pengaturan')
def pengaturan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return render_template('pengaturan.html', user=user)

# --- ACTIONS ---
@app.route('/approve-user/<int:user_id>')
def approve_user(user_id):
    curr = get_current_user()
    if not curr or curr.role != 'owner': 
        flash("Hanya Owner yang bisa menyetujui user!", "danger")
        return redirect(url_for('home'))
    
    target = db.session.get(User, user_id)
    if target:
        target.is_approved = True
        db.session.commit()
        flash(f"Akun {target.name} berhasil disetujui!", "success")
    return redirect(url_for('karyawan'))

@app.route('/tambah-pekerjaan', methods=['POST'])
def tambah_pekerjaan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    
    title = request.form.get('title')
    assigned_to = request.form.get('assigned_to')
    
    if title and assigned_to:
        new_task = Task(title=title, created_by=user.id, assigned_to=int(assigned_to), status='todo')
        db.session.add(new_task)
        db.session.commit()
        flash("Pekerjaan baru berhasil ditambahkan!", "success")
    
    return redirect(url_for('semuapekerjaan'))

if __name__ == '__main__':
    app.run(debug=True)