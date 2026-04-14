from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from models import db, User, Task, ActivityLog
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pradan.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'pradan_joy_secret'

db.init_app(app)

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None

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

@app.route('/')
def home():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    total_pekerjaan = Task.query.count()
    sedang_dikerjakan = Task.query.filter_by(status='doing').count()
    total_karyawan = User.query.filter_by(is_approved=True).count()
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', user=user, total_pekerjaan=total_pekerjaan, sedang_dikerjakan=sedang_dikerjakan, total_karyawan=total_karyawan, logs=logs, User=User)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Rute tambahan agar navigasi tidak 404
@app.route('/semuapekerjaan')
def semuapekerjaan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    users = User.query.filter_by(is_approved=True).all()
    todo = Task.query.filter_by(status='todo').all()
    doing = Task.query.filter_by(status='doing').all()
    done = Task.query.filter_by(status='done').all()
    return render_template('SemuaPekerjaan.html', user=user, users=users, todo=todo, doing=doing, done=done)

@app.route('/karyawan')
def karyawan():
    user = get_current_user()
    if not user: return redirect(url_for('login'))
    semua_user = User.query.all()
    return render_template('karyawan.html', user=user, semua_user=semua_user)

if __name__ == '__main__':
    app.run(debug=True)