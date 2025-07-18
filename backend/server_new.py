from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import jwt
import bcrypt
import os
import uuid
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient
import mimetypes
import subprocess
from pathlib import Path

# Connect to MongoDB
client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client.test_database

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-here"

# Create required directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/documents", exist_ok=True)

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "student"

class UserLogin(BaseModel):
    email: str
    password: str

class ClassCreate(BaseModel):
    name: str
    description: str
    grade: str

class SubjectCreate(BaseModel):
    name: str
    description: str
    class_id: str

class ChapterCreate(BaseModel):
    name: str
    description: str
    subject_id: str

class ContentCreate(BaseModel):
    title: str
    content_type: str  # 'document', 'spreadsheet', 'presentation', 'pdf', 'webpage', 'image', 'video', 'text'
    file_path: str     # LAN file path or URL
    description: Optional[str] = ""
    chapter_id: str

class ProgressUpdate(BaseModel):
    chapter_id: str
    completed: bool

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def get_file_type(file_path: str) -> str:
    """Determine file type based on extension"""
    file_path = file_path.lower()
    
    # Document formats
    if file_path.endswith(('.doc', '.docx')):
        return 'document'
    elif file_path.endswith(('.xls', '.xlsx', '.csv')):
        return 'spreadsheet'
    elif file_path.endswith(('.ppt', '.pptx')):
        return 'presentation'
    elif file_path.endswith('.pdf'):
        return 'pdf'
    elif file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg')):
        return 'image'
    elif file_path.endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm')):
        return 'video'
    elif file_path.endswith(('.mp3', '.wav', '.ogg', '.flac')):
        return 'audio'
    elif file_path.endswith(('.htm', '.html')):
        return 'webpage'
    elif file_path.endswith('.txt'):
        return 'text'
    else:
        return 'file'

def is_valid_path(file_path: str) -> bool:
    """Check if file path is valid (exists on LAN or is URL)"""
    if file_path.startswith(('http://', 'https://')):
        return True  # URL - assume valid
    
    # Check if file exists on local network
    try:
        return os.path.exists(file_path) or Path(file_path).is_file()
    except:
        return False

# Authentication endpoints
@app.post("/api/auth/signup")
async def signup(user: UserCreate):
    # Check if user already exists
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "email": user.email,
        "password": hashed_password.decode('utf-8'),
        "role": user.role,
        "created_at": datetime.utcnow()
    }
    
    db.users.insert_one(user_data)
    
    # Create access token
    access_token = create_access_token({"user_id": user_id, "email": user.email})
    
    return {"access_token": access_token, "user": {"id": user_id, "email": user.email, "role": user.role}}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    # Find user
    db_user = db.users.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user["password"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token({"user_id": db_user["id"], "email": db_user["email"]})
    
    return {"access_token": access_token, "user": {"id": db_user["id"], "email": db_user["email"], "role": db_user["role"]}}

# Classes endpoints
@app.post("/api/classes/create")
async def create_class(class_data: ClassCreate, user_id: str = Depends(verify_token)):
    class_id = str(uuid.uuid4())
    class_doc = {
        "id": class_id,
        "name": class_data.name,
        "description": class_data.description,
        "grade": class_data.grade,
        "created_by": user_id,
        "created_at": datetime.utcnow()
    }
    
    db.classes.insert_one(class_doc)
    return {"class_id": class_id, "message": "Class created successfully"}

@app.get("/api/classes")
async def get_classes(user_id: str = Depends(verify_token)):
    classes = list(db.classes.find({}, {"_id": 0}))
    return classes

# Subjects endpoints
@app.post("/api/subjects/create")
async def create_subject(subject_data: SubjectCreate, user_id: str = Depends(verify_token)):
    subject_id = str(uuid.uuid4())
    subject_doc = {
        "id": subject_id,
        "name": subject_data.name,
        "description": subject_data.description,
        "class_id": subject_data.class_id,
        "created_by": user_id,
        "created_at": datetime.utcnow()
    }
    
    db.subjects.insert_one(subject_doc)
    return {"subject_id": subject_id, "message": "Subject created successfully"}

@app.get("/api/subjects/{class_id}")
async def get_subjects(class_id: str, user_id: str = Depends(verify_token)):
    subjects = list(db.subjects.find({"class_id": class_id}, {"_id": 0}))
    return subjects

# Chapters endpoints
@app.post("/api/chapters/create")
async def create_chapter(chapter_data: ChapterCreate, user_id: str = Depends(verify_token)):
    chapter_id = str(uuid.uuid4())
    chapter_doc = {
        "id": chapter_id,
        "name": chapter_data.name,
        "description": chapter_data.description,
        "subject_id": chapter_data.subject_id,
        "created_by": user_id,
        "created_at": datetime.utcnow()
    }
    
    db.chapters.insert_one(chapter_doc)
    return {"chapter_id": chapter_id, "message": "Chapter created successfully"}

@app.get("/api/chapters/{subject_id}")
async def get_chapters(subject_id: str, user_id: str = Depends(verify_token)):
    chapters = list(db.chapters.find({"subject_id": subject_id}, {"_id": 0}))
    return chapters

@app.get("/api/chapter/{chapter_id}")
async def get_chapter_details(chapter_id: str, user_id: str = Depends(verify_token)):
    chapter = db.chapters.find_one({"id": chapter_id}, {"_id": 0})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Get subject and class info
    subject = db.subjects.find_one({"id": chapter["subject_id"]}, {"_id": 0})
    class_info = db.classes.find_one({"id": subject["class_id"]}, {"_id": 0}) if subject else None
    
    return {
        "chapter": chapter,
        "subject": subject,
        "class": class_info
    }

# Content endpoints
@app.post("/api/content/create")
async def create_content(content_data: ContentCreate, user_id: str = Depends(verify_token)):
    # Validate file path
    if not is_valid_path(content_data.file_path):
        raise HTTPException(status_code=400, detail="Invalid file path or file does not exist")
    
    # Auto-detect content type if not specified
    if content_data.content_type == "auto":
        content_data.content_type = get_file_type(content_data.file_path)
    
    content_id = str(uuid.uuid4())
    content_doc = {
        "id": content_id,
        "title": content_data.title,
        "content_type": content_data.content_type,
        "file_path": content_data.file_path,
        "description": content_data.description,
        "chapter_id": content_data.chapter_id,
        "created_by": user_id,
        "created_at": datetime.utcnow()
    }
    
    db.content.insert_one(content_doc)
    return {"content_id": content_id, "message": "Content created successfully"}

@app.get("/api/content/{chapter_id}")
async def get_content(chapter_id: str, user_id: str = Depends(verify_token)):
    content = list(db.content.find({"chapter_id": chapter_id}, {"_id": 0}))
    return content

@app.get("/api/content/open/{content_id}")
async def open_content(content_id: str, user_id: str = Depends(verify_token)):
    """Open content file using system default application"""
    content = db.content.find_one({"id": content_id}, {"_id": 0})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    file_path = content["file_path"]
    
    # If it's a URL, return the URL
    if file_path.startswith(('http://', 'https://')):
        return {"type": "url", "path": file_path}
    
    # If it's a local file, check if it exists
    if not is_valid_path(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return file info for client to handle
    return {
        "type": "file",
        "path": file_path,
        "content_type": content["content_type"],
        "title": content["title"]
    }

# Progress tracking endpoints
@app.post("/api/progress/update")
async def update_progress(progress_data: ProgressUpdate, user_id: str = Depends(verify_token)):
    progress_doc = {
        "user_id": user_id,
        "chapter_id": progress_data.chapter_id,
        "completed": progress_data.completed,
        "updated_at": datetime.utcnow()
    }
    
    # Update or insert progress
    db.progress.update_one(
        {"user_id": user_id, "chapter_id": progress_data.chapter_id},
        {"$set": progress_doc},
        upsert=True
    )
    
    return {"message": "Progress updated successfully"}

@app.get("/api/progress/{user_id}")
async def get_progress(user_id: str, current_user_id: str = Depends(verify_token)):
    progress = list(db.progress.find({"user_id": user_id}, {"_id": 0}))
    return progress

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)