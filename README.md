# Software Engineering Ticket System

## Overview

This project is a Django-based Ticket Management System developed for the Software Engineering module.  
The system implements role-based access control and a full CRUD workflow for ticket lifecycle management.

## Features

- User authentication (login/logout)
- Role-based access (Admin, Technician, Reporter)
- Ticket creation, viewing, assignment, and status updates
- Filtering by status, category, priority
- Bootstrap-based responsive UI
- Seed data using Django fixtures

## Technology Stack

- Python 3.x
- Django
- SQLite (development)
- Bootstrap 5
- Git & GitHub

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Emily-773/Software_Engineering_Ticket_System.git
cd Software_Engineering_Ticket_System
2. Install dependencies
pip install -r requirements.txt
3. Apply migrations
python manage.py migrate
4. Load seed data
python manage.py loaddata tickets/fixtures/seed.json
5. Create superuser
python manage.py createsuperuser
6. Run the server
python manage.py runserver
Roles

Admin – Assign tickets and manage system configuration

Reporter – Create and view tickets

Technician – View assigned tickets and update status

Author

Emily Rutherford
BSc Computer Science
University of Suffolk