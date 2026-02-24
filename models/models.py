from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin', 'company', 'student'
    is_active = db.Column(db.Boolean, default=True)  # For blacklisting
    
    # Relationships
    company_profile = db.relationship("Company", backref="user", uselist=False, cascade="all,delete")
    student_profile = db.relationship("Student", backref="user", uselist=False, cascade="all,delete")


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    approval_status = db.Column(db.String(50), default='pending')  # 'pending', 'approved', 'rejected'
    location = db.Column(db.String(255), nullable=True)
    
    # Relationships
    drives = db.relationship("Drive", cascade="all,delete", backref="company", lazy=True)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(255), nullable=True)
    cgpa = db.Column(db.Float, nullable=True)
    resume = db.Column(db.String(500), nullable=True)  # File path/URL
    
    # Relationships
    applications = db.relationship("Application", cascade="all,delete", backref="student", lazy=True)


class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    job_title = db.Column(db.String(255), nullable=False)
    job_description = db.Column(db.Text, nullable=True)
    eligibility_criteria = db.Column(db.Text, nullable=True)
    application_deadline = db.Column(db.Date, nullable=False)
    salary = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'approved', 'closed'
    drive_name = db.Column(db.String(255), nullable=False)
    
    # Relationships
    applications = db.relationship("Application", cascade="all,delete", backref="drive", lazy=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("drive.id"), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), default='applied')  # 'applied', 'shortlisted', 'selected', 'rejected'
    