from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from models import db, User, Task, ActivityLog, Vendor
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pradan.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'pradan_joy_secret'

# Konfigurasi Upload Folder untuk Logo Vendor
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 

db.init_app(app)

# --- FUNGSI PEMBANTU ---
def get_current_user():
    user_id = session.get('user_id')
    if user_id: return db.session.get(User, user_id)
    return None

@app.context_processor
def inject_user():
    return dict(user=get_current_user(), User=User)

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

# --- HALAMAN UTAMA & KANBAN ---
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
    if user.role == 'accounting': return redirect(url_for('accounting_sheet'))
    return render_template('SemuaPekerjaan.html', 
                           todo=Task.query.filter_by(status='todo').all(),
                           doing=Task.query.filter_by(status='doing').all(),
                           done=Task.query.filter_by(status='done').all(),
                           users=User.query.filter_by(is_approved=True).all())

# --- PEKERJAAN AKTIF (UPDATE PROGRES) ---
@app.route('/pekerjaan-aktif', methods=['GET', 'POST'])
def pekerjaan_aktif():
    user = get_current_user()
    if not user: return redirect(url_for('login'))

    # Tangkap data jika tombol "Simpan Laporan" ditekan
    if request.method == 'POST':
        task_id = request.form.get('task_id')
        task = db.session.get(Task, task_id)
        if task:
            task.progress_notes = request.form.get('progress_notes')
            task.vendor_info = request.form.get('vendor_info')
            db.session.commit()
            
            # Catat log aktivitas
            log = ActivityLog(user_id=user.id, action=f"Update progres klien: {task.client_name}")
            db.session.add(log)
            db.session.commit()
            flash('Detail pekerjaan berhasil diperbarui!', 'success')
        return redirect(url_for('pekerjaan_aktif'))

    # Tampilkan hanya data yang di kolom DOING
    doing_tasks = Task.query.filter_by(status='doing').all()
    return render_template('pekerjaan_aktif.html', tasks=doing_tasks)

# --- ACCOUNTING ---
@app.route('/accounting-sheet')
def accounting_sheet():
    user = get_current_user()
    if not user or user.role not in ['accounting', 'owner']: return redirect(url_for('home'))
    return render_template('accounting_sheet.html', tasks=Task.query.all())

# --- LIBRARY VENDOR ---
@app.route('/vendor')
def vendor():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    category = request.args.get('category', 'Dekor')
    vendors = Vendor.query.filter_by(category=category).all()
    return render_template('vendor.html', current_category=category, vendors=vendors)

@app.route('/add-vendor', methods=['POST'])
def add_vendor():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    category = request.form.get('category')
    tier = request.form.get('tier')
    
    logo_file = request.files.get('logo')
    logo_filename = None
    if logo_file and logo_file.filename != '':
        filename = secure_filename(f"vendor_{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo_file.filename}")
        logo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        logo_filename = filename
        
    new_vendor = Vendor(name=name, description=description, category=category, tier=int(tier), logo=logo_filename)
    db.session.add(new_vendor)
    db.session.commit()
    
    flash(f"Vendor '{name}' berhasil ditambahkan ke Tier {tier}!", "success")
    return redirect(url_for('vendor', category=category))

@app.route('/edit-vendor/<int:vendor_id>', methods=['POST'])
def edit_vendor(vendor_id):
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    
    vendor = db.session.get(Vendor, vendor_id)
    if vendor:
        vendor.name = request.form.get('name')
        vendor.description = request.form.get('description')
        
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename != '':
            filename = secure_filename(f"vendor_{vendor.id}_{datetime.now().strftime('%H%M%S')}_{logo_file.filename}")
            logo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            vendor.logo = filename
            
        db.session.commit()
        flash(f"Data vendor '{vendor.name}' diperbarui!", "success")
        return redirect(url_for('vendor', category=vendor.category))
    return redirect(url_for('vendor'))

@app.route('/delete-vendor/<int:vendor_id>')
def delete_vendor(vendor_id):
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    
    vendor = db.session.get(Vendor, vendor_id)
    if vendor:
        nama_vendor = vendor.name
        kategori = vendor.category
        db.session.delete(vendor)
        
        log = ActivityLog(user_id=user.id, action=f"Menghapus Vendor: {nama_vendor}")
        db.session.add(log)
        db.session.commit()
        
        flash(f"Vendor '{nama_vendor}' berhasil dihapus!", "success")
        return redirect(url_for('vendor', category=kategori))
    return redirect(url_for('vendor'))

# --- MANAJEMEN KARYAWAN & PEKERJAAN ---
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
    return redirect(url_for('karyawan'))

@app.route('/delete-user/<int:user_id>')
def delete_user(user_id):
    curr = get_current_user()
    if curr and curr.role == 'owner':
        target = db.session.get(User, user_id)
        if target and target.role != 'owner':
            db.session.delete(target)
            db.session.commit()
    return redirect(url_for('karyawan'))

@app.route('/tambah-pekerjaan', methods=['POST'])
def tambah_pekerjaan():
    user = get_current_user()
    date_str = request.form.get('event_date')
    if date_str:
        event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        status = 'todo' if (event_date - datetime.now().date()).days <= 180 else 'waiting'
    else:
        event_date = None
        status = 'todo'

    new_task = Task(client_name=request.form.get('title'), event_date=event_date, venue=request.form.get('venue'), status=status, assigned_to=int(request.form.get('assigned_to')))
    db.session.add(new_task)
    
    log = ActivityLog(user_id=user.id, action=f"Tambah Client: {request.form.get('title')}")
    db.session.add(log)
    db.session.commit()
    return redirect(url_for('semuapekerjaan'))

@app.route('/delete-task/<int:task_id>')
def delete_task(task_id):
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    task = db.session.get(Task, task_id)
    if task:
        nama_klien = task.client_name
        db.session.delete(task)
        log = ActivityLog(user_id=user.id, action=f"Menghapus Event: {nama_klien}")
        db.session.add(log)
        db.session.commit()
        flash(f"Pekerjaan {nama_klien} berhasil dihapus!", "success")
    return redirect(request.referrer or url_for('home'))

@app.route('/api/tasks/<int:task_id>/edit', methods=['POST'])
def edit_task_api(task_id):
    user = get_current_user()
    if not user: return jsonify({'error': 'Sesi habis'}), 401
    
    task = db.session.get(Task, task_id)
    if not task: return jsonify({'error': 'Not found'}), 404
    
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if not new_status: return jsonify({'error': 'Status invalid'}), 400

    old_status = task.status or 'unknown'
    task.status = new_status
    
    log = ActivityLog(user_id=user.id, action=f"Geser '{task.client_name}' dari {old_status.upper()} ke {new_status.upper()}")
    db.session.add(log)
    db.session.commit()
    return jsonify({'success': True})

# --- RUTINITAS LAIN ---
@app.route('/pengaturan')
def pengaturan():
    return render_template('pengaturan.html')

@app.route('/klien')
def klien():
    return render_template('klien.html')

if __name__ == '__main__':
    app.run(debug=True)