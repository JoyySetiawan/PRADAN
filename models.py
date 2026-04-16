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
    event_date = db.Column(db.Date, nullable=True) 
    venue = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='waiting') 
    
    # Keuangan
    total_budget = db.Column(db.Float, default=0.0)
    amount_paid = db.Column(db.Float, default=0.0)
    payment_proof = db.Column(db.String(200), nullable=True) 
    
    # --- TAMBAHAN BARU: Catatan Detail & Vendor ---
    progress_notes = db.Column(db.Text, nullable=True)
    vendor_info = db.Column(db.Text, nullable=True)
    
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    assignee = db.relationship('User', foreign_keys=[assigned_to])

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    logo = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    tier = db.Column(db.Integer, nullable=False)