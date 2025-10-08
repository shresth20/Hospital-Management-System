from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, login_user, logout_user, current_user

from models import db, User
from routes import bcrypt, admin, doctor, patient

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'app_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'

    # initailize instance
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        # this function is used by Flask-Login to reload the user object from the user ID stored in the session
        return User.query.get(int(user_id))

    # register routes
    # app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(doctor, url_prefix='/doctor')
    app.register_blueprint(patient, url_prefix='/patient')

    # create tables if they don't exist
    with app.app_context():  
        db.create_all()
        print('Database Created Successfully !!')

    return app

app = create_app()


# for all users
@app.route('/')
def home():
    return render_template('home.html') 

# AUTH ROUTES
# for all roles
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # redirect on db if already logged in
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
@app.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
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
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

# logout
@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
