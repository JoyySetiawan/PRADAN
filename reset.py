from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.drop_all()
    db.create_all()
    hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
    owner = User(name='Joy Setiawan', email='joy@pradan.com', password=hashed_pw, role='owner', is_approved=True)
    db.session.add(owner)
    db.session.commit()
    print("✅ Database Reset! Login: joy@pradan.com | Password: admin123")