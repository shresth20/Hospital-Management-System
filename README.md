# 🏥 Hospital Management System

A comprehensive Flask-based web application for managing hospital operations, including patient appointments, doctor availability, treatment records, and administrative functions with role-based access control.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-orange.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

### 🔐 Role-Based Access Control
Three distinct user portals with specific permissions:

#### Admin Portal
- Comprehensive dashboard with system statistics and live charts
- Complete user management (doctors and patients)
  - View all users in data tables
  - Search functionality for doctors and patients
  - Update user profiles
  - Delete user accounts
- Department management (CRUD operations)
- View all appointments across the hospital
- Generate system reports with matplotlib visualizations

#### Doctor Portal
- Personal dashboard with upcoming appointments
- View and manage profile information
- Availability management
  - Set specific dates and time slots
  - Add multiple availability windows
  - Delete availability slots
- Appointment management
  - View assigned appointments
  - Update appointment status (Complete/Cancel)
- Treatment records
  - Create treatment records (diagnosis, prescription, notes)
  - View patient medical history
- Statistics dashboard with visual charts

#### Patient Portal
- User-friendly dashboard
- View and update profile information
- Search doctors by department/specialization
- Smart appointment booking
  - Real-time doctor availability checking
  - Book appointments with available doctors
  - View booking confirmation
- Appointment history
  - View all past and upcoming appointments
  - Cancel booked appointments
- Access treatment records from completed visits
- Personal statistics dashboard

---

## 🛠 Technology Stack

### Backend
- **Flask** - Lightweight Python web framework
- **Flask-SQLAlchemy** - ORM for database operations
- **Flask-Login** - User session management
- **Flask-RESTful** - RESTful API development
- **Flask-Bcrypt** - Password hashing

### Frontend
- **HTML5/CSS3** - Structure and styling
- **Jinja2** - Template engine
- **Bootstrap 5** - Responsive UI framework
- **JavaScript** - Client-side interactivity

### Database
- **SQLite** - Lightweight relational database

### Visualization
- **Matplotlib** - Statistical charts and graphs

---

## 🗄 Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐
│   DEPARTMENT    │
│─────────────────│
│ id (PK)         │
│ name (UNIQUE)   │
│ description     │
└─────────────────┘
        │
        │ 1:N
        ▼
┌─────────────────┐       ┌──────────────────────┐
│      USER       │       │ DOCTOR_AVAILABILITY  │
│─────────────────│       │──────────────────────│
│ id (PK)         │◄──────│ id (PK)              │
│ email (UNIQUE)  │  1:N  │ doctor_id (FK)       │
│ password        │       │ available_date       │
│ first_name      │       │ start_time           │
│ last_name       │       │ end_time             │
│ role            │       └──────────────────────┘
│ contact_number  │
│ gender          │       ┌──────────────────────┐
│ dob             │       │    APPOINTMENT       │
│ address         │       │──────────────────────│
│ qualification   │◄──────│ id (PK)              │
│ specialization  │  1:N  │ patient_id (FK)      │
└─────────────────┘       │ doctor_id (FK)       │
        │                 │ appointment_datetime │
        │                 │ reason               │
        │                 │ status               │
        │                 │ created_at           │
        │                 └──────────────────────┘
        │                         │
        │                         │ 1:1
        │                         ▼
        │                 ┌──────────────────────┐
        │                 │     TREATMENT        │
        │                 │──────────────────────│
        └─────────────────│ id (PK)              │
          1:N             │ appointment_id (FK)  │
                          │ diagnosis            │
                          │ prescription         │
                          │ notes                │
                          │ created_at           │
                          └──────────────────────┘
```
---

## 📡 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/auth/login` | Render login page | Public |
| POST | `/auth/login` | Authenticate user | Public |
| GET | `/auth/register` | Render registration page | Public |
| POST | `/auth/register` | Register new patient | Public |
| GET | `/auth/logout` | Logout user | Authenticated |

### Admin Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/admin/` | Admin dashboard | Admin |
| GET | `/admin/doctor` | List all doctors | Admin |
| GET | `/admin/search_doctor` | Search doctors | Admin |
| POST | `/admin/update_doctor/<id>` | Update doctor data | Admin |
| DELETE | `/admin/delete_doctor/<id>` | Delete doctor | Admin |
| GET | `/admin/patient` | List all patients | Admin |
| GET | `/admin/search_patient` | Search patients | Admin |
| POST | `/admin/update_patient/<id>` | Update patient data | Admin |
| DELETE | `/admin/delete_patient/<id>` | Delete patient | Admin |
| GET | `/admin/stats` | View statistics charts | Admin |
| GET | `/admin/appointments` | View all appointments | Admin |

### Doctor Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/doctor/` | Doctor dashboard | Doctor |
| GET | `/doctor/profile` | View profile | Doctor |
| GET | `/doctor/appointment/update_status/<id>` | Update appointment status | Doctor |
| GET | `/doctor/appointment/treatment/<id>` | Render treatment form | Doctor |
| POST | `/doctor/appointment/treatment/<id>` | Submit treatment data | Doctor |
| GET | `/doctor/patient_history/<id>` | View patient history | Doctor |
| GET | `/doctor/availability` | Manage availability | Doctor |
| POST | `/doctor/availability` | Add availability slot | Doctor |
| DELETE | `/doctor/delete_availability/<id>` | Delete availability | Doctor |
| GET | `/doctor/stats` | View statistics | Doctor |

### Patient Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/patient/` | Patient dashboard | Patient |
| GET | `/patient/profile` | View profile | Patient |
| POST | `/patient/update_profile` | Update profile | Patient |
| GET | `/patient/find_doctors` | Search doctors | Patient |
| GET | `/patient/book_appointment/<doctor_id>` | Render booking form | Patient |
| POST | `/patient/book_appointment/<doctor_id>` | Book appointment | Patient |
| POST | `/patient/appointment/cancel/<id>` | Cancel appointment | Patient |
| GET | `/patient/treatment/<id>` | View treatment details | Patient |
| GET | `/patient/stats` | View statistics | Patient |

### RESTful API Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/doctors` | List all doctors | API |
| GET | `/api/patients` | List all patients | API |
| GET | `/api/appointments/` | View appointments | API |
| POST | `/api/appointments/<id>` | Create appointment | API |
| PUT | `/api/appointments/<id>` | Update appointment | API |
| DELETE | `/api/appointments/<id>` | Delete appointment | API |

---

## 📁 Project Structure

```
hospital-management-system/
│
├── app.py                      # Flask application entry point
├── models.py                   # SQLAlchemy database models
├── requirements.txt            # Python dependencies
├── chart.py                    # To plot graph by mitplotlib
│
├── routes/                     # Flask Blueprints
│   ├── __init__.py
│   ├── auth.py                # Authentication routes
│   ├── admin.py               # Admin portal routes
│   ├── doctor.py              # Doctor portal routes
│   ├── patient.py             # Patient portal routes
│   └── api.py                 # RESTful API routes
│
├── templates/                  # Jinja2 templates
│   ├── base.html              # Base template
│   ├── home.html              # Landing page
│   │
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   │
│   ├── admin/
|   |   ├── appointment/                  
|   |   │   ├── appointment.html             
|   |   ├── doctor/                 
|   |   │   ├── doctors.html              
|   |   │   ├── register.html           
|   |   │   └── update.html            
|   |   ├── patient/                  
|   |   │   ├── patients.html            
|   |   │   └── update.html              
│   │   └── dashboard.html
│   │
│   ├── doctor/
│   │   ├── dashboard.html
│   │   ├── profile.html
│   │   ├── appointments.html
│   │   ├── availability.html
│   │   ├── treatment.html
│   │   └── stats.html
│   │
│   └── patient/
│       ├── dashboard.html
│       ├── profile.html
│       ├── find_doctors.html
│       ├── book_appointment.html
│       ├── appointments.html
│       ├── treatment.html
│       └── stats.html
│
└── instance/
    └── hospital.db            # SQLite database file
```

---


---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by Shresth Kasera

</div>