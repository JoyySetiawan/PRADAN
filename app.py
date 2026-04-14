from flask import Flask, jsonify, request, render_template
from models import db, User, Task, ActivityLog

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pradan.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def can_edit_task(user, task):
    if task.creator.role == 'accounting':
        return user.role == 'accounting'
    if user.role == 'pm':
        return task.assigned_to == user.id
    return True

# ==========================================
# RUTE UNTUK MENAMPILKAN DASHBOARD UI
# ==========================================
@app.route('/')
def home():
    # Ini akan mencari file dashboard.html di dalam folder "templates"
    return render_template('dashboard.html')
# ==========================================

@app.route('/api/history', methods=['GET'])
def get_history():
    current_user_id = int(request.args.get('user_id', 1)) 
    user = db.session.get(User, current_user_id)
    
    if not user or user.role not in ['owner', 'accounting', 'pa']:
        return jsonify({'error': 'Akses Ditolak: Hanya Manajemen yang bisa melihat riwayat.'}), 403

    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).all()
    hasil = [{'action': log.action, 'task_id': log.task_id} for log in logs]
    return jsonify(hasil)

@app.route('/api/tasks/<int:task_id>/edit', methods=['POST'])
def edit_task(task_id):
    current_user_id = int(request.args.get('user_id', 1)) 
    user = db.session.get(User, current_user_id)
    task = db.session.get(Task, task_id)
    
    if not task:
        return jsonify({'error': 'Pekerjaan tidak ditemukan'}), 404

    if not can_edit_task(user, task):
        return jsonify({'error': 'Akses Ditolak: Anda tidak punya wewenang mengedit ini.'}), 403
    
    data = request.json or {}
    old_status = task.status
    task.status = data.get('status', task.status)
    
    new_log = ActivityLog(user_id=user.id, task_id=task.id, action=f"Mengubah status dari {old_status} menjadi {task.status}")
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({'message': 'Sukses mengubah pekerjaan!'})

if __name__ == '__main__':
    app.run(debug=True)