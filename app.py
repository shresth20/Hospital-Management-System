from flask import Flask, render_template, url_for
from flask_login import LoginManager

from models import db, User

from routes.auth import auth, bcrypt
from routes.admin import admin
from routes.doctor import doctor
from routes.patient import patient


login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'app_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'

    # initailize instances
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'


    # this function is used by flask-login to reload the user object from the user ID stored in the session
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # register routes
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(doctor, url_prefix='/doctor')
    app.register_blueprint(patient, url_prefix='/patient')





    # create tables if they don't exist
    with app.app_context():  
        db.create_all()
        print('Database Created Successfully !!')

    return app

app = create_app()

# Home for all users
@app.route('/')
def home():
    return render_template('home.html') 


if __name__ == '__main__':
    app.run(debug=True)
