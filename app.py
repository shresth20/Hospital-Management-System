from flask import Flask
from models import db  

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'

    db.init_app(app)

    with app.app_context():
        db.create_all()  # create tables if they don't exist
        print('Database creted Successfully !!')

    return app

app = create_app()

@app.route('/')
def home():
    return '<h1> Hello flask </h1>'


if __name__ == '__main__':
    app.run(debug=True)
