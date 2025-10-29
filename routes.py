from sqlalchemy import or_
from flask import Blueprint, url_for, render_template, redirect, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from sqlalchemy import func
from datetime import date, timedelta, datetime

from models import db, User, Department, Appointment, Treatment, DoctorAvailability

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

# doctor dashboard
@doctor.route('/')
@login_required
def dashboard():
    check_user_role('doctor')

    today, next_week = date.today(), date.today()+timedelta(days=7)
    appointments = (
        Appointment.query.filter(
            Appointment.doctor_id == current_user.id,
            Appointment.status == 'Booked',
            Appointment.appointment_datetime.between(
                datetime.now(), datetime.combine(next_week, datetime.max.time())
            )
        )
        .order_by(Appointment.appointment_datetime.asc())
        .all()
    )
    return render_template('doctor/dashboard.html', appointments=appointments)

# update appointment status


@doctor.route('/appointment/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    check_user_role('doctor')

    appointment = Appointment.query.get_or_404(id)
    if appointment.doctor_id != current_user.id:
        flash('Not authorized.', 'danger')
        
    else:
        status = request.form.get('status')
        if status in ['Completed', 'Cancelled']:
            appointment.status = status
            db.session.commit()
            flash(f'Appointment marked as {status}.', 'success')
        else:
            flash('Invalid status.', 'danger')
    return redirect(url_for('doctor.dashboard'))


# treatment to patients

@doctor.route('/appointment/treatment/<int:id>', methods=['GET', 'POST'])
@login_required
def treatment(id):
    check_user_role('doctor')

    appointment = Appointment.query.get_or_404(id)

    if appointment.doctor_id != current_user.id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('doctor.dashboard'))
    
    if appointment.status != 'Booked':
        flash('Can only treat booked appointments.', 'warning')
        return redirect(url_for('doctor.dashboard'))

    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        if not diagnosis:
            flash('Diagnosis required.', 'danger')
            return render_template('treatment.html', appointment=appointment)

        new_treatment = Treatment(
            appointment_id=id,
            diagnosis=diagnosis,
            prescription=request.form.get('prescription'),
            notes=request.form.get('notes')
        )

        db.session.add(new_treatment)
        appointment.status = 'Completed'
        db.session.commit()

        flash('Treatment saved. Appointment completed.', 'success')
        return redirect(url_for('doctor.dashboard'))

    return render_template('doctor/treatment.html', appointment=appointment)

# patient history


@doctor.route('/patient_history/<int:id>')
@login_required
def patient_history(id):
    check_user_role('doctor')

    patient = User.query.get_or_404(id)
    history = (
        Appointment.query.filter_by(patient_id=id, status='Completed')
        .join(Treatment)
        .order_by(Appointment.appointment_datetime.desc())
        .all()
    )
    return render_template('patient_history.html', patient=patient, history=history)

# doctor manage his availability


@doctor.route('/availability', methods=['GET', 'POST'])
@login_required
def availability():
    check_user_role('doctor')

    if request.method == 'POST':
        try:
            available_date = datetime.strptime(
                request.form['available_date'], '%Y-%m-%d').date()
            start = datetime.strptime(
                request.form['start_time'], '%H:%M').time()
            end = datetime.strptime(request.form['end_time'], '%H:%M').time()

            if start >= end:
                flash('Start time must be before end time.', 'danger')
            elif available_date < date.today():
                flash('Cannot set past availability.', 'danger')
            else:
                db.session.add(DoctorAvailability(
                    doctor_id=current_user.id,
                    availabile_date=available_date,
                    start_time=start,
                    end_time=end
                ))
                db.sessoin.commit()
                flash('Availability added.', 'success')

        except Exception as e:
            db.sessoin.commit()
            flash('Availability added.', 'success')
        return redirect(url_for('doctor.availability'))

    today, next_week = date.today(), date.today() + timedelta(days=7)
    slots = (
        DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == current_user.id,
            DoctorAvailability.available_date.between(today, next_week)
        )
        .order_by(DoctorAvailability.available_date, DoctorAvailability.start_time)
        .all()
    )
    return render_template('manage_availability.html', slots=slots)

# delete availability


@doctor.route('/availability/delete/<int:id>', methods=['POST'])
@login_required
def delete_slot(id):
    check_user_role('doctor')

    slot = DoctorAvailability.query.get_or_404(id)
    if slot.doctor_id != current_user.id:
        flash('Not authorized.', 'danger')
    else:
        db.session.delete(slot)
        db.session.commit()
        flash('Slot deleted.', 'success')
    return redirect(url_for('doctor.availability'))


# -------------------PATIENT ROURTES-------------------------------------------------

# patient dashbaord
@patient.route('/')
@login_required
def dashboard():
    check_user_role('patient')
    upcoming = Appointment.query.filter(
        Appointment.patient_id == current_user.id,
        Appointment.status == 'Booked',
        Appointment.appointment_datetime >= datetime.now()
    ).order_by(Appointment.appointment_datetime.asc()).all()

    past = Appointment.query.filter(
        Appointment.patient_id == current_user.id,
        Appointment.status.in_(['Completed', 'Cancelled'])
    ).order_by(Appointment.appointment_datetime.desc()).all()

    return render_template('patient/dashboard.html', upcoming=upcoming, past=past)

# find doctor


@patient.route('/find_doctors')
@login_required
def find_doctors():
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

    return render_template('patient/find_doctors.html', doctors=filtered_doctors, query=query)

# book appointment


@patient.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def book_appointment(doctor_id):
    if current_user.role != 'patient':
        flash('Only patients can book appointments.', 'error')
        return redirect(url_for('home'))

    doctor = User.query.filter_by(id=doctor_id, role='doctor').first_or_404()

    if request.method == 'POST':
        try:
            appointment_datetime = datetime.fromisoformat(
                request.form['appointment_datetime'])
            reason = request.form['reason']

            # Create new appointment
            new_appointment = Appointment(
                patient_id=current_user.id,
                doctor_id=doctor_id,
                appointment_datetime=appointment_datetime,
                reason=reason,
                status='Booked',
                created_at=datetime.utcnow()
            )

            db.session.add(new_appointment)
            db.session.commit()

            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('patient.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error booking appointment: {str(e)}', 'error')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

    # For GET request, show available slots
    available_slots = {}
    today = date.today()

    # Show slots for next 7 days
    for i in range(7):
        day = today + timedelta(days=i)
        slots = []

        # Create slots from 9 AM to 5 PM
        start_time = datetime.combine(day, datetime.min.time().replace(hour=9))
        end_time = datetime.combine(day, datetime.min.time().replace(hour=17))

        current_slot = start_time
        while current_slot < end_time:
            # Check if slot is already booked
            existing_appointment = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_datetime=current_slot,
                status='Booked'
            ).first()

            if not existing_appointment:
                slots.append(current_slot)

            current_slot += timedelta(minutes=30)  # 30-minute slots

        if slots:  # Only add days that have available slots
            available_slots[day] = slots

    return render_template('patient/appointment.html',
                           doctor=doctor,
                           available_slots=available_slots)

# cancel appointment


@patient.route('/appointment/cancel/<int:id>', methods=['POST'])
@login_required
def cancel_appointment(id):
    check_user_role('patient')

    appt = Appointment.query.get_or_404(id)
    if appt.status != 'Booked':
        flash('Cannot cancel this appointment.', 'warning')
        return redirect(url_for('patient.dashboard'))

    appt.status = 'Cancelled'
    db.session.commit()
    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('patient.dashboard'))

# view treatment


@patient.route('/treatment/<int:id>')
@login_required
def view_treatment(id):
    check_user_role('patient')

    appt = Appointment.query.get_or_404(id)
    
    if appt.patient_id != current_user.id:
        flash('You are not authorized to view this...', 'danger')
        return redirect(url_for('patient.dashboard'))

    if not appt.treatment:
        flash('No treatment found.', 'danger')
        return redirect(url_for('patient.dashboard'))
    return render_template('patient/treatment.html', appointment=appt)

# view/update profile


@patient.route('/profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if current_user.role != 'patient':
        flash('Access denied.', 'error')
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            user = User.query.get(current_user.id)

            user.first_name = request.form.get('first_name')
            user.last_name = request.form.get('last_name')
            user.email = request.form.get('email')
            user.contact_number = request.form.get('contact_number')
            user.gender = request.form.get('gender')
            user.address = request.form.get('address')
            dob_str = request.form.get('dob')
            if dob_str:
                try:
                    user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date format', 'error')
                    return redirect(url_for('patient.update_profile'))

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('patient.update_profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}', 'error')

    return render_template('patient/profile.html')
