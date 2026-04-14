from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) 
    is_approved = db.Column(db.Boolean, default=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=True) # Untuk monitoring H-6 Bulan
    venue = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='waiting') # waiting, todo, done
    
    # Bagian Keuangan (Hanya bisa diedit Accounting)
    total_budget = db.Column(db.Float, default=0.0)
    amount_paid = db.Column(db.Float, default=0.0)
    payment_proof = db.Column(db.String(200), nullable=True) 
    
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    assignee = db.relationship('User', foreign_keys=[assigned_to])

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)