from flask import Blueprint, url_for, render_template, redirect, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

from models import db, User

bcrypt = Bcrypt()

auth = Blueprint('auth', __name__)


# function to check current user role and also allow multi user access
def check_user_role(role):
    if current_user.role not in role:
        flash(f'You must be an {role} to view this page.')
        return redirect(url_for('auth.login'))



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
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
