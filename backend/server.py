from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
import uuid
from typing import Optional, List

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# MongoDB connection
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db.users
courses_collection = db.courses
enrollments_collection = db.enrollments
progress_collection = db.progress

app = FastAPI()

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

class CourseCreate(BaseModel):
    title: str
    description: str
    instructor: str
    content: List[dict]
    duration: int
    difficulty: str
    image_url: Optional[str] = None

class EnrollmentCreate(BaseModel):
    course_id: str

class ProgressUpdate(BaseModel):
    course_id: str
    lesson_id: str
    completed: bool = True

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
    # Check if courses already exist
    if courses_collection.count_documents({}) == 0:
        sample_courses = [
            {
                "id": str(uuid.uuid4()),
                "title": "Introduction to Python Programming",
                "description": "Learn the fundamentals of Python programming from scratch. Perfect for beginners who want to start their coding journey.",
                "instructor": "Dr. Sarah Johnson",
                "content": [
                    {"id": "1", "title": "Getting Started with Python", "type": "video", "duration": 15, "url": "https://www.youtube.com/embed/rfscVS0vtbw"},
                    {"id": "2", "title": "Variables and Data Types", "type": "text", "content": "In Python, variables are containers for storing data values. Python has various data types including integers, floats, strings, and booleans."},
                    {"id": "3", "title": "Control Structures", "type": "video", "duration": 20, "url": "https://www.youtube.com/embed/DZwmZ8Usvnk"},
                    {"id": "4", "title": "Functions and Modules", "type": "text", "content": "Functions are reusable blocks of code that perform specific tasks. Modules are files containing Python code that can be imported and used in other programs."}
                ],
                "duration": 120,
                "difficulty": "Beginner",
                "image_url": "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Web Development with React",
                "description": "Master modern web development using React. Build interactive user interfaces and single-page applications.",
                "instructor": "Mike Chen",
                "content": [
                    {"id": "1", "title": "React Fundamentals", "type": "video", "duration": 25, "url": "https://www.youtube.com/embed/Ke90Tje7VS0"},
                    {"id": "2", "title": "Components and Props", "type": "text", "content": "React components are the building blocks of React applications. Props are used to pass data from parent components to child components."},
                    {"id": "3", "title": "State Management", "type": "video", "duration": 30, "url": "https://www.youtube.com/embed/35lXWvCuM8o"},
                    {"id": "4", "title": "React Hooks", "type": "text", "content": "Hooks are functions that let you use state and other React features in functional components. The most commonly used hooks are useState and useEffect."}
                ],
                "duration": 180,
                "difficulty": "Intermediate",
                "image_url": "https://images.unsplash.com/photo-1633356122544-f134324a6cee?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Data Science with Python",
                "description": "Explore data science concepts using Python. Learn pandas, numpy, and matplotlib for data analysis and visualization.",
                "instructor": "Dr. Emily Rodriguez",
                "content": [
                    {"id": "1", "title": "Introduction to Data Science", "type": "video", "duration": 20, "url": "https://www.youtube.com/embed/ua-CiDNNj30"},
                    {"id": "2", "title": "Pandas for Data Manipulation", "type": "text", "content": "Pandas is a powerful Python library for data manipulation and analysis. It provides data structures like DataFrames and Series for working with structured data."},
                    {"id": "3", "title": "Data Visualization", "type": "video", "duration": 25, "url": "https://www.youtube.com/embed/UO98lJQ3QGI"},
                    {"id": "4", "title": "Statistical Analysis", "type": "text", "content": "Statistical analysis involves collecting, organizing, analyzing, and interpreting data to discover patterns and trends."}
                ],
                "duration": 240,
                "difficulty": "Advanced",
                "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
                "created_at": datetime.utcnow()
            }
        ]
        courses_collection.insert_many(sample_courses)

# Initialize data on startup
initialize_sample_data()

# Routes
@app.get("/")
async def root():
    return {"message": "E-Learning Platform API"}

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

@app.get("/api/courses")
async def get_courses():
    courses = list(courses_collection.find({}, {"_id": 0}))
    return courses

@app.get("/api/courses/{course_id}")
async def get_course(course_id: str):
    course = courses_collection.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@app.post("/api/enrollments")
async def enroll_in_course(enrollment_data: EnrollmentCreate, current_user: dict = Depends(get_current_user)):
    # Check if course exists
    course = courses_collection.find_one({"id": enrollment_data.course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing_enrollment = enrollments_collection.find_one({
        "user_id": current_user["id"],
        "course_id": enrollment_data.course_id
    })
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
    
    # Create enrollment
    enrollment = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "course_id": enrollment_data.course_id,
        "enrolled_at": datetime.utcnow(),
        "progress": 0,
        "completed": False
    }
    
    enrollments_collection.insert_one(enrollment)
    
    return {"message": "Successfully enrolled in course"}

@app.get("/api/enrollments/user/{user_id}")
async def get_user_enrollments(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    enrollments = list(enrollments_collection.find({"user_id": user_id}, {"_id": 0}))
    
    # Get course details for each enrollment
    for enrollment in enrollments:
        course = courses_collection.find_one({"id": enrollment["course_id"]}, {"_id": 0})
        enrollment["course"] = course
    
    return enrollments

@app.post("/api/progress")
async def update_progress(progress_data: ProgressUpdate, current_user: dict = Depends(get_current_user)):
    # Check if user is enrolled in the course
    enrollment = enrollments_collection.find_one({
        "user_id": current_user["id"],
        "course_id": progress_data.course_id
    })
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")
    
    # Update or create progress record
    progress_record = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "course_id": progress_data.course_id,
        "lesson_id": progress_data.lesson_id,
        "completed": progress_data.completed,
        "completed_at": datetime.utcnow()
    }
    
    # Check if progress already exists for this lesson
    existing_progress = progress_collection.find_one({
        "user_id": current_user["id"],
        "course_id": progress_data.course_id,
        "lesson_id": progress_data.lesson_id
    })
    
    if existing_progress:
        progress_collection.update_one(
            {"id": existing_progress["id"]},
            {"$set": {"completed": progress_data.completed, "completed_at": datetime.utcnow()}}
        )
    else:
        progress_collection.insert_one(progress_record)
    
    # Update overall course progress
    course = courses_collection.find_one({"id": progress_data.course_id})
    total_lessons = len(course["content"])
    completed_lessons = progress_collection.count_documents({
        "user_id": current_user["id"],
        "course_id": progress_data.course_id,
        "completed": True
    })
    
    progress_percentage = (completed_lessons / total_lessons) * 100
    
    enrollments_collection.update_one(
        {"user_id": current_user["id"], "course_id": progress_data.course_id},
        {"$set": {"progress": progress_percentage, "completed": progress_percentage == 100}}
    )
    
    return {"message": "Progress updated successfully", "progress": progress_percentage}

@app.get("/api/progress/user/{user_id}/course/{course_id}")
async def get_user_course_progress(user_id: str, course_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    progress_records = list(progress_collection.find({
        "user_id": user_id,
        "course_id": course_id
    }, {"_id": 0}))
    
    return progress_records

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)