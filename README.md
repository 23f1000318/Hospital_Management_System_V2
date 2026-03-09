# Hospital Management System

A full-stack Hospital Management System built with Flask (Backend) and Vue.js (Frontend). This application enables seamless management of hospital operations including patient appointments, doctor schedules, treatments, and administrative tasks.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [User Roles](#user-roles)
- [Background Jobs](#background-jobs)
- [Caching Strategy](#caching-strategy)
- [Testing Emails with MailHog](#testing-emails-with-mailhog)

---

## Features

### Admin Features
- **Dashboard** - Overview of hospital statistics (doctors, patients, appointments)
- **User Management** - Approve/reject new doctor registrations, blacklist users
- **Department Management** - CRUD operations for medical departments
- **Doctor Management** - View and manage all doctors
- **Patient Management** - Search patients by name, ID, or contact info
- **Appointment Management** - View all appointments across the hospital

### Doctor Features
- **Dashboard** - Today's appointments, weekly schedule, assigned patients
- **Availability Management** - Set available time slots for next 7 days
- **Appointment Management** - View, complete, or cancel appointments
- **Treatment Records** - Add diagnosis, prescriptions, and notes for appointments
- **Patient History** - View full treatment history of assigned patients

### Patient Features
- **Dashboard** - View upcoming appointments, find doctors, quick actions
- **Doctor Search** - Search by name, department, or specialization
- **Appointment Booking** - Book appointments based on doctor availability
- **Appointment Management** - View and cancel booked appointments
- **Medical History** - View complete treatment history
- **Export Records** - Export treatment history as CSV (async job with email notification)

### Core Functionalities
- **Role-Based Access Control** - Admin, Doctor, Patient roles with specific permissions
- **Conflict Prevention** - Prevents double-booking same time slot
- **Status Transitions** - Appointments flow: `Booked → Completed/Cancelled`
- **Token-based Authentication** - Secure API access with Flask-Security-Too
- **Redis Caching** - Optimized performance with cache invalidation
- **Background Jobs** - Celery tasks for reminders, reports, and exports

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Flask | Web framework |
| Flask-RESTful | REST API development |
| Flask-Security-Too | Authentication & Authorization |
| Flask-SQLAlchemy | ORM for database |
| Flask-Caching | Redis-based caching |
| Celery | Background task processing |
| Redis | Message broker & cache storage |
| SQLite | Database (development) |

### Frontend
| Technology | Purpose |
|------------|---------|
| Vue.js 3 | Frontend framework |
| Vue Router | Client-side routing |
| Pinia | State management |
| Bootstrap 5 | UI components & styling |
| Bootstrap Icons | Icon library |
| Vite | Build tool |

---

## Project Structure

```
hospital-management-system/
├── backend/
│   ├── app.py                 # Flask application factory
│   ├── celery_factory.py      # Celery configuration
│   ├── config.py              # App configuration
│   ├── extensions.py          # Flask extensions
│   ├── models.py              # SQLAlchemy models
│   ├── req.txt                # Python dependencies
│   ├── scripts/
│   │   └── init_db.py         # Database initialization script
│   ├── resources/             # API endpoints
│   │   ├── auth_resource.py
│   │   ├── appointment_resource.py
│   │   ├── dashboard_resource.py
│   │   ├── department_resource.py
│   │   ├── doctor_resource.py
│   │   ├── doctor_dashboard_resource.py
│   │   ├── export_resource.py
│   │   ├── patient_resource.py
│   │   ├── patient_dashboard_resource.py
│   │   ├── treatment_resource.py
│   │   └── user_resource.py
│   ├── services/              # Business logic layer
│   │   ├── appointment_service.py
│   │   ├── doctor_service.py
│   │   ├── patient_service.py
│   │   └── ...
│   ├── tasks/                 # Celery background tasks
│   │   ├── reminder_tasks.py  # Daily appointment reminders
│   │   ├── report_tasks.py    # Monthly doctor reports
│   │   └── export_tasks.py    # CSV export job
│   ├── utils/
│   │   └── email_utils.py     # Email sending utilities
│   └── instance/
│       └── database.sqlite3   # SQLite database
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.vue
        ├── main.js
        ├── router/index.js
        ├── stores/
        │   ├── user.js
        │   └── cart.js
        ├── components/
        │   ├── Navbar.vue
        │   └── Footer.vue
        └── pages/
            ├── HomePage.vue
            ├── LoginPage.vue
            ├── SignupPage.vue
            ├── admin/
            │   ├── DashboardAdminPage.vue
            │   ├── DoctorsAdminPage.vue
            │   ├── PatientsAdminPage.vue
            │   ├── AppointmentsAdminPage.vue
            │   └── DepartmentsAdminPage.vue
            ├── doctor/
            │   ├── DashboardDoctorPage.vue
            │   ├── AppointmentsDoctorPage.vue
            │   └── PatientsDoctorPage.vue
            └── patient/
                ├── DashboardPatientPage.vue
                ├── DoctorsPatientPage.vue
                ├── AppointmentsPatientPage.vue
                ├── HistoryPatientPage.vue
                └── ProfilePatientPage.vue
```

---

## Prerequisites

Ensure you have the following installed:

- **Python 3.9+**
- **Node.js 18+** & **npm**
- **Redis Server** (for caching and Celery)
- **MailHog** (optional, for email testing)

### Installing Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
```

**Windows:**
Download from [Redis for Windows](https://github.com/tporadowski/redis/releases)

### Installing MailHog (for email testing)

**macOS:**
```bash
brew install mailhog
```

**Go Install:**
```bash
go install github.com/mailhog/MailHog@latest
```

**Docker:**
```bash
docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd hospital-management-system
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r req.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
# Default VITE_API_URL=http://localhost:5000/api — update if backend runs on a different port
```

### 4. Initialize Database

```bash
cd ../backend

# Run the initialization script (creates tables, roles, admin user, and sample departments)
python scripts/init_db.py
```

---

## Running the Application

### 1. Start Redis Server

```bash
# If not running as a service
redis-server
```

### 2. Start MailHog (Optional - for email testing)

```bash
mailhog
# Access web UI at http://localhost:8025
```

### 3. Start Backend Server

```bash
cd backend
source venv/bin/activate  # Activate virtual environment (macOS/Linux)
# Windows: venv\Scripts\activate

python app.py
# Server starts at http://localhost:5000 (auto-detects next available port if 5000 is busy)
```

### 4. Start Celery Worker (for background tasks)

```bash
# In a new terminal
cd backend
source venv/bin/activate

celery -A celery_factory:celery worker --loglevel=info
```

### 5. Start Celery Beat (for scheduled tasks)

```bash
# In a new terminal
cd backend
source venv/bin/activate

celery -A celery_factory:celery beat --loglevel=info
```

### 6. Start Frontend Development Server

```bash
# In a new terminal
cd frontend

npm run dev
# Frontend runs at http://localhost:5173
```

### Quick Start (All Services)

Run these in separate terminal tabs:

```bash
# Terminal 1 - Redis
redis-server

# Terminal 2 - MailHog
mailhog

# Terminal 3 - Backend
cd backend && source venv/bin/activate && python app.py

# Terminal 4 - Celery Worker
cd backend && source venv/bin/activate && celery -A celery_factory:celery worker -l info

# Terminal 5 - Celery Beat
cd backend && source venv/bin/activate && celery -A celery_factory:celery beat -l info

# Terminal 6 - Frontend
cd frontend && npm run dev
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/register` | User registration |
| POST | `/auth/logout` | User logout |

### Admin Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Admin dashboard stats |
| GET | `/api/users` | List all users |
| GET | `/api/users/pending` | List pending approvals |
| PATCH | `/api/users/:id/approve` | Approve user |
| PATCH | `/api/users/:id/toggle-active` | Activate/deactivate user |

### Department Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/departments` | List all departments |
| POST | `/api/departments` | Create department |
| GET | `/api/departments/:id` | Get department |
| PUT | `/api/departments/:id` | Update department |
| DELETE | `/api/departments/:id` | Delete department |

### Doctor Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/doctors` | List all doctors |
| GET | `/api/doctors/search?q=` | Search doctors |
| GET | `/api/doctors/:id` | Get doctor details |
| GET | `/api/doctors/:id/availability` | Get doctor availability |
| GET | `/api/doctor/dashboard` | Doctor dashboard |
| PUT | `/api/doctor/availability` | Update availability |
| PATCH | `/api/doctor/appointments/:id/status` | Update appointment status |
| POST | `/api/doctor/appointments/:id/treatment` | Add treatment record |
| GET | `/api/doctor/patients/:id/history` | View patient history |

### Patient Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/patients` | List all patients |
| GET | `/api/patients/search?q=` | Search patients |
| GET | `/api/patient/dashboard` | Patient dashboard |
| GET | `/api/patient/profile` | Get profile |
| PUT | `/api/patient/profile` | Update profile |
| POST | `/api/patient/book-appointment` | Book appointment |
| PATCH | `/api/patient/appointments/:id/cancel` | Cancel appointment |
| GET | `/api/patient/history` | View treatment history |
| POST | `/api/patient/export` | Trigger CSV export |
| GET | `/api/patient/exports` | List previous exports |
| GET | `/api/exports/download/:filename` | Download export file |

### Appointment Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/appointments` | List appointments |
| POST | `/api/appointments` | Create appointment |
| GET | `/api/appointments/:id` | Get appointment |
| PUT | `/api/appointments/:id` | Update appointment |
| DELETE | `/api/appointments/:id` | Delete appointment |

---

## User Roles

### Admin
- Created during initialization
- Default credentials: `admin@hospital.com` / `admin123`
- Full access to all management features

### Doctor
- Registers via signup (requires admin approval)
- Manages own appointments and availability
- Can view patient history and add treatments

### Patient
- Registers via signup (auto-approved)
- Books appointments with available doctors
- Views own medical history and exports records

---

## Background Jobs

### 1. Daily Appointment Reminders
- **Schedule:** Every day at 8:00 AM
- **Task:** Sends email reminders to patients with appointments scheduled for that day
- **Queue:** `reminders`

### 2. Monthly Doctor Activity Reports
- **Schedule:** 1st of every month at 9:00 AM
- **Task:** Generates HTML report with statistics and sends to each doctor
- **Queue:** `reports`

### 3. CSV Export (User-Triggered)
- **Trigger:** Patient clicks "Export Records" in dashboard
- **Task:** Generates CSV with treatment history and sends email notification
- **Files:** Saved to `backend/instance/exports/`

---

## Caching Strategy

| Resource | Cache Duration | Key Pattern |
|----------|---------------|-------------|
| Departments List | 1 hour | `departments_all` |
| Department (single) | 1 hour | Memoized by ID |
| Doctors List | 5 minutes | `doctors_all` |
| Doctor (single) | 5 minutes | Memoized by ID |
| Doctor Availability | 2 minutes | Memoized by doctor ID |
| Admin Dashboard | 1 minute | `admin_dashboard` |
| Doctor Dashboard | 1 minute | `doctor_dashboard_{id}` |
| Patient Dashboard | 1 minute | `patient_dashboard_{id}` |

### Redis Usage
- `redis://localhost:6379/0` - Celery message broker
- `redis://localhost:6379/1` - Celery result backend
- `redis://localhost:6379/2` - API cache

---

## Testing Emails with MailHog

1. Start MailHog:
   ```bash
   mailhog
   ```

2. Access the MailHog web interface:
   ```
   http://localhost:8025
   ```

3. Trigger emails by:
   - Running the daily reminder task manually
   - Triggering a CSV export from patient dashboard
   - Waiting for scheduled monthly reports (or trigger manually)

### Manual Task Testing

```python
# In Flask shell
flask shell

# Trigger daily reminders
from tasks.reminder_tasks import send_daily_appointment_reminders
send_daily_appointment_reminders.delay()

# Trigger export
from tasks.export_tasks import export_patient_treatments_csv
export_patient_treatments_csv.delay(patient_id=1, user_email="test@example.com", user_name="Test User")
```

---

## Environment Variables

### Backend (`backend/.env`)

The backend uses `LocalDevelopmentConfig` by default — no `.env` file is strictly required for local development. Optional overrides:

```env
SECRET_KEY=your-secret-key-here
SECURITY_PASSWORD_SALT=your-salt-here

# SMTP (MailHog defaults)
SMTP_HOST=localhost
SMTP_PORT=1025
SENDER_EMAIL=noreply@hospital.com

# Redis
REDIS_URL=redis://localhost:6379/2
```

### Frontend (`frontend/.env`)

Copy from the provided example:

```bash
cp frontend/.env.example frontend/.env
```

```env
# Backend API URL (update port if backend starts on a different port)
VITE_API_URL=http://localhost:5000/api
```

---

## Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis if not running
redis-server
```

### Celery Worker Not Processing Tasks
```bash
# Ensure Redis is running
# Check worker logs for errors
celery -A celery_factory:celery worker -l debug
```

### Frontend Not Connecting to Backend
- Verify CORS is configured for `http://localhost:5173`
- Check backend is running on port 5000
- Verify API URL in frontend `utils/api.js`

### Database Issues
```bash
# Reset database
cd backend
rm instance/database.sqlite3
python scripts/init_db.py
```

---

## License

This project is developed for educational purposes.

---

## Contributors

Hospital Management System - Built with Flask & Vue.js
