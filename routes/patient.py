from flask import Blueprint, url_for, render_template, redirect, request, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date, timedelta, datetime

from routes.auth import check_user_role
from models import db, User, Appointment, DoctorAvailability

from chart import plot_to_img
import matplotlib.pyplot as plt

patient = Blueprint('patient', __name__)

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

    # chart
    appts = Appointment.query.filter_by(patient_id=current_user.id).all()
    counts = {'Booked': 0, 'Completed': 0, 'Cancelled': 0}
    for appt in appts:
        if appt.status in counts:
            counts[appt.status] += 1

    plt.figure(figsize=(4, 4))
    plt.pie(counts.values(), labels=counts.keys(), autopct='%1.1f%%', startangle=90)
    plt.title("Your Appointment Status Ratio")
    chart = plot_to_img()

    return render_template('patient/dashboard.html', upcoming=upcoming, past=past, chart=chart)

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

## booking appointment 
@patient.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def book_appointment(doctor_id):
    if current_user.role != 'patient':
        flash('Only patients can book appointments.', 'danger')
        return redirect(url_for('home'))

    doctor = User.query.filter_by(id=doctor_id, role='doctor').first_or_404()

    if request.method == 'POST':
        try:
            appointment_datetime = datetime.fromisoformat(request.form['appointment_datetime'])
            reason = request.form['reason']

            # Check for slot conflicts
            conflict = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_datetime=appointment_datetime,
                status='Booked'
            ).first()

            if conflict:
                flash('That time slot is already booked.', 'danger')
            else:
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
            flash(f'Error booking appointment: {str(e)}', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

    # Show available slots from DoctorAvailability
    today = date.today()
    next_week = today + timedelta(days=7)

    availability_records = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.available_date.between(today, next_week)
    ).order_by(DoctorAvailability.available_date).all()

    available_slots = {}
    for record in availability_records:
        slots = []
        start_dt = datetime.combine(record.available_date, record.start_time)
        end_dt = datetime.combine(record.available_date, record.end_time)

        # Generate 30-min slots
        current_slot = start_dt
        while current_slot < end_dt:
            # Check if already booked
            booked = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_datetime=current_slot,
                status='Booked'
            ).first()

            if not booked:
                slots.append(current_slot)
            current_slot += timedelta(minutes=30)

        if slots:
            available_slots[record.available_date] = slots

    return render_template('patient/book_appointment.html',
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
