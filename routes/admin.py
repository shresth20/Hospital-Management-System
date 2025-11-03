from flask import Blueprint, url_for, render_template, redirect, request, flash
from flask_login import login_required
from sqlalchemy import func
from datetime import datetime

from routes.auth import bcrypt, check_user_role
from models import db, User, Department, Appointment

from chart import plot_to_img
import matplotlib.pyplot as plt


admin = Blueprint('admin', __name__)


@admin.route('/')
@login_required
def dashboard():
    check_user_role('admin')

    status_counts = (
        db.session.query(Appointment.status, db.func.count(Appointment.id))
        .group_by(Appointment.status)
        .all()
    )

    labels = [status for status, _ in status_counts]
    values = [count for _, count in status_counts]

    # Pie chart for appointment status
    plt.figure(figsize=(4, 4))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title("Appointment Status Distribution")
    appointment_chart = plot_to_img()

    # Patient age distribution
    patients = User.query.filter_by(role='patient').all()
    from datetime import date as _date
    ages = []
    for p in patients:
        dob = getattr(p, 'dob', None)
        if not dob:
            continue
        try:
            dob_date = dob if isinstance(dob, _date) else dob.date()
            today = _date.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            if age >= 0:
                ages.append(age)
        except Exception:
            continue

    plt.figure(figsize=(5, 3))
    plt.hist(ages, bins=5, color='skyblue', edgecolor='black')
    plt.title("Patient Age Distribution")
    plt.xlabel("Age")
    plt.ylabel("Count")
    age_chart = plot_to_img()

    doctors = User.query.filter_by(role='doctor').all()
    spec_counts = {}
    for d in doctors:
        spec = getattr(d, 'specialization', None)
        spec_name = spec.name if spec and hasattr(
            spec, 'name') else (str(spec) if spec else 'Unknown')
        spec_counts[spec_name] = spec_counts.get(spec_name, 0) + 1

    labels = list(spec_counts.keys())
    values = list(spec_counts.values())
    x = list(range(len(labels)))

    plt.figure(figsize=(5, 3))
    plt.bar(x, values, color='lightgreen')
    plt.title("Doctors per Specialization")
    plt.xticks(x, labels, rotation=30)
    spec_chart = plot_to_img()

    return render_template(
        'admin/dashboard.html',
        appointment_chart=appointment_chart,
        age_chart=age_chart,
        spec_chart=spec_chart,
        total_patients=len(patients),
        total_doctors=len(doctors)
    )


# -------------------DOCTOR--------------------------------------------------------------------------------------------------

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

        dob_str = request.form.get('dob')
        dob = datetime.strptime(
            dob_str, '%Y-%m-%d').date() if dob_str else None

        new_doctor = User(
            email=email,
            password=hashed_password,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            role='doctor',
            contact_number=request.form.get('contact_number'),
            dob=dob,
            gender=request.form.get('gender'),
            qualification=request.form.get('qualification'),
            specialization_id=request.form.get('specialization_id')
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash('Doctor has been added successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    departments = Department.query.all()
    return render_template('admin/doctor/register.html', departments=departments)


# update doctor
@admin.route('/update_doctor/<int:id>', methods=['GET', 'POST'])
@login_required
def update_doctor(id):
    check_user_role('admin')

    doctor = User.query.get_or_404(id)
    if doctor.role != 'doctor':
        flash('Invalid User ID', 'danger')
        return redirect(url_for('admin.view_doctors'))

    if request.method == 'POST':
        doctor.first_name = request.form.get('first_name')
        doctor.last_name = request.form.get('last_name')
        doctor.email = request.form.get('email')
        doctor.contact_number = request.form.get('contact_number')
        doctor.gender = request.form.get('gender')
        doctor.qualification = request.form.get('qualification')
        doctor.specialization_id = request.form.get('specialization_id')

        dob_str = request.form.get('dob')
        if dob_str:
            try:
                doctor.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD', 'danger')
                departments = Department.query.all()
                return render_template('admin/doctor/update.html', doctor=doctor, departments=departments)
        else:
            doctor.dob = None

        db.session.commit()
        flash('Doctor profile has been updated successfully!', 'success')
        return redirect(url_for('admin.view_doctors'))

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


# -------------------PATIENT--------------------------------------------------------------------------------------------------

# patient control
@admin.route('/view_patients')
@login_required
def view_patients():
    check_user_role('admin')
    patients = User.query.filter_by(role='patient').all()
    return render_template('admin/patient/patients.html', patients=patients)

# update patient


# Added methods=['GET', 'POST']
@admin.route('/update_patient/<int:id>', methods=['GET', 'POST'])
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
        patient.gender = request.form.get('gender')
        patient.address = request.form.get('address')

        dob_str = request.form.get('dob')
        if dob_str:
            try:
                patient.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD', 'danger')
                return render_template('admin/patient/update.html', patient=patient)
        else:
            patient.dob = None

        try:
            db.session.commit()
            flash('Patient profile has been updated successfully!', 'success')
            return redirect(url_for('admin.view_patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating patient: {str(e)}', 'danger')
            return render_template('admin/patient/update.html', patient=patient)

    return render_template('admin/patient/update.html', patient=patient)

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

    sort_by = request.args.get('sort', '').lower()
    query = Appointment.query

    if sort_by == 'booked':
        query = query.filter_by(status='Booked')
    elif sort_by == 'completed':
        query = query.filter_by(status='Completed')
    elif sort_by == 'cancelled':
        query = query.filter_by(status='Cancelled')

    appointments = query.order_by(
        Appointment.appointment_datetime.desc()).all()

    return render_template('admin/appointment/appointments.html',
                           appointments=appointments,
                           current_sort=sort_by)
