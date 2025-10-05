# Medical Image Diagnostics API Server

A comprehensive FastAPI-based backend server for AI-powered medical image diagnostics, supporting brain tumor, breast cancer, and stroke analysis with PostgreSQL database, JWT authentication, and Cloudinary integration.

## 🚀 Features

- **AI-Powered Medical Diagnosis**: Multiple ML models for different medical conditions
  - Brain Tumor Detection (MRI) with segmentation
  - Breast Cancer Analysis (BI-RADS & Pathological)
  - Stroke Classification (MRI)
- **FastAPI Framework**: Modern, fast async web framework for building APIs
- **PostgreSQL Database**: Robust relational database with SQLAlchemy ORM
- **JWT Authentication**: Secure authentication with access/refresh tokens
- **Soft Delete**: Account deactivation with data anonymization for compliance
- **Cloud Storage**: Cloudinary integration for image storage and management
- **Database Migrations**: Alembic-powered migrations with CLI tools
- **Security**: Password hashing, CORS, input validation, rate limiting
- **Modular Architecture**: Clean separation of concerns with services, models, and schemas
- **Docker Support**: Containerized deployment with docker-compose
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation

## 🛠️ Tech Stack

- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens) with refresh token rotation
- **Image Storage**: Cloudinary
- **ML Frameworks**:
  - PyTorch for brain tumor models
  - FastAI for breast cancer BI-RADS classification
  - TensorFlow/Keras for stroke classification
  - OpenCV and Pillow for image processing
- **Validation**: Pydantic for request/response schemas
- **Security**: python-jose for JWT, passlib for password hashing
- **Email**: emails library for notifications
- **Deployment**: Docker, docker-compose, uvicorn

## 📁 Project Structure

```
server/
├── app/
│   ├── api/
│   │   ├── dependencies/          # FastAPI dependencies (auth, etc.)
│   │   └── v1/
│   │       ├── endpoints/         # API route handlers
│   │       │   ├── auth.py        # Authentication endpoints
│   │       │   ├── diagnosis.py   # Brain tumor diagnosis
│   │       │   ├── breast_cancer.py # Breast cancer diagnosis
│   │       │   ├── stroke.py      # Stroke diagnosis
│   │       │   └── statistics.py  # Analytics endpoints
│   │       └── api.py            # API router configuration
│   ├── core/
│   │   ├── config.py             # Application settings & environment
│   │   ├── database.py           # Database configuration
│   │   ├── security.py           # JWT and password utilities
│   │   └── cloudinary_config.py  # Cloud storage configuration
│   ├── models/
│   │   ├── user.py               # User SQLAlchemy model
│   │   ├── diagnosis.py          # Diagnosis results model
│   │   └── ai_models/            # ML model definitions
│   ├── schemas/
│   │   ├── user.py               # User Pydantic schemas
│   │   ├── diagnosis.py          # Diagnosis schemas
│   │   ├── breast_cancer.py      # Breast cancer schemas
│   │   ├── stroke.py             # Stroke schemas
│   │   └── statistics.py         # Analytics schemas
│   └── services/
│       ├── auth_service.py       # Authentication business logic
│       ├── diagnosis_service.py  # Brain tumor ML service
│       ├── breast_cancer_service.py # Breast cancer ML service
│       ├── stroke_service.py     # Stroke ML service
│       ├── statistics_service.py # Analytics service
│       └── cloudinary_service.py # Image storage service
├── alembic/                      # Database migrations
├── brain_tumor_2d/               # Brain tumor ML model directory
├── breast_cancer/                # Breast cancer ML models
├── stroke-classification/        # Stroke ML model
├── uploads/                      # Local upload directories
├── requirements.txt              # Python dependencies
├── main.py                       # FastAPI application entry point
├── migrate.py                    # Migration CLI (Python)
├── migrate.ps1                   # Migration CLI (PowerShell)
├── docker-compose.yml            # Docker services configuration
├── Dockerfile                    # Container build configuration
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ (or Docker for containerized DB)
- Docker & Docker Compose (for containerized deployment)
- pip (Python package manager)

### Installation

1. **Navigate to the server directory**:
   ```bash
   cd server
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Windows Command Prompt
   python -m venv venv
   venv\Scripts\activate.bat

   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   # Copy example environment file
   cp .env.example .env

   # Edit .env file with your configuration
   ```

5. **Set up the database**:
   ```bash
   # Option 1: Using Docker Compose (recommended)
   docker-compose up -d db

   # Option 2: Local PostgreSQL installation
   # Create database: medical_image_diagnostics
   ```

6. **Run database migrations**:
   ```bash
   # Windows PowerShell
   .\migrate.ps1 migrate

   # Python (cross-platform)
   python migrate.py migrate
   ```

### Running the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**API URLs:**
- Base API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs` (Swagger UI)
- Alternative Docs: `http://localhost:8000/redoc` (ReDoc)

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Security (Required)
SECRET_KEY=your-super-secret-key-here-change-this-in-production

# Database (Required)
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=medical_image_diagnostics
POSTGRES_PORT=5432

# Optional: Use SQLite for development
USE_SQLITE=false

# Cloudinary (Required for image storage)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email (Optional - for password reset)
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=Medical Diagnostics

# CORS (Required)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# JWT Settings (Optional - defaults provided)
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

## 🏥 AI Models & Diagnosis Types

### Brain Tumor Detection
- **Input**: MRI brain scans
- **Models**: ResNet18 (classification) + SwinUNet (segmentation)
- **Classes**: glioma, meningioma, pituitary, no tumor
- **Output**: Classification + segmentation mask (if tumor detected)

### Breast Cancer Analysis
- **Input**: Mammograms or histology images
- **Analysis Types**:
  - **BI-RADS**: Breast Imaging Reporting and Data System classification
  - **Pathological**: Tissue analysis for malignancy detection
- **Models**: FastAI (BI-RADS) + ResNet18 (Pathological)

### Stroke Classification
- **Input**: Brain MRI scans
- **Model**: TensorFlow/Keras CNN
- **Classes**: hemorrhagic_stroke, ischemic_stroke, no_stroke

## 📡 API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - User login (returns JWT tokens)
- `GET /me` - Get current user profile
- `POST /refresh-token` - Refresh access token
- `POST /forgot-password` - Initiate password reset
- `POST /reset-password` - Reset password with token
- `POST /change-password` - Change password (authenticated)
- `GET /check-username/{username}` - Check username availability
- `GET /settings` - Get user settings
- `PUT /settings` - Update user settings
- `PUT /profile` - Update user profile
- `DELETE /account` - Soft delete user account (deactivate)

### Brain Tumor Diagnosis (`/api/v1/diagnosis`)
- `POST /diagnose` - Upload MRI for brain tumor analysis
- `GET /` - Get user's diagnosis history
- `GET /{id}` - Get specific diagnosis result
- `PUT /{id}` - Update diagnosis notes

### Breast Cancer Diagnosis (`/api/v1/breast-cancer`)
- `POST /diagnose` - Upload image for breast cancer analysis
- `GET /` - Get breast cancer diagnosis history
- `GET /{id}` - Get specific diagnosis
- `PUT /{id}` - Update diagnosis notes

### Stroke Diagnosis (`/api/v1/stroke`)
- `POST /diagnose` - Upload MRI for stroke analysis
- `GET /` - Get stroke diagnosis history
- `GET /{id}` - Get specific diagnosis
- `PUT /{id}` - Update diagnosis notes

### Statistics & Analytics (`/api/v1/statistics`)
- `GET /dashboard` - Dashboard statistics
- `GET /analytics` - Detailed analytics
- `GET /tumor-distribution` - Tumor type distribution
- `GET /weekly-analytics` - Weekly diagnosis trends

### General
- `GET /` - API root information
- `GET /health` - Health check

## 🗄️ Database Schema

### Users Table
```sql
- id: Primary key
- first_name, last_name: User details
- username, email: Unique identifiers (stored in lowercase)
- phone_number: Optional contact
- hashed_password: bcrypt hashed password
- is_active, is_verified: Account status
- is_deleted: Soft delete flag
- deleted_at: Soft delete timestamp
- gdpr_consent, marketing_consent: User consents with timestamps
- role, institution: Professional information
- dark_mode, interface_scale, default_analysis_model: UI preferences
- email_notifications, push_notifications, analysis_notifications, report_notifications: Notification settings
- data_retention_period, anonymous_analytics, data_sharing: Privacy settings
- created_at, updated_at: Timestamps
- reset_token*: Password reset fields
```

### Diagnosis Results Table
```sql
- id: Primary key
- user_id: Foreign key to users
- image_path: Cloudinary URL
- predicted_class: AI prediction
- confidence_score: Prediction confidence
- segmentation_path*: Segmentation image URL
- diagnosis_type: Type of diagnosis
- analysis_type*: Specific analysis method
- additional_results*: JSON for complex results
- notes*: User notes
- created_at: Timestamp
```

## 🔒 Security Features

- **JWT Authentication**: Stateless auth with access/refresh tokens
- **Password Security**: bcrypt hashing with salt
- **Input Validation**: Pydantic schemas for all requests
- **CORS Protection**: Configurable cross-origin policies
- **Rate Limiting**: Built-in protection against abuse
- **Secure Headers**: FastAPI security middleware
- **Soft Delete**: Account deactivation preserves data integrity
- **Case-Insensitive Auth**: Username/email normalization for consistency
- **Environment Variables**: Sensitive data not in code

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Start all services (API + PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build the image
docker build -t medical-diagnostics-api .

# Run with environment variables
docker run -p 8000:8000 --env-file .env medical-diagnostics-api
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## 📊 Database Migrations

### Using PowerShell (Windows):
```powershell
# Create migration
.\migrate.ps1 create "Add new field"

# Run migrations
.\migrate.ps1 migrate

# Rollback
.\migrate.ps1 rollback

# Check status
.\migrate.ps1 status
```

### Using Python (Cross-platform):
```bash
# Create migration
python migrate.py create "Add new field"

# Run migrations
python migrate.py migrate

# Rollback
python migrate.py rollback

# Check status
python migrate.py status
```

## 🔧 Development Workflow

### Adding New Diagnosis Types

1. **Create ML Model**: Add model files to appropriate directory
2. **Update Schemas**: Add Pydantic schemas in `app/schemas/`
3. **Create Service**: Implement business logic in `app/services/`
4. **Add Endpoints**: Create API routes in `app/api/v1/endpoints/`
5. **Update Models**: Modify database models if needed
6. **Add Migrations**: Create database migrations
7. **Update Frontend**: Update client services and types

### Model Training

Each ML model directory contains:
- `requirements.txt`: Model-specific dependencies
- Model files: Pre-trained weights and architectures
- Training scripts (if available)

## 📈 Monitoring & Logging

- **Health Checks**: `/health` endpoint for monitoring
- **Structured Logging**: JSON-formatted logs
- **Error Handling**: Comprehensive error responses
- **Performance**: Async operations for scalability

## 🚀 Production Deployment

### Recommended Setup

1. **Web Server**: nginx as reverse proxy
2. **WSGI Server**: gunicorn with uvicorn workers
3. **Database**: Managed PostgreSQL instance
4. **File Storage**: Cloudinary or AWS S3
5. **SSL/TLS**: Let's Encrypt certificates
6. **Monitoring**: Application performance monitoring

### Production Commands

```bash
# Using gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Using docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write comprehensive tests
4. Update documentation for new features
5. Use conventional commit messages
6. Ensure all migrations are tested

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **API Documentation**: Visit `/docs` when server is running
- **Health Check**: `/health` endpoint for service status
- **Logs**: Check container logs for debugging
- **Issues**: Open GitHub issues for bugs/features

## 🔄 API Versioning

Current API version: **v1**
- Base path: `/api/v1`
- All endpoints are versioned for backward compatibility
- Future versions will maintain separate routes