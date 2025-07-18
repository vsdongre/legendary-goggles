from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
import uuid
from typing import Optional, List
import json

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# MongoDB connection
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db.users
classes_collection = db.classes
subjects_collection = db.subjects
chapters_collection = db.chapters
content_collection = db.content

app = FastAPI()

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Mount static files for uploaded content
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models
class UserSignup(BaseModel):
    username: str
    email: str
    password: str
    role: str = "student"

class UserLogin(BaseModel):
    email: str
    password: str

class ClassCreate(BaseModel):
    name: str
    description: str
    grade_level: int

class SubjectCreate(BaseModel):
    name: str
    description: str
    class_id: str

class ChapterCreate(BaseModel):
    name: str
    description: str
    subject_id: str
    content: Optional[str] = ""

class ContentUpload(BaseModel):
    chapter_id: str
    title: str
    content_type: str  # "text", "video", "document", "image"
    content_data: str

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = users_collection.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Initialize sample data
def initialize_sample_data():
    # Check if classes already exist
    if classes_collection.count_documents({}) == 0:
        # Create sample classes
        classes_data = [
            {
                "id": str(uuid.uuid4()),
                "name": "Class 1",
                "description": "First Grade",
                "grade_level": 1,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Class 2",
                "description": "Second Grade",
                "grade_level": 2,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Class 3",
                "description": "Third Grade",
                "grade_level": 3,
                "created_at": datetime.utcnow()
            }
        ]
        classes_collection.insert_many(classes_data)
        
        # Create sample subjects
        class_1_id = classes_data[0]["id"]
        class_2_id = classes_data[1]["id"]
        
        subjects_data = [
            {
                "id": str(uuid.uuid4()),
                "name": "Mathematics",
                "description": "Basic Math Concepts",
                "class_id": class_1_id,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "English",
                "description": "Language and Literature",
                "class_id": class_1_id,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Science",
                "description": "Basic Science Concepts",
                "class_id": class_1_id,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Mathematics",
                "description": "Intermediate Math",
                "class_id": class_2_id,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "English",
                "description": "Advanced Language Skills",
                "class_id": class_2_id,
                "created_at": datetime.utcnow()
            }
        ]
        subjects_collection.insert_many(subjects_data)
        
        # Create sample chapters
        math_subject_id = subjects_data[0]["id"]
        english_subject_id = subjects_data[1]["id"]
        
        chapters_data = [
            {
                "id": str(uuid.uuid4()),
                "name": "Numbers and Counting",
                "description": "Learn to count and understand numbers",
                "subject_id": math_subject_id,
                "content": "This chapter introduces basic counting and number recognition. Students will learn to count from 1 to 100 and understand the concept of numbers.",
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Addition and Subtraction",
                "description": "Basic arithmetic operations",
                "subject_id": math_subject_id,
                "content": "In this chapter, students will learn how to add and subtract numbers. We will start with single-digit numbers and progress to double-digit numbers.",
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Alphabets and Phonics",
                "description": "Learn letters and sounds",
                "subject_id": english_subject_id,
                "content": "This chapter focuses on learning the English alphabet and understanding the sounds each letter makes. Students will practice writing letters and identifying sounds.",
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Simple Words and Sentences",
                "description": "Building vocabulary and sentences",
                "subject_id": english_subject_id,
                "content": "Students will learn to form simple words and construct basic sentences. This chapter builds on the phonics foundation to create meaningful communication.",
                "created_at": datetime.utcnow()
            }
        ]
        chapters_collection.insert_many(chapters_data)

# Initialize data on startup
initialize_sample_data()

# Routes
@app.get("/")
async def root():
    return {"message": "E-Learning Platform API - Class/Subject/Chapter Structure"}

@app.post("/api/auth/signup")
async def signup(user_data: UserSignup):
    # Check if user already exists
    existing_user = users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_id = str(uuid.uuid4())
    
    user = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hashed_password,
        "role": user_data.role,
        "created_at": datetime.utcnow()
    }
    
    users_collection.insert_one(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "role": user_data.role
        }
    }

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    user = users_collection.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.get("/api/auth/user")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"]
    }

@app.get("/api/classes")
async def get_classes():
    classes = list(classes_collection.find({}, {"_id": 0}))
    return classes

@app.get("/api/subjects/{class_id}")
async def get_subjects_by_class(class_id: str):
    subjects = list(subjects_collection.find({"class_id": class_id}, {"_id": 0}))
    return subjects

@app.get("/api/chapters/{subject_id}")
async def get_chapters_by_subject(subject_id: str):
    chapters = list(chapters_collection.find({"subject_id": subject_id}, {"_id": 0}))
    return chapters

@app.get("/api/chapter/{chapter_id}")
async def get_chapter_details(chapter_id: str):
    chapter = chapters_collection.find_one({"id": chapter_id}, {"_id": 0})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Get subject and class info
    subject = subjects_collection.find_one({"id": chapter["subject_id"]}, {"_id": 0})
    class_info = classes_collection.find_one({"id": subject["class_id"]}, {"_id": 0})
    
    # Get content for this chapter
    content = list(content_collection.find({"chapter_id": chapter_id}, {"_id": 0}))
    
    return {
        "chapter": chapter,
        "subject": subject,
        "class": class_info,
        "content": content
    }

@app.post("/api/content/upload")
async def upload_content(content_data: ContentUpload, current_user: dict = Depends(get_current_user)):
    # Check if chapter exists
    chapter = chapters_collection.find_one({"id": content_data.chapter_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Create content record
    content_record = {
        "id": str(uuid.uuid4()),
        "chapter_id": content_data.chapter_id,
        "title": content_data.title,
        "content_type": content_data.content_type,
        "content_data": content_data.content_data,
        "uploaded_by": current_user["id"],
        "created_at": datetime.utcnow()
    }
    
    content_collection.insert_one(content_record)
    
    return {"message": "Content uploaded successfully", "content_id": content_record["id"]}

@app.post("/api/content/upload-file")
async def upload_file(
    chapter_id: str,
    title: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Check if chapter exists
    chapter = chapters_collection.find_one({"id": chapter_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Create unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"uploads/{unique_filename}"
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Determine content type based on file extension
    content_type = "document"
    if file_extension.lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        content_type = "image"
    elif file_extension.lower() in ['mp4', 'avi', 'mov', 'wmv']:
        content_type = "video"
    elif file_extension.lower() in ['pdf', 'doc', 'docx', 'txt']:
        content_type = "document"
    
    # Create content record
    content_record = {
        "id": str(uuid.uuid4()),
        "chapter_id": chapter_id,
        "title": title,
        "content_type": content_type,
        "content_data": file_path,
        "filename": file.filename,
        "uploaded_by": current_user["id"],
        "created_at": datetime.utcnow()
    }
    
    content_collection.insert_one(content_record)
    
    return {"message": "File uploaded successfully", "content_id": content_record["id"]}

@app.get("/api/content/{chapter_id}")
async def get_chapter_content(chapter_id: str):
    content = list(content_collection.find({"chapter_id": chapter_id}, {"_id": 0}))
    return content

# Admin routes (for adding new classes, subjects, chapters)
@app.post("/api/admin/class")
async def create_class(class_data: ClassCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    class_record = {
        "id": str(uuid.uuid4()),
        "name": class_data.name,
        "description": class_data.description,
        "grade_level": class_data.grade_level,
        "created_at": datetime.utcnow()
    }
    
    classes_collection.insert_one(class_record)
    
    return {"message": "Class created successfully", "class_id": class_record["id"]}

@app.post("/api/admin/subject")
async def create_subject(subject_data: SubjectCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    subject_record = {
        "id": str(uuid.uuid4()),
        "name": subject_data.name,
        "description": subject_data.description,
        "class_id": subject_data.class_id,
        "created_at": datetime.utcnow()
    }
    
    subjects_collection.insert_one(subject_record)
    
    return {"message": "Subject created successfully", "subject_id": subject_record["id"]}

@app.post("/api/admin/chapter")
async def create_chapter(chapter_data: ChapterCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    chapter_record = {
        "id": str(uuid.uuid4()),
        "name": chapter_data.name,
        "description": chapter_data.description,
        "subject_id": chapter_data.subject_id,
        "content": chapter_data.content,
        "created_at": datetime.utcnow()
    }
    
    chapters_collection.insert_one(chapter_record)
    
    return {"message": "Chapter created successfully", "chapter_id": chapter_record["id"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)