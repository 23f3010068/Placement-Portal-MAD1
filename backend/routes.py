import os
from flask import render_template, request, url_for, redirect
from flask import current_app as app
from models.models import *
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy import or_


UPLOAD = 'static/uploads'
EXTENSION = {'pdf'}
if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD)
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSION



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

@app.route("/admin/approve/company/<int:company_id>/<name>")
def approve_company(company_id, name):
    company = Company.query.get(company_id)
    if company:
        company.approval_status = 'approved'
        db.session.commit()
    return redirect(url_for('admin_dashboard', name=name))

@app.route("/admin/reject/company/<int:company_id>/<name>")
def reject_company(company_id, name):
    company = Company.query.get(company_id)
    if company:
        company.approval_status = 'rejected'
        db.session.commit()
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



@app.route("/company/dashboard/<int:company_id>")
def company_dashboard(company_id):
    company = Company.query.get_or_404(company_id)    
    ongoing_drives = Drive.query.filter(
        Drive.company_id == company_id, 
        Drive.status.in_(['pending', 'approved'])).all()

    closed_drives = Drive.query.filter_by(company_id=company_id, status='closed').all()    
    return render_template("company_dashboard.html", 
                           company=company, 
                           ongoing_drives=ongoing_drives, 
                           closed_drives=closed_drives)


@app.route("/company/create_drive/<int:company_id>", methods=["GET", "POST"])
def create_drive(company_id):
    if request.method == "POST":
        drive_name = request.form.get("drive_name")
        job_title = request.form.get("job_title")
        description = request.form.get("job_description")
        eligibility = request.form.get("eligibility")
        salary = request.form.get("salary")
        location = request.form.get("location")
        deadline_str = request.form.get("deadline")
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        company = Company.query.get(company_id)
        initial_status = 'approved' if company.approval_status == 'approved' else 'pending'

        new_drive = Drive(
            company_id=company_id,
            drive_name=drive_name,
            job_title=job_title,
            job_description=description,
            eligibility_criteria=eligibility,
            salary=salary,
            location=location,
            application_deadline=deadline,
            status=initial_status)
        
        db.session.add(new_drive)
        db.session.commit()        
        return redirect(url_for('company_dashboard', company_id=company_id))
    return render_template("create_drive.html", company_id=company_id)



@app.route("/company/drive/<int:drive_id>/<int:company_id>")
def view_drive_details(drive_id, company_id):
    drive = Drive.query.get_or_404(drive_id)
    applications = Application.query.filter_by(drive_id=drive_id).all()    
    return render_template("drive_info.html", 
                           drive=drive, 
                           applications=applications, 
                           company_id=company_id)


@app.route("/company/drive/complete/<int:drive_id>/<int:company_id>")
def mark_drive_complete(drive_id, company_id):
    drive = Drive.query.get(drive_id)
    if drive:
        drive.status = 'closed'
        db.session.commit()    
    return redirect(url_for('company_dashboard', company_id=company_id))


@app.route("/company/application/review/<int:app_id>/<int:company_id>")
def review_application_page(app_id, company_id):
    application = Application.query.get_or_404(app_id)
    
    return render_template("review_application.html", 
                           application=application, 
                           company_id=company_id)


@app.route("/company/application/update/<int:app_id>/<int:company_id>", methods=["POST"])
def update_application_status(app_id, company_id):
    application = Application.query.get_or_404(app_id)
    new_status = request.form.get("status")
    if new_status in ['shortlisted', 'rejected', 'waiting']:
        application.status = new_status
        db.session.commit()    
    return redirect(url_for('view_drive_details', drive_id=application.drive_id, company_id=company_id))


@app.route("/company/drive/update/<int:drive_id>/<int:company_id>", methods=["GET", "POST"])
def update_drive(drive_id, company_id):
    drive = Drive.query.get_or_404(drive_id)
    if request.method == "POST":
        drive.drive_name = request.form.get("drive_name")
        drive.job_title = request.form.get("job_title")
        drive.job_description = request.form.get("job_description")
        drive.eligibility_criteria = request.form.get("eligibility")
        drive.salary = request.form.get("salary")
        drive.location = request.form.get("location")
        deadline_str = request.form.get("deadline")
        drive.application_deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        drive.status = 'approved'
        db.session.commit()
        return redirect(url_for('company_dashboard', company_id=company_id))
    return render_template("update_drive.html", drive=drive, company_id=company_id)




@app.route("/student/dashboard/<int:student_id>")
def student_dashboard(student_id):
    student = Student.query.get_or_404(student_id)
    companies = Company.query.filter_by(approval_status='approved').all()
    applications = Application.query.filter_by(student_id=student_id).all()
    return render_template("student_dashboard.html", 
                           student=student, 
                           companies=companies, 
                           applications=applications)

@app.route("/student/company/<int:company_id>/<int:student_id>")
def student_company_details(company_id, student_id):
    company = Company.query.get_or_404(company_id)
    drives = Drive.query.filter_by(company_id=company_id, status='approved').all()
    return render_template("company_details.html", 
                           company=company, 
                           drives=drives, 
                           student_id=student_id)

@app.route("/student/drive/<int:drive_id>/<int:student_id>")
def student_drive_details(drive_id, student_id):
    drive = Drive.query.get_or_404(drive_id)
    existing_app = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
    has_applied = True if existing_app else False
    return render_template("student_drive_details.html", 
                           drive=drive, 
                           student_id=student_id,
                           has_applied=has_applied)

@app.route("/student/apply/<int:drive_id>/<int:student_id>")
def apply_for_drive(drive_id, student_id):
    existing_app = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
    if existing_app:
        print("You have already applied for this drive.")
    else:
        new_app = Application(
            student_id=student_id,
            drive_id=drive_id,
            status='applied',
            application_date=datetime.now())
        db.session.add(new_app)
        db.session.commit()
        print("Application submitted successfully!")
    return redirect(url_for('student_dashboard', student_id=student_id))

@app.route("/student/history/<int:student_id>")
def student_history(student_id):
    applications = Application.query.filter_by(student_id=student_id).order_by(Application.application_date.desc()).all()
    return render_template("student_history.html", applications=applications, student_id=student_id)

@app.route("/student/profile/edit/<int:student_id>")
def edit_student_profile(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template("edit_profile.html", student=student)

@app.route("/student/profile/update/<int:student_id>", methods=["POST"])
def update_student_profile(student_id):
    student = Student.query.get_or_404(student_id)
    student.full_name = request.form.get("full_name")
    student.department = request.form.get("department")
    student.phone = request.form.get("phone")
    if request.form.get("cgpa"):
        student.cgpa = float(request.form.get("cgpa"))

    if 'resume' in request.files:
        file = request.files['resume']
        
        # Check if user selected a file
        if file.filename != '': 
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"resume_{student.id}_{filename}"
                save_path = os.path.join('static/uploads', unique_filename)
                file.save(save_path)
                student.resume = unique_filename
                print(f"File saved successfully: {save_path}")
            else:
                print("Invalid file type or no file selected")
    db.session.commit()
    return redirect(url_for('student_dashboard', student_id=student_id))

