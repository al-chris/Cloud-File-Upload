# Cloud File Upload API - Setup Instructions

## Requirements

Create a `requirements.txt` file:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
boto3==1.34.0
google-cloud-storage==2.10.0
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
python-multipart==0.0.6
pydantic==2.5.0
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name

# Google Cloud Storage Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/gcs-service-account.json
GCS_BUCKET_NAME=your-gcs-bucket-name

# Google Drive Configuration
GOOGLE_DRIVE_CREDENTIALS_FILE=/path/to/your/drive-credentials.json
GOOGLE_DRIVE_TOKEN_FILE=token.json
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id  # Optional
```

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. AWS S3 Setup

1. Create an AWS account and S3 bucket
2. Create IAM user with S3 permissions
3. Get access key ID and secret access key
4. Set environment variables

### 3. Google Cloud Storage Setup

1. Create a Google Cloud Project
2. Enable Cloud Storage API
3. Create a service account
4. Download the service account JSON key
5. Set `GOOGLE_APPLICATION_CREDENTIALS` to the JSON file path

### 4. Google Drive Setup

1. Go to Google Cloud Console
2. Enable Google Drive API
3. Create OAuth 2.0 credentials (Desktop application)
4. Download the credentials JSON file
5. Set `GOOGLE_DRIVE_CREDENTIALS_FILE` to the JSON file path

**Note**: For Google Drive, you'll need to run the authentication flow once. The first time you use the Drive endpoint, you may need to authenticate manually.

### 5. Run the Application

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - API information
- `POST /upload/s3` - Upload to AWS S3
- `POST /upload/gcs` - Upload to Google Cloud Storage
- `POST /upload/drive` - Upload to Google Drive
- `POST /upload/all` - Upload to all configured services
- `GET /health` - Check service configuration status

## Usage Examples

### Upload to S3
```bash
curl -X POST "http://localhost:8000/upload/s3" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your-file.pdf"
```

### Upload to Google Cloud Storage
```bash
curl -X POST "http://localhost:8000/upload/gcs" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your-file.pdf"
```

### Upload to Google Drive
```bash
curl -X POST "http://localhost:8000/upload/drive" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your-file.pdf"
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Security Notes

- Store credentials securely using environment variables
- Use IAM roles with minimal required permissions
- Consider implementing authentication for your API endpoints
- For production, use proper secret management services
- Enable CORS if needed for web frontend integration

## Troubleshooting

1. **AWS Credentials Error**: Ensure AWS credentials are properly set and have S3 permissions
2. **GCS Authentication Error**: Verify service account JSON file path and permissions
3. **Google Drive Auth Error**: Complete OAuth flow for first-time setup
4. **File Upload Error**: Check file size limits and bucket permissions

## Resourses
- https://developers.google.com/workspace/drive/api/quickstart/python

## Optional Enhancements

You can extend this API with:
- File size validation
- File type restrictions
- Progress tracking for large files
- File metadata storage
- Batch upload capabilities
- Authentication middleware
- Rate limiting
- Logging and monitoring