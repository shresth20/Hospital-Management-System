from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()



# department db schema
class Department(db.Model):
    __tablename__='departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # relation to user model - for doctor in this department
    doctors = db.relationship('User', back_populates='specialization', lazy=True)
    
    def __repr__(self):
        return f'<Department {self.name}>'
    

# users db schema
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # role - admin, doctor, patient
    role = db.Column(db.String(20), nullable=False)
    contact_number = db.Column(db.String(100), nullable=True)
    
    # for patient
    gender = db.Column(db.String(10), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    patient_appointments = db.relationship('Appointment', foreign_keys='Appointment.patient_id', back_populates='patient', lazy=True)

    # for doctor
    qualification = db.Column(db.String(200))
    specialization_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    specialization = db.relationship('Department', back_populates='doctors')
    doctor_appointments = db.relationship('Appointment', foreign_keys='Appointment.doctor_id', back_populates='doctor', lazy=True)

    def __repr__(self):
        return f'User {self.first_name}{self.last_name}({self.role})'
    


# appointment db schema
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)

    # for patient
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient = db.relationship('User', foreign_keys=[patient_id], back_populates='patient_appointments')
    appointment_datatime = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text)
    
    # status- Booked, Completed, Cancelled
    status = db.Column(db.String(20), nullable=False, default='Booked')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # for doctor
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor = db.relationship('User', foreign_keys=[doctor_id], back_populates='doctor_appointments')

    # one-one relation 
    treatment = db.relationship('Treatment', back_populates='appointment', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Appointment {self.id} on {self.appointment_datetime} with Dr. {self.doctor.last_name}>"
    


# treatment db schema
class Treatment(db.Model):
    __tablename__ = 'treatments'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # one-to-one relation
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), unique=True, nullable=False)

    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # back reference to the Appointment object
    appointment = db.relationship('Appointment', back_populates='treatment')

    def __repr__(self):
        return f"<Treatment for Appointment {self.appointment_id}>"