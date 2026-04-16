from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from models import db, User, Task, ActivityLog
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pradan.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'pradan_joy_secret'

db.init_app(app)

# --- FUNGSI PEMBANTU ---
def get_current_user():
    user_id = session.get('user_id')
    if user_id: return db.session.get(User, user_id)
    return None

@app.context_processor
def inject_user():
    # Agar variabel 'user' bisa dipakai di semua file HTML tanpa error
    return dict(user=get_current_user(), User=User)

# --- AUTHENTICATION (LOGIN & REGIS) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash("Email tidak terdaftar!", "danger")
            return redirect(url_for('login'))
        if not check_password_hash(user.password, password):
            flash("Email atau Password salah!", "danger")
            return redirect(url_for('login'))
        if not user.is_approved:
            flash("Akun belum disetujui Owner. Hubungi Pak Joy.", "warning")
            return redirect(url_for('login'))
            
        session['user_id'] = user.id
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash("Email sudah terdaftar!", "danger")
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        new_user = User(name=request.form.get('name'), email=email, password=hashed_pw, 
                        role=request.form.get('role'), is_approved=False)
        db.session.add(new_user)
        db.session.commit()
        flash("Registrasi Berhasil! Tunggu persetujuan Owner.", "info")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- HALAMAN UTAMA ---
@app.route('/')
def home():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return render_template('dashboard.html', 
                           total_pekerjaan=Task.query.count(),
                           sedang_dikerjakan=Task.query.filter_by(status='doing').count(),
                           total_karyawan=User.query.filter_by(is_approved=True).count(),
                           logs=ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(5).all())

@app.route('/semuapekerjaan')
def semuapekerjaan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    # Poin 1: Jika Accounting, paksa masuk ke spreadsheet
    if user.role == 'accounting': return redirect(url_for('accounting_sheet'))
    
    return render_template('SemuaPekerjaan.html', 
                           todo=Task.query.filter_by(status='todo').all(),
                           doing=Task.query.filter_by(status='waiting').all(),
                           done=Task.query.filter_by(status='done').all(),
                           users=User.query.filter_by(is_approved=True).all())

@app.route('/accounting-sheet')
def accounting_sheet():
    user = get_current_user()
    # Proteksi: Hanya Accounting & Owner yang bisa akses
    if not user or user.role not in ['accounting', 'owner']:
        flash("Akses ditolak!", "danger")
        return redirect(url_for('home'))
    return render_template('accounting_sheet.html', tasks=Task.query.all())

@app.route('/vendor')
def vendor():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return render_template('vendor.html')

# --- MANAJEMEN KARYAWAN (OWNER ONLY) ---
@app.route('/karyawan')
def karyawan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return render_template('karyawan.html', semua_user=User.query.all())

@app.route('/approve-user/<int:user_id>')
def approve_user(user_id):
    curr = get_current_user()
    if curr and curr.role == 'owner':
        target = db.session.get(User, user_id)
        if target:
            target.is_approved = True
            db.session.commit()
            flash(f"Akun {target.name} disetujui!", "success")
    return redirect(url_for('karyawan'))

@app.route('/delete-user/<int:user_id>')
def delete_user(user_id):
    curr = get_current_user()
    if curr and curr.role == 'owner':
        target = db.session.get(User, user_id)
        if target and target.role != 'owner':
            db.session.delete(target)
            db.session.commit()
            flash("User berhasil dihapus!", "success")
    return redirect(url_for('karyawan'))

# --- ACTIONS (TAMBAH DATA) ---
@app.route('/tambah-pekerjaan', methods=['POST'])
def tambah_pekerjaan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    
    # Poin 2: Logika H-6 Bulan otomatis
    date_str = request.form.get('event_date')
    if date_str:
        event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        days_to_event = (event_date - datetime.now().date()).days
        # Masuk waiting list jika > 180 hari (6 bulan)
        status = 'todo' if days_to_event <= 180 else 'waiting'
    else:
        event_date = None
        status = 'todo'

    new_task = Task(client_name=request.form.get('title'), 
                    event_date=event_date, 
                    venue=request.form.get('venue'), 
                    status=status)
    db.session.add(new_task)
    db.session.commit()
    
    # Log aktivitas
    log = ActivityLog(user_id=user.id, action=f"Tambah Client: {request.form.get('title')}")
    db.session.add(log)
    db.session.commit()
    
    flash("Pekerjaan berhasil ditambahkan!", "success")
    return redirect(url_for('semuapekerjaan'))

# --- HALAMAN LAIN (AGAR TIDAK BUILDERROR) ---
@app.route('/pekerjaan-aktif')
def pekerjaan_aktif():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return render_template('pekerjaan_aktif.html')

@app.route('/klien')
def klien():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return render_template('klien.html')

@app.route('/pengaturan')
def pengaturan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    return render_template('pengaturan.html')

if __name__ == '__main__':
    app.run(debug=True)