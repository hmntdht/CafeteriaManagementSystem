# Nast Eat - Cafeteria Management System

**Nast Eat** is a web-based Cafeteria Management System designed for students and staff to order food online, manage accounts, and streamline cafeteria operations. This project is developed using HTML, CSS, Bootstrap, and Flask (Python) for the backend. It includes features like user authentication, OTP verification, and payment simulation.

---

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Folder Structure](#folder-structure)
- [Usage](#usage)

---

## Features

1. **User Authentication**
   - Sign up and login functionality.
   - OTP verification for secure login.
   - Forgot password functionality.

2. **Food Ordering**
   - Browse cafeteria menu items.
   - Add items to the cart.
   - Simulate order placement and payment.

3. **Admin Panel**
   - Manage menu items.
   - View orders and payments.

4. **Responsive UI**
   - Mobile-friendly design using Bootstrap.

---

## Technologies Used

- **Frontend**
  - HTML5, CSS3
  - Bootstrap 5

- **Backend**
  - Python 3.x
  - Flask
  - Flask-WTF (for forms)
  - Flask-Mail (for OTP verification)

- **Database**
  - SQLite / MySQL (can be configured)

---

## Installation

Follow these steps to run the project locally:

1. **Clone the repository**

git clone https://github.com/your-username/nast-eat.git
cd nast-eat

**Create a virtual environment
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

**Install dependencies

pip install -r requirements.txt
Set environment variables

Create a .env file and configure:

env

FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password

**Run the Flask application
flask run
Access the application
Open your browser and go to http://127.0.0.1:5000/

**Folder Structure
nast-eat/
│
├── templates/
│   ├── login.html
│   ├── signup.html
│   ├── otp.html
│   └── dashboard.html
│
├── static/
│   ├── css/
│   │   └── style_login.css
│   ├── js/
│   └── images/
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore

]




