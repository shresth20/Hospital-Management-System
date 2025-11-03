from flask import Blueprint, url_for, render_template, redirect, request, flash
from flask_login import login_required, current_user
from datetime import date, timedelta, datetime

from routes.auth import check_user_role
from models import db, User, Appointment, Treatment, DoctorAvailability

from chart import plot_to_img
import matplotlib.pyplot as plt

doctor = Blueprint('doctor', __name__)

# doctor dashboard


@doctor.route('/')
@login_required
def dashboard():
    check_user_role('doctor')

    appointments = (
        Appointment.query.filter(
            Appointment.doctor_id == current_user.id,
            Appointment.status == 'Booked',
        )
        .order_by(Appointment.appointment_datetime.asc())
        .all()
    )

    past_appt = (
        Appointment.query.filter(
            Appointment.doctor_id == current_user.id,
            Appointment.status != 'Booked',
        )
        .order_by(Appointment.appointment_datetime.desc())
        .all()
    )

    return render_template('doctor/dashboard.html', appointments=appointments,  past_appointments=past_appt)


@doctor.route('/stats')
@login_required
def stats():
    check_user_role('doctor')

    # Chart
    appts = (
        Appointment.query.filter_by(doctor_id=current_user.id)
        .all()
    )
    day_counts = {}
    for appt in appts:
        day = appt.appointment_datetime.strftime('%A')
        day_counts[day] = day_counts.get(day, 0) + 1

    plt.figure(figsize=(5, 3))
    plt.bar(day_counts.keys(), day_counts.values(), color='orange')
    plt.title("Weekly Appointment Load")
    plt.xlabel("Day")
    plt.ylabel("Appointments")
    chart = plot_to_img()

    return render_template('doctor/statistics.html', chart=chart)


@doctor.route('/profile')
@login_required
def profile():
    check_user_role('doctor')
    total_appointments = Appointment.query.filter_by(
        doctor_id=current_user.id).count()

    return render_template('doctor/profile.html',  total_appointments=total_appointments)


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

    today = date.today()
    dob = appointment.patient.dob
    age =  today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

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
    


    return render_template('doctor/treatment.html', appointment=appointment,  patient_age=age)

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
    return render_template('doctor/patient_history.html', patient=patient, history=history)

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
                new_slot = DoctorAvailability(
                    doctor_id=current_user.id,
                    available_date=available_date,
                    start_time=start,
                    end_time=end
                )
                db.session.add(new_slot)
                db.session.commit()
                flash('Availability added successfully.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding availability: {str(e)}', 'danger')

        return redirect(url_for('doctor.availability'))

    # Show upcoming week’s availability
    today, next_week = date.today(), date.today() + timedelta(days=7)
    slots = (
        DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == current_user.id,
            DoctorAvailability.available_date.between(today, next_week)
        )
        .order_by(DoctorAvailability.available_date, DoctorAvailability.start_time)
        .all()
    )

    return render_template('doctor/manage_availability.html', slots=slots)

# delete availability


@doctor.route('/delete_availability/<int:id>', methods=['POST'])
@login_required
def delete_availability(id):
    check_user_role('doctor')
    slot = DoctorAvailability.query.get_or_404(id)

    if slot.doctor_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('doctor.availability'))

    db.session.delete(slot)
    db.session.commit()
    flash("Availability slot deleted.", "success")
    return redirect(url_for('doctor.availability'))
