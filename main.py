from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
import boto3
from google.cloud import storage as gcs
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
import os
import io
from typing import Optional
from pydantic import BaseModel
from botocore.exceptions import ClientError, NoCredentialsError

app = FastAPI(title="Cloud File Upload API", version="1.0.0")

# Configuration models
class CloudConfig:
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    
    # Google Cloud Storage Configuration
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Google Drive Configuration
    GOOGLE_DRIVE_CREDENTIALS_FILE = os.getenv("GOOGLE_DRIVE_CREDENTIALS_FILE")
    GOOGLE_DRIVE_TOKEN_FILE = os.getenv("GOOGLE_DRIVE_TOKEN_FILE", "token.json")
    GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")  # Optional: specific folder ID

# Response models
class UploadResponse(BaseModel):
    success: bool
    message: str
    file_url: Optional[str] = None
    file_id: Optional[str] = None

# AWS S3 Client
def get_s3_client():
    try:
        return boto3.client(
            's3',
            aws_access_key_id=CloudConfig.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=CloudConfig.AWS_SECRET_ACCESS_KEY,
            region_name=CloudConfig.AWS_REGION
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize S3 client: {str(e)}")

# Google Cloud Storage Client
def get_gcs_client():
    try:
        if CloudConfig.GOOGLE_APPLICATION_CREDENTIALS:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CloudConfig.GOOGLE_APPLICATION_CREDENTIALS
        return gcs.Client()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize GCS client: {str(e)}")

# Google Drive Client
def get_drive_service():
    try:
        creds = None
        token_path = "cred/drive/token.json"
        creds_file = "cred/drive/credentials.json"
        scopes = ["https://www.googleapis.com/auth/drive.file"]

        # Load existing token
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, scopes)

        # If there are no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Google Drive authentication required. Please run google_auth_flow.py to authenticate."
                )

        return build('drive', 'v3', credentials=creds)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Drive service: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Cloud File Upload API", "endpoints": ["/upload/s3", "/upload/gcs", "/upload/drive"]}

@app.post("/upload/s3", response_model=UploadResponse)
async def upload_to_s3(file: UploadFile = File(...)):
    """Upload file to AWS S3"""
    if not CloudConfig.S3_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="S3 bucket name not configured")
    
    try:
        s3_client = get_s3_client()
        
        # Read file content
        file_content = await file.read()
        
        # Upload to S3
        s3_client.put_object(
            Bucket=CloudConfig.S3_BUCKET_NAME,
            Key=file.filename,
            Body=file_content,
            ContentType=file.content_type
        )
        
        # Generate file URL
        file_url = f"https://{CloudConfig.S3_BUCKET_NAME}.s3.{CloudConfig.AWS_REGION}.amazonaws.com/{file.filename}"
        
        return UploadResponse(
            success=True,
            message=f"File '{file.filename}' uploaded successfully to S3",
            file_url=file_url
        )
    
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/upload/gcs", response_model=UploadResponse)
async def upload_to_gcs(file: UploadFile = File(...)):
    """Upload file to Google Cloud Storage"""
    if not CloudConfig.GCS_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="GCS bucket name not configured")
    
    try:
        client = get_gcs_client()
        bucket = client.bucket(CloudConfig.GCS_BUCKET_NAME)
        blob = bucket.blob(file.filename)
        
        # Read file content
        file_content = await file.read()
        
        # Upload to GCS
        blob.upload_from_string(
            file_content,
            content_type=file.content_type
        )
        
        # Make blob publicly readable (optional)
        # blob.make_public()
        
        file_url = f"https://storage.googleapis.com/{CloudConfig.GCS_BUCKET_NAME}/{file.filename}"
        
        return UploadResponse(
            success=True,
            message=f"File '{file.filename}' uploaded successfully to GCS",
            file_url=file_url
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS upload failed: {str(e)}")

@app.post("/upload/drive", response_model=UploadResponse)
async def upload_to_drive(file: UploadFile = File(...)):
    """Upload file to Google Drive"""
    try:
        service = get_drive_service()
        
        # Read file content
        file_content = await file.read()
        media = MediaIoBaseUpload(
            io.BytesIO(file_content),
            mimetype=file.content_type,
            resumable=True
        )
        
        # File metadata
        file_metadata = {
            'name': file.filename
        }
        
        # Add to specific folder if configured
        if CloudConfig.GOOGLE_DRIVE_FOLDER_ID:
            file_metadata['parents'] = [CloudConfig.GOOGLE_DRIVE_FOLDER_ID]
        
        # Upload to Drive
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webViewLink,webContentLink'
        ).execute()
        
        return UploadResponse(
            success=True,
            message=f"File '{file.filename}' uploaded successfully to Google Drive",
            file_url=uploaded_file.get('webViewLink'),
            file_id=uploaded_file.get('id')
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive upload failed: {str(e)}")

@app.post("/upload/all")
async def upload_to_all_services(file: UploadFile = File(...)):
    """Upload file to all configured cloud services"""
    results = {}
    
    # Try S3
    if CloudConfig.S3_BUCKET_NAME and CloudConfig.AWS_ACCESS_KEY_ID:
        try:
            # Reset file pointer
            await file.seek(0)
            s3_result = await upload_to_s3(file)
            results['s3'] = s3_result.dict()
        except Exception as e:
            results['s3'] = {"success": False, "message": str(e)}
    
    # Try GCS
    if CloudConfig.GCS_BUCKET_NAME:
        try:
            await file.seek(0)
            gcs_result = await upload_to_gcs(file)
            results['gcs'] = gcs_result.dict()
        except Exception as e:
            results['gcs'] = {"success": False, "message": str(e)}
    
    # Try Google Drive
    if CloudConfig.GOOGLE_DRIVE_CREDENTIALS_FILE:
        try:
            await file.seek(0)
            drive_result = await upload_to_drive(file)
            results['drive'] = drive_result.dict()
        except Exception as e:
            results['drive'] = {"success": False, "message": str(e)}
    
    return {"results": results}


@app.get("/list/s3")
async def list_s3_files():
    """List files in AWS S3 bucket"""
    if not CloudConfig.S3_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="S3 bucket name not configured")
    try:
        s3_client = get_s3_client()
        response = s3_client.list_objects_v2(Bucket=CloudConfig.S3_BUCKET_NAME)
        files = []
        for obj in response.get('Contents', []):
            files.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat()
            })
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list S3 files: {str(e)}")

@app.get("/list/gcs")
async def list_gcs_files():
    """List files in Google Cloud Storage bucket"""
    if not CloudConfig.GCS_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="GCS bucket name not configured")
    try:
        client = get_gcs_client()
        bucket = client.bucket(CloudConfig.GCS_BUCKET_NAME)
        blobs = bucket.list_blobs()
        files = []
        for blob in blobs:
            files.append({
                "name": blob.name,
                "size": blob.size,
                "updated": blob.updated.isoformat() if blob.updated else None
            })
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list GCS files: {str(e)}")

@app.get("/list/drive")
async def list_drive_files():
    """List files in Google Drive (folder if configured)"""
    try:
        service = get_drive_service()
        query = None
        if CloudConfig.GOOGLE_DRIVE_FOLDER_ID:
            query = f"'{CloudConfig.GOOGLE_DRIVE_FOLDER_ID}' in parents"
        results = service.files().list(
            q=query,
            pageSize=20,
            fields="files(id, name, mimeType, modifiedTime, size, webViewLink)"
        ).execute()
        files = results.get("files", [])
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list Drive files: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "services": {
        "s3_configured": bool(CloudConfig.S3_BUCKET_NAME and CloudConfig.AWS_ACCESS_KEY_ID),
        "gcs_configured": bool(CloudConfig.GCS_BUCKET_NAME),
        "drive_configured": bool(CloudConfig.GOOGLE_DRIVE_CREDENTIALS_FILE)
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)