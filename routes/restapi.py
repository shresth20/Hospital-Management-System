from flask import Blueprint, request
from flask_restful import Resource, Api
from models import db, User, Appointment
from datetime import datetime

api_bp = Blueprint('api', __name__)
api = Api(api_bp)


class DoctorList(Resource):
    def get(self):
        doctors = User.query.filter_by(role='doctor').all()
        return [{"id": d.id, "name": f"{d.first_name} {d.last_name}", "department": d.qualification} for d in doctors], 200


class PatientList(Resource):
    def get(self):
        patients = User.query.filter_by(role='patient').all()
        return [{"id": p.id, "name": f"{p.first_name} {p.last_name}", "contact": p.contact_number} for p in patients], 200


class AppointmentAPI(Resource):
    def get(self):
        appointments = Appointment.query.all()
        return [{
            "id": a.id,
            "doctor_id": a.doctor_id,
            "patient_id": a.patient_id,
            "datetime": a.appointment_datetime.isoformat(),
            "status": a.status
        } for a in appointments], 200

    def post(self):
        data = request.get_json()
        new_appointment = Appointment(
            doctor_id=data['doctor_id'],
            patient_id=data['patient_id'],
            appointment_datetime=datetime.fromisoformat(data['datetime']),
            status='Booked'
        )
        db.session.add(new_appointment)
        db.session.commit()
        return {"message": "Appointment created successfully"}, 201

    def put(self):
        data = request.get_json()
        appt = Appointment.query.get(data['id'])
        if not appt:
            return {"error": "Appointment not found"}, 404
        appt.status = data.get('status', appt.status)
        db.session.commit()
        return {"message": "Appointment updated"}, 200

    def delete(self):
        data = request.get_json()
        appt = Appointment.query.get(data['id'])
        if not appt:
            return {"error": "Appointment not found"}, 404
        db.session.delete(appt)
        db.session.commit()
        return {"message": "Appointment deleted"}, 200


api.add_resource(DoctorList, '/doctors')
api.add_resource(PatientList, '/patients')
api.add_resource(AppointmentAPI, '/appointments')
