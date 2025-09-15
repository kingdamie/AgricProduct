# Agricultural Product Prediction System

A Django web application for predicting agricultural product metrics based on various factors.

## Features

- User authentication (signup/login)
- Input form for agricultural data
- Prediction of production, yield, and price
- Dashboard to view previous predictions
- Modern UI with Bootstrap 5

## Installation

1. Clone the repository
2. Create and activate a virtual environment
3. Install requirements: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Run the development server: `python manage.py runserver`

## Usage

1. Access the application at `http://localhost:8000`
2. Sign up or log in
3. Enter agricultural data to get predictions
4. View your prediction history in the dashboard