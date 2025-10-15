from flask import Blueprint, url_for, render_template, redirect, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from sqlalchemy import func

from models import db, User, Department, Appointment

bcrypt = Bcrypt()

auth = Blueprint('auth', __name__)
admin = Blueprint('admin', __name__)
doctor = Blueprint('doctor', __name__)
patient = Blueprint('patient', __name__)

# function to check current user role and also allow multi user access


def check_user_role(role):
    if current_user.role not in role:
        flash(f'You must be an {role} to view this page.')
        return redirect(url_for('auth.login'))

# ---------------AUTHENTICATOIN ROUTES---------------------------------------------

# for all roles


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # redirect on db if already logged in
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        else:
            return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
        except Exception as e:
            return (f"Error: {e}")

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')

            # redirect by role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif user.role == 'patient':
                return redirect(url_for('patient.dashboard'))
        else:
            flash('Please check email and password.', 'danger')

    return render_template('auth/login.html')

# create new patient


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        # create new patient and redirect to dashboard
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')

        # check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.', 'warning')
            return redirect(url_for('auth.register'))

        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf-8')
        new_patient = User(
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role='patient'
        )
        db.session.add(new_patient)
        db.session.commit()

        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

# logout


@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ---------------ADMIN ROUTES---------------------------------------------

# admin dashboard
@admin.route('/')
@login_required
def dashboard():
    check_user_role('admin')
    total_doctors = User.query.filter_by(role='doctor').count()
    total_patients = User.query.filter_by(role='patient').count()
    total_appointments = Appointment.query.count()
    return render_template('admin/dashboard.html', total_doctors=total_doctors, total_patients=total_patients, total_appointments=total_appointments)

# doctor control


@admin.route('/view_doctors')
@login_required
def view_doctors():
    check_user_role('admin')

    doctors = User.query.filter_by(role='doctor').all()
    return render_template('admin/doctor/doctors.html', doctors=doctors)

# register doctor


@admin.route('/register_doctor', methods=['GET', 'POST'])
@login_required
def register_doctor():
    check_user_role('admin')

    if request.method == 'POST':
        email = request.form.get('email')
        # check if doctor email already exists
        if User.query.filter_by(email=email).first():
            flash('A user with this email already exists.', 'warning')
            return redirect(url_for('admin.add_doctor'))

        hashed_password = bcrypt.generate_password_hash(
            request.form.get('password')).decode('utf-8')
        new_doctor = User(
            email=email,
            password=hashed_password,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            role='doctor',
            specialization_id=request.form.get('specialization_id')
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash('Doctor has been added successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    departments = Department.query.all()
    return render_template('admin/doctor/register.html', departments=departments)


# update doctor
@admin.route('/update_doctor/<int:id>')
@login_required
def update_doctor(id):
    check_user_role('admin')

    doctor = User.query.get_or_404(id)
    if doctor.role != 'doctor':
        flash('Invalid User ID', 'danger')
        return redirect(url_for('admin.view_doctors'))

    if request.method == 'post':
        doctor.first_name = request.form.get('first_name')
        doctor.last_name = request.form.get('last_name')
        doctor.email = request.form.get('email')
        doctor.contact_number = request.form.get('contact_number')
        doctor.specialization_id = request.form.get('specialization_id')
        doctor.session.commit()
        flash('Doctor profile has updated successfully!', 'success')
        return redirect(url_for(admin.view_doctors))

    departments = Department.query.all()
    return render_template('admin/doctor/update.html', doctor=doctor, departments=departments)


# delete doctor
@admin.route('/delete_doctor/<int:id>')
@login_required
def delete_doctor(id):
    check_user_role('admin')

    doctor = User.query.get_or_404(id)
    if doctor.role != 'doctor':
        flash('Invalid user ID.', 'danger')
        return redirect(url_for('admin.view_doctors'))

    db.session.delete(doctor)
    db.session.commit()
    flash('Doctor has been removed/blacklisted from the system.', 'success')
    return redirect(url_for('admin.view_doctors'))


# search/filter doctor
@admin.route('/search_doctors')
@login_required
def search_doctors():
    check_user_role('admin')

    query = request.args.get('search', '').strip()

    if query:
        filtered_doctors = User.query.filter(
            User.role == 'doctor',
            (
                func.concat(User.first_name, ' ', User.last_name).ilike(f"%{query}%") |
                User.qualification.ilike(f"%{query}%")
            )
        ).all()
        print(filtered_doctors)
    else:
        filtered_doctors = User.query.filter_by(role='doctor').all()

    return render_template('admin/doctor/doctors.html', results=filtered_doctors, query=query)

# patient control


@admin.route('/view_patients')
@login_required
def view_patients():
    check_user_role('admin')

    return render_template('admin/patient/patients.html')

# update patient


@admin.route('/update_patient/<int:id>')
@login_required
def update_patient(id):
    check_user_role('admin')

    patient = User.query.get_or_404(id)
    if patient.role != 'patient':
        flash('Invalid user ID.', 'danger')
        return redirect(url_for('admin.view_patients'))

    if request.method == 'POST':
        patient.first_name = request.form.get('first_name')
        patient.last_name = request.form.get('last_name')
        patient.email = request.form.get('email')
        patient.contact_number = request.form.get('contact_number')
        patient.address = request.form.get('address')
        db.session.commit()
        flash('Patient profile has been updated successfully!', 'success')
        return redirect(url_for('admin.view_patients'))

    return render_template('update_patient.html', patient=patient)

# delete patient


@admin.route('/delete_patient/<int:id>')
@login_required
def delete_patient(id):
    check_user_role('admin')

    patient = User.query.get_or_404(id)
    if patient.role != 'patient':
        flash('Invalid user ID.', 'danger')
        return redirect(url_for('admin.view_patients'))

    db.session.delete(patient)
    db.session.commit()
    flash('Patient has been removed/blacklisted from the system.', 'success')
    return redirect(url_for('admin.view_patients'))

# search/filter patient


@admin.route('/search_patients')
@login_required
def search_patients():
    query = request.args.get('search', '')
    results = []
    if query:
        results = (User.query.filter_by(role='patient').filter(
            func.concat(User.first_name, ' ', User.last_name).ilike(f"%{query}%") |
            (User.email.ilike(f"%{query}%")) | (User.contact_number.ilike(f"%{query}%")))
            .all())
    # Also retrieve full list of patients to show below
    patients = User.query.filter_by(role='patient').all()
    return render_template('admin/patient/patients.html', results=results, query=query, patients=patients)

# appointment table


@admin.route('/view_appointments')
@login_required
def view_appointments():
    check_user_role('admin')

    appointments = Appointment.query.options(
        db.joinedload(Appointment.patient),
        db.joinedload(Appointment.doctor).joinedload(User.specialization)
    ).order_by(Appointment.created_at.desc()).all()

    return render_template('admin/appointment/appointments.html', appointments=appointments)


# -----------DOCTOR ROUTES-----------------------------------------------------
@doctor.route('/')
@login_required
def dashboard():
    check_user_role('doctor')

    return render_template('doctor/dashboard.html')


# -------------------PATIENT ROURTES-------------------------------------------------
@patient.route('/')
@login_required
def dashboard():
    check_user_role('patient')

    return render_template('patient/dashboard.html')
