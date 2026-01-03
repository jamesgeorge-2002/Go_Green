# Go Green - SWCMS (Solid Waste Collection Management System)

A comprehensive Django-based waste collection management system designed to streamline solid waste pickup, tracking, and payment processing for municipalities and panchayaths.

## Features

### For Users (Customers)
- **Pickup Request Management**
  - Request waste pickups with waste type selection (wet, dry, plastic, e-waste, recyclable)
  - Add images and descriptions for pickups
  - Schedule pickup date and time
  - Track pickup status (pending, picked, completed)

- **Payment Management**
  - Online payment via Razorpay integration
  - View payment history and status
  - Download receipts

- **User Dashboard**
  - View upcoming and previous pickups
  - Track reward points based on waste impact
  - Manage profile information
  - Submit feedback and complaints

- **Rewards System**
  - Earn points based on waste collection participation
  - Points calculated by total waste collected and environmental impact
  - Leaderboard ranking

### For Workers
- **Dashboard**
  - View assigned ward pickups
  - Filter by status (pending, picked, completed)
  - Real-time pickup tracking

- **Pickup Management**
  - Mark pickups as picked
  - Mark pickups as completed with waste weight entry
  - **Collect cash payment** option if customer didn't pay online
  - View payment status

- **Receipt Management**
  - Auto-generate PDF receipt on completion
  - Reprint receipts anytime
  - Receipts include:
    - Pickup details (waste type, weight, date)
    - Customer information
    - Payment status
    - Previous 5 pickups history
    - Signature line for verification

- **Feedback Management**
  - View and resolve customer feedback/complaints
  - Respond to feedback

### For Admins
- **User Management**
  - Add, edit, delete users
  - Manage user roles (user, worker, admin)
  - Allocate workers to wards

- **Panchayath & Ward Management**
  - Create and manage panchayaths
  - Create and manage wards within panchayaths
  - Assign workers to wards

- **Payment Tracking**
  - View all payments
  - Track payment status

- **Reward Management**
  - View user reward points
  - Give bonus rewards to least-waste users
  - Track total waste collected per user

- **Feedback Management**
  - View all feedbacks
  - Respond to complaints

### Authentication & Security
- Role-based access control (User, Worker, Admin)
- Login/Register system
- Password reset via email
- Profile management

## Tech Stack

- **Backend:** Django 4.2.7+
- **Database:** SQLite (easily upgradable to PostgreSQL)
- **Payment Gateway:** Razorpay
- **PDF Generation:** ReportLab
- **Frontend:** Bootstrap 5, Bootstrap Icons
- **Email Backend:** Console (development), SMTP (production)

## Installation

### Prerequisites
- Python 3.8+
- pip
- virtualenv (recommended)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/jamesgeorge-2002/Go_Green.git
   cd Go_Green
   ```

2. **Create virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Navigate to Django project**
   ```bash
   cd swcms
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main app: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

## Configuration

### Razorpay Integration
Update settings in `swcms/settings.py`:
```python
RAZORPAY_KEY_ID = 'your_razorpay_key_id'
RAZORPAY_KEY_SECRET = 'your_razorpay_key_secret'
```

### Email Configuration (Production)
Update settings in `swcms/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
DEFAULT_FROM_EMAIL = 'your_email@gmail.com'
```

## Project Structure

```
Go_Green/
├── swcms/                          # Django project root
│   ├── manage.py
│   ├── db.sqlite3
│   ├── swcms/                      # Project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── user_dashboard/             # Main app
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── admin.py
│   │   ├── templates/
│   │   │   └── user_dashboard/
│   │   │       ├── base.html
│   │   │       ├── index.html
│   │   │       ├── login.html
│   │   │       ├── register.html
│   │   │       ├── worker_dashboard.html
│   │   │       ├── admin_dashboard.html
│   │   │       ├── payment.html
│   │   │       ├── pickup_detail.html
│   │   │       └── [other templates]
│   │   ├── static/
│   │   │   └── css/
│   │   │       └── style.css
│   │   └── migrations/
│   └── media/
│       └── pickup_images/
├── requirements.txt
└── README.md
```

## Usage Guide

### For Users
1. **Register** - Create account as User
2. **Request Pickup** - Fill form with waste details and schedule
3. **Make Payment** - Use Razorpay to pay for collection
4. **Track Status** - Monitor pickup in dashboard
5. **View History** - Check completed pickups and earn rewards

### For Workers
1. **Login** - Sign in with worker account
2. **View Dashboard** - See pending pickups in assigned ward
3. **Mark as Picked** - Mark when waste collection starts
4. **Enter Weight** - Enter actual waste weight when complete
5. **Handle Payment** - If online payment not done, collect cash
6. **Print Receipt** - Generate and print customer receipt
7. **Manage Feedback** - Respond to customer feedback

### For Admins
1. **Login** - Sign in with admin account
2. **Manage Users** - Add/edit/delete users and assign roles
3. **Manage Wards** - Create panchayaths and wards
4. **Allocate Workers** - Assign workers to wards
5. **View Reports** - Check payment, feedback, and reward statistics
6. **Bonus Rewards** - Give extra points to top performers

## API Endpoints

### Authentication
- `POST /register/` - User registration
- `POST /register/worker/` - Worker registration
- `POST /register/admin/` - Admin registration
- `POST /login/` - Login
- `GET /logout/` - Logout
- `GET /password-reset/` - Request password reset
- `GET /password-reset/confirm/<uidb64>/<token>/` - Reset password

### User Routes
- `GET /` - User dashboard
- `GET /edit-profile/` - Edit profile
- `GET /request-pickup/` - Request pickup form
- `GET /pickup/<id>/` - View pickup details
- `GET /payment/<id>/` - Make payment
- `GET /request-management/` - View all pickups
- `GET /payment-management/` - View all payments
- `GET /feedback/` - Submit feedback

### Worker Routes
- `GET /worker-dashboard/` - Worker dashboard
- `GET /mark-picked/<id>/` - Mark pickup as picked
- `GET /mark-completed/<id>/` - Mark pickup as completed
- `GET /collect-cash/<id>/` - Record cash payment
- `GET /print-receipt/<id>/` - Print receipt
- `GET /feedback-management/` - View feedback

### Admin Routes
- `GET /admin-dashboard/` - Admin dashboard
- `GET /admin-users/` - User management
- `GET /admin-wards/` - Ward management
- `GET /admin-panchayath/` - Panchayath management
- `GET /admin-rewards/` - Reward management
- `GET /admin-feedbacks/` - Feedback management

## Database Models

### User Profile
- User (Django built-in)
- Profile (role, ward, mobile, location)

### Waste Management
- PickupRequest (waste type, status, weight, schedule)
- Ward (name, number, panchayath)
- Panchayath (name, code, description)

### Payments
- Payment (amount, status, razorpay IDs)

### Feedback
- Feedback (subject, message, status, response)

### Rewards
- Reward (points, total_waste_collected)

## Key Features Implementation

### Forgot Password
- Email-based password reset
- Secure token generation
- Console backend for development

### Payment Processing
- Online payment via Razorpay
- Cash payment option for workers
- Payment status tracking

### Receipt Generation
- Automatic PDF generation on completion
- Includes previous 5 pickups
- Reprint capability anytime
- Print-friendly format

### Reward System
- Automatic point calculation
- Impact-based scoring (waste type + quantity)
- User ranking by environmental contribution
- Bonus reward system for admins

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For support, email support@gogreen.local or open an issue in the repository.

## Future Enhancements

- Mobile app (React Native/Flutter)
- Real-time GPS tracking for workers
- SMS notifications
- Advanced analytics dashboard
- Integration with waste disposal facilities
- IoT bin sensors
- Blockchain-based verification
- AI-powered waste segregation detection
