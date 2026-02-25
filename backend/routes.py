import os
from flask import render_template, request, url_for, redirect, flash
from flask import current_app as app
from models.models import *
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy import or_

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("email").split("@")[0].capitalize()
        user = User.query.filter_by(email=email).first()
        if user and user.password == password: 
            if not user.is_active:
                return render_template("login.html", msg="Restriced User!!.")
            if user.role == 'admin':
                return redirect(url_for("admin_dashboard", name = name))
            elif user.role == 'student':
                return redirect(url_for("student_dashboard", student_id=user.student_profile.id))

            elif user.role == 'company':
                if user.company_profile.approval_status == 'approved':
                    return redirect(url_for("company_dashboard", company_id=user.company_profile.id))
                elif user.company_profile.approval_status == 'rejected':
                    return render_template("login.html", msg="Your registration was rejected by admin")
                else:
                    return render_template("login.html", msg="Your account is pending approval by admin") 
        else:
            return render_template("login.html", msg="Invalid credentials, please try again")
    return render_template("login.html")


@app.route("/logout")
def logout():
    return redirect(url_for('home'))


@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        full_name = request.form.get("full_name")
        department = request.form.get("department")
        if User.query.filter_by(email=email).first():
            return render_template("register_student.html", msg="Email already exists")
        new_user = User(email=email, password=password, role='student', is_active=True)
        
        new_student = Student(user=new_user, full_name=full_name, department=department)
        try:
            db.session.add(new_user)
            db.session.add(new_student)
            db.session.commit()
            return redirect(url_for('signin'))
        except Exception as e:
            db.session.rollback()
            return render_template("register_student.html", msg="Registration failed, please try again")
    return render_template("register_student.html")


@app.route("/register/company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        company_name = request.form.get("company_name")
        location = request.form.get("location")
        if User.query.filter_by(email=email).first():
            return render_template("register_company.html", msg="Email already exists")
        new_user = User(email=email, password=password, role='company', is_active=True)
        
        new_company = Company(
            user=new_user, 
            company_name=company_name,  
            location=location,
            approval_status='pending')
        try:
            db.session.add(new_user)
            db.session.add(new_company)
            db.session.commit()
            return render_template("login.html", msg1="Registration successful! Wait for Admin approval")
        except:
            db.session.rollback()
            return render_template("register_company.html", msg="Error registering company")
    return render_template("register_company.html")

@app.route("/admin/dashboard/<name>")
def admin_dashboard(name):
    companies = Company.query.all()
    pending_companies = Company.query.filter_by(approval_status='pending').all()
    students = Student.query.all()
    ongoing_drives = Drive.query.filter(Drive.status.in_(['approved'])).all()
    student_applications = Application.query.order_by(Application.application_date.desc()).limit(20).all()

    return render_template("admin_dashboard.html",
                           companies=companies,
                           name=name,
                           role="admin",  
                           pending_companies=pending_companies,
                           students=students,
                           ongoing_drives=ongoing_drives,
                           student_applications=student_applications)

@app.route("/admin/dashboard/<name>")
def admin_dashboard(name):
    companies = Company.query.all()
    pending_companies = Company.query.filter_by(approval_status='pending').all()
    students = Student.query.all()
    ongoing_drives = Drive.query.filter(Drive.status.in_(['approved'])).all()
    student_applications = Application.query.order_by(Application.application_date.desc()).limit(20).all()

    return render_template("admin_dashboard.html",
                           companies=companies,
                           name=name,
                           role="admin",  
                           pending_companies=pending_companies,
                           students=students,
                           ongoing_drives=ongoing_drives,
                           student_applications=student_applications)

@app.route("/admin/approve/company/<int:company_id>/<name>")
def approve_company(company_id, name):
    company = Company.query.get(company_id)
    if company:
        company.approval_status = 'approved'
        db.session.commit()
        flash(f"{company.company_name} approved successfully!", "success")
    return redirect(url_for('admin_dashboard', name=name))

@app.route("/admin/reject/company/<int:company_id>/<name>")
def reject_company(company_id, name):
    company = Company.query.get(company_id)
    if company:
        company.approval_status = 'rejected'
        db.session.commit()
        flash(f"{company.company_name} rejected.", "danger")
    return redirect(url_for('admin_dashboard', name=name))

@app.route("/admin/blacklist/company/<int:company_id>/<name>")
def blacklist_company(company_id, name):
    company = Company.query.get(company_id)
    if company and company.user:
        company.user.is_active = not company.user.is_active
        db.session.commit()        
    return redirect(url_for('admin_dashboard', name=name))

@app.route("/admin/blacklist/student/<int:student_id>/<name>")
def blacklist_student(student_id, name):
    student = Student.query.get(student_id)
    
    if student and student.user:
        student.user.is_active = not student.user.is_active
        db.session.commit()
    return redirect(url_for('admin_dashboard', name=name))

app.route("/admin/search", methods=["GET"])
def admin_search():
    query = request.args.get('q', '').strip()
    admin_name = request.args.get('name', 'Admin')
    if not query:
        return redirect(url_for('admin_dashboard', name=admin_name))
    companies = Company.query.filter(Company.company_name.ilike(f'%{query}%')).all()
    students = Student.query.filter(Student.full_name.ilike(f'%{query}%')).all()
    return render_template("admin_dashboard.html",
                           name=admin_name,
                           role="admin",
                           companies=companies,
                           students=students,
                           pending_companies=[],
                           ongoing_drives=[],
                           student_applications=[],
                           search_query=query) 
