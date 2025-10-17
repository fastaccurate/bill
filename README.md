#  Automated Bill Splitting & Payment Reminder App

A comprehensive full-stack web application for splitting bills among friends and automating payment reminders via SMS. Built with React, Flask, PostgreSQL, and Twilio API.

##  Features

###  **Core Functionality**
- **User Authentication**: Secure registration and login with JWT tokens
- **Group Management**: Create and manage groups with role-based permissions
- **Bill Splitting**: Multiple splitting methods (equal, exact amounts, percentages)
- **Expense Tracking**: Comprehensive expense management with categories
- **Payment Reminders**: Automated SMS reminders via Twilio API
- **Settlement Tracking**: Track who owes what and settlement status

###  **Advanced Features**
- **Real-time Balance Calculations**: Automatic balance updates across groups
- **Bulk Reminders**: Send payment reminders to multiple users at once
- **Expense Analytics**: Statistics and reporting for spending patterns
- **Responsive Design**: Mobile-first design that works on all devices
- **Optimistic Updates**: Smooth UI interactions with real-time updates

##  **Tech Stack**

### **Frontend**
- **React 18** - Modern UI library with hooks
- **Redux Toolkit** - State management with RTK Query
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **Heroicons** - Beautiful hand-crafted SVG icons
- **React Router** - Client-side routing
- **Axios** - HTTP client for API requests

### **Backend**
- **Flask** - Python web framework
- **SQLAlchemy** - Python SQL toolkit and ORM
- **PostgreSQL** - Robust relational database
- **Flask-JWT-Extended** - JWT token authentication
- **Flask-CORS** - Cross-Origin Resource Sharing
- **Twilio API** - SMS messaging service

### **Deployment**
- **Frontend**: Vercel (with automatic deployments)
- **Backend**: AWS Elastic Beanstalk + RDS PostgreSQL
- **SMS Service**: Twilio API integration

## 🚀 **Quick Start**

### **Prerequisites**
- Node.js 16+ and npm/yarn
- Python 3.8+
- PostgreSQL 12+
- Twilio account for SMS functionality

### **Backend Setup**

1. **Clone and navigate to backend directory**
```bash
git clone <repository-url>
cd bill-splitting-app/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Database Configuration  
DATABASE_URL=postgresql://username:password@localhost/billsplit_db

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number

# CORS Origins
CORS_ORIGINS=http://localhost:3000,https://yourdomain.vercel.app
```

5. **Database setup**
```bash
# Create PostgreSQL database
createdb billsplit_db

# Run migrations
flask db upgrade
```

6. **Start development server**
```bash
python run.py
```

Backend will be available at `http://localhost:5000`

### **Frontend Setup**

1. **Navigate to frontend directory**
```bash
cd ../frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Environment configuration**
```bash
# Create .env file
VITE_API_URL=http://localhost:5000/api
```

4. **Start development server**
```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## 📊 **API Documentation**

### **Authentication Endpoints**
```
POST /api/auth/register     - User registration
POST /api/auth/login        - User login
POST /api/auth/refresh      - Refresh JWT token
GET  /api/auth/profile      - Get user profile
PUT  /api/auth/profile      - Update user profile
POST /api/auth/change-password - Change password
```

### **Group Management**
```
GET    /api/groups              - Get user groups
POST   /api/groups              - Create new group
GET    /api/groups/{id}         - Get group details
PUT    /api/groups/{id}         - Update group
POST   /api/groups/{id}/members - Add group member
DELETE /api/groups/{id}/members/{userId} - Remove member
GET    /api/groups/{id}/balance - Get group balance
```

### **Expense Management**
```
GET    /api/expenses/group/{groupId} - Get group expenses
POST   /api/expenses               - Create new expense
GET    /api/expenses/{id}          - Get expense details
PUT    /api/expenses/{id}          - Update expense
DELETE /api/expenses/{id}          - Delete expense
POST   /api/expenses/{id}/settle   - Mark expense as settled
```

### **SMS Reminders**
```
POST /api/reminders/send-payment-reminder - Send individual reminder
POST /api/reminders/send-bulk-reminders   - Send bulk reminders
GET  /api/reminders/group/{id}/reminder-candidates - Get reminder candidates
```

## 🚢 **Deployment**

### **Frontend Deployment (Vercel)**

1. **Connect to Vercel**
```bash
npm install -g vercel
vercel login
```

2. **Deploy**
```bash
vercel --prod
```

3. **Environment Variables**
Set in Vercel dashboard:
- `VITE_API_URL`: Your backend API URL

### **Backend Deployment (AWS)**

1. **Install AWS CLI and EB CLI**
```bash
pip install awsebcli
```

2. **Initialize Elastic Beanstalk**
```bash
eb init
```

3. **Deploy**
```bash
eb create production
eb deploy
```

4. **Database Setup**
- Create RDS PostgreSQL instance
- Update `DATABASE_URL` environment variable
- Run migrations: `eb ssh` then `flask db upgrade`

## 🧪 **Testing**

### **Backend Testing**
```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=app
```

### **Frontend Testing**
```bash
# Run tests
npm test

# Run tests in watch mode
npm test -- --watch
```

## 📁 **Project Structure**

```
bill-splitting-app/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API routes (blueprints)
│   │   ├── services/        # Business logic services
│   │   └── extensions.py    # Flask extensions
│   ├── config.py           # App configuration
│   ├── run.py             # Application entry point
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   ├── pages/         # Page components
│   │   ├── redux/         # Redux store and slices
│   │   ├── services/      # API services
│   │   └── utils/         # Utility functions
│   ├── package.json       # Node.js dependencies
│   └── vite.config.js     # Vite configuration
└── README.md
```

## 🤝 **Contributing**

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

