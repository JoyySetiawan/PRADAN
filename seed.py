from app import app, db
from models import User, Task

# Membuka konteks aplikasi agar bisa mengakses database
with app.app_context():
    # Reset database (hapus yang lama, buat baru)
    db.drop_all()
    db.create_all()

    # 1. Memasukkan Karyawan Pradan Organizer
    owner = User(name="Joy Setiawan", role="owner")
    accounting = User(name="Sari", role="accounting")
    pm = User(name="Budi", role="pm")
    pa = User(name="Ayu", role="pa")

    db.session.add_all([owner, accounting, pm, pa])
    db.session.commit() # Simpan ke database

    # 2. Memasukkan Kartu Pekerjaan (Task)
    # Task 1: Dibuat oleh Accounting
    task_keuangan = Task(
        title="Menghitung DP Catering Klien A", 
        status="todo", 
        created_by=accounting.id, 
        assigned_to=accounting.id
    )
    
    # Task 2: Dibuat oleh Owner, dikerjakan oleh PM
    task_lapangan = Task(
        title="Cek Venue Gedung", 
        status="doing", 
        created_by=owner.id, 
        assigned_to=pm.id
    )

    db.session.add_all([task_keuangan, task_lapangan])
    db.session.commit()

    print("✅ Berhasil! Data karyawan dan pekerjaan dummy sudah dimasukkan ke database.")