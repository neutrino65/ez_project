# Secure File Sharing System

A robust Django-based file sharing platform that enables secure document exchange between operations teams and clients. Built with Django REST Framework, it features encrypted download links, user role management, and email verification.

## What This System Does

**For Operations Teams:**
- Upload business documents (PowerPoint, Word, Excel files)
- Manage file access and distribution

**For Clients:**
- Register and verify email addresses
- Browse available documents
- Download files through secure, time-limited links

## Security Features

- **Encrypted Download URLs**: Each download link is cryptographically signed and expires after 10 minutes
- **Role-Based Access**: Operations users can upload, clients can download
- **Email Verification**: Clients must verify their email before accessing files
- **File Type Validation**: Only business documents (pptx, docx, xlsx) are allowed
- **Token Authentication**: Secure API access using Django tokens

## API Endpoints

### Operations User APIs

#### Login
```bash
POST /api/ops/login/
Content-Type: application/json

{
    "username": "ops_user",
    "password": "your_password"
}
```

#### Upload File
```bash
POST /api/ops/upload/
Authorization: Token your_token_here
Content-Type: multipart/form-data

file: [your_pptx_docx_or_xlsx_file]
```

### Client User APIs

#### Sign Up
```bash
POST /api/client/signup/
Content-Type: application/json

{
    "username": "client_user",
    "email": "client@company.com",
    "password": "secure_password",
    "user_type": "client"
}
```

#### Email Verification
```bash
GET /api/client/verify/{encrypted_token}/
```

#### Login
```bash
POST /api/client/login/
Content-Type: application/json

{
    "username": "client_user",
    "password": "secure_password"
}
```

#### List Available Files
```bash
GET /api/client/files/
Authorization: Token your_token_here
```

#### Get Download Link
```bash
GET /api/client/download-link/{file_id}/
Authorization: Token your_token_here
```

#### Download File
```bash
GET /api/client/download/{encrypted_token}/
Authorization: Token your_token_here
```

## 🛠️ Quick Setup

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone and navigate to project**
```bash
git clone <repository-url>
cd ez_project
```

2. **Set up virtual environment**
```bash
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up database**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create admin user**
```bash
python manage.py createsuperuser
```

6. **Start the server**
```bash
python manage.py runserver
```

Visit `http://localhost:8000/admin/` to manage users and files.

## 📖 Usage Examples

### Complete Workflow

1. **Admin creates an Operations user** (via Django admin)

2. **Ops user uploads a document:**
```bash
# Login first
curl -X POST http://localhost:8000/api/ops/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "ops_user", "password": "password123"}'

# Upload file using the returned token
curl -X POST http://localhost:8000/api/ops/upload/ \
  -H "Authorization: Token abc123..." \
  -F "file=@presentation.pptx"
```

3. **Client registers:**
```bash
curl -X POST http://localhost:8000/api/client/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@client.com",
    "password": "secure123",
    "user_type": "client"
  }'
```

4. **Client verifies email** (click link from console output)

5. **Client logs in and downloads:**
```bash
# Login
curl -X POST http://localhost:8000/api/client/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "password": "secure123"}'

# List files
curl -X GET http://localhost:8000/api/client/files/ \
  -H "Authorization: Token xyz789..."

# Get download link
curl -X GET http://localhost:8000/api/client/download-link/1/ \
  -H "Authorization: Token xyz789..."

# Download file
curl -X GET "http://localhost:8000/api/client/download/encrypted_token_here" \
  -H "Authorization: Token xyz789..." \
  --output downloaded_file.pptx
```

## 🔧 Configuration

### Environment Variables
```bash
SECRET_KEY=your_django_secret_key
DEBUG=True  # Set to False in production
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### File Upload Settings
- **Max size**: 50MB per file
- **Allowed formats**: .pptx, .docx, .xlsx
- **Storage**: Local filesystem (configurable for cloud)

## 🚨 Important Notes

### Security
- Download links expire after 10 minutes
- Only the requesting client can use their download link
- Email verification is required for client access
- File uploads are restricted to operations users only

### Development vs Production
- **Development**: Emails print to console
- **Production**: Configure SMTP email backend
- **Production**: Use HTTPS for all API calls

### File Management
- Files are stored in `media/user_<id>/` directories
- Original filenames are preserved
- File metadata includes uploader and timestamp
