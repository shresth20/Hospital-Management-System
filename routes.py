from flask import Blueprint, url_for, render_template, redirect, request, flash
from flask_login import login_required, current_user
from flask_bcrypt import Bcrypt

from models import db, User, Department

bcrypt = Bcrypt()

admin = Blueprint('admin', __name__)
doctor = Blueprint('doctor', __name__)
patient = Blueprint('patient', __name__)

# ADMIN ROUTES
@admin.route('/')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('You must be an admin to view this page.')
        return redirect(url_for('login'))
    
    return render_template('admin/dashboard.html')


@admin.route('/register_doctor', methods=['GET', 'POST'])
@login_required
def register_doctor():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        # check if doctor email already exists
        if User.query.filter_by(email=email).first():
            flash('A user with this email already exists.', 'warning')
            return redirect(url_for('admin.add_doctor'))

        hashed_password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
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
    return render_template('admin/register_doctor.html', departments=departments)




# DOCTOR ROUTES
@login_required
@doctor.route('/')
def dashboard():
    if current_user.role != 'doctor':
        return redirect(url_for('home'))
    
    return render_template('doctor/dashboard.html')


# PATIENT ROURTES
@login_required
@patient.route('/')
def dashboard():
    if current_user.role != 'patient':
        return redirect(url_for('home'))
    
    return render_template('patient/dashboard.html')
