from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
import uuid
from typing import Optional, List
import json
import shutil

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
assignments_collection = db.assignments
quizzes_collection = db.quizzes
progress_collection = db.progress

app = FastAPI()

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/documents", exist_ok=True)

# Custom endpoint to serve video files with proper content-type
@app.get("/api/media/{file_path:path}")
@app.head("/api/media/{file_path:path}")
async def serve_media_file(file_path: str):
    from fastapi.responses import FileResponse
    import mimetypes
    
    # Remove 'uploads/' prefix if present since we're serving from uploads directory
    if file_path.startswith('uploads/'):
        file_path = file_path[8:]
    
    file_full_path = f"uploads/{file_path}"
    
    # Check if file exists
    if not os.path.exists(file_full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(file_full_path)
    if mime_type is None:
        if file_path.endswith('.mp4'):
            mime_type = 'video/mp4'
        elif file_path.endswith('.avi'):
            mime_type = 'video/x-msvideo'
        elif file_path.endswith('.mov'):
            mime_type = 'video/quicktime'
        elif file_path.endswith('.webm'):
            mime_type = 'video/webm'
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif file_path.endswith('.png'):
            mime_type = 'image/png'
        elif file_path.endswith('.pdf'):
            mime_type = 'application/pdf'
        else:
            mime_type = 'application/octet-stream'
    
    return FileResponse(
        file_full_path,
        media_type=mime_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Cache-Control": "public, max-age=3600",
        }
    )

# Keep the original uploads endpoint for backward compatibility
@app.get("/uploads/{file_path:path}")
@app.head("/uploads/{file_path:path}")
async def serve_uploaded_file(file_path: str):
    from fastapi.responses import FileResponse
    import mimetypes
    
    file_full_path = f"uploads/{file_path}"
    
    # Check if file exists
    if not os.path.exists(file_full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(file_full_path)
    if mime_type is None:
        if file_path.endswith('.mp4'):
            mime_type = 'video/mp4'
        elif file_path.endswith('.avi'):
            mime_type = 'video/x-msvideo'
        elif file_path.endswith('.mov'):
            mime_type = 'video/quicktime'
        elif file_path.endswith('.webm'):
            mime_type = 'video/webm'
        else:
            mime_type = 'application/octet-stream'
    
    return FileResponse(
        file_full_path,
        media_type=mime_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

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

class AssignmentCreate(BaseModel):
    title: str
    description: str
    chapter_id: str
    due_date: Optional[str] = None
    points: int = 100

class QuizCreate(BaseModel):
    title: str
    description: str
    chapter_id: str
    questions: List[dict]
    time_limit: int = 30  # minutes

class ProgressUpdate(BaseModel):
    chapter_id: str
    completed: bool = True
    score: Optional[int] = None

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

# Initialize comprehensive sample data
def initialize_sample_data():
    # Create admin user if doesn't exist
    admin_user = users_collection.find_one({"email": "admin@example.com"})
    if not admin_user:
        admin_user = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@example.com",
            "password_hash": hash_password("Admin123!"),
            "role": "admin",
            "created_at": datetime.utcnow()
        }
        users_collection.insert_one(admin_user)
    
    # Check if classes already exist
    if classes_collection.count_documents({}) == 0:
        # Create comprehensive classes
        classes_data = [
            {
                "id": str(uuid.uuid4()),
                "name": "Class 1",
                "description": "First Grade - Foundation Learning",
                "grade_level": 1,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Class 2",
                "description": "Second Grade - Building Skills",
                "grade_level": 2,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Class 3",
                "description": "Third Grade - Advanced Learning",
                "grade_level": 3,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Class 4",
                "description": "Fourth Grade - Intermediate Level",
                "grade_level": 4,
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Class 5",
                "description": "Fifth Grade - Advanced Concepts",
                "grade_level": 5,
                "created_at": datetime.utcnow()
            }
        ]
        classes_collection.insert_many(classes_data)
        
        # Create comprehensive subjects
        subjects_data = []
        for class_data in classes_data:
            class_id = class_data["id"]
            # Common subjects for all classes
            subjects_data.extend([
                {
                    "id": str(uuid.uuid4()),
                    "name": "Mathematics",
                    "description": f"Math concepts for {class_data['name']}",
                    "class_id": class_id,
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "English",
                    "description": f"Language and Literature for {class_data['name']}",
                    "class_id": class_id,
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Science",
                    "description": f"Science concepts for {class_data['name']}",
                    "class_id": class_id,
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Social Studies",
                    "description": f"History and Geography for {class_data['name']}",
                    "class_id": class_id,
                    "created_at": datetime.utcnow()
                }
            ])
        
        subjects_collection.insert_many(subjects_data)
        
        # Create comprehensive chapters
        chapters_data = []
        for subject in subjects_data:
            subject_id = subject["id"]
            subject_name = subject["name"]
            
            if subject_name == "Mathematics":
                chapters_data.extend([
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Numbers and Counting",
                        "description": "Learn basic numbers and counting",
                        "subject_id": subject_id,
                        "content": "This chapter introduces students to the world of numbers. Students will learn to recognize numbers from 1 to 100, understand the concept of quantity, and practice counting objects. Activities include number recognition games, counting exercises, and simple number patterns.",
                        "created_at": datetime.utcnow()
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Addition and Subtraction",
                        "description": "Basic arithmetic operations",
                        "subject_id": subject_id,
                        "content": "Students will master the fundamental operations of addition and subtraction. Starting with single-digit numbers, they will progress to double-digit calculations. Visual aids, manipulatives, and real-world examples help students understand these concepts.",
                        "created_at": datetime.utcnow()
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Shapes and Geometry",
                        "description": "Basic geometric shapes and properties",
                        "subject_id": subject_id,
                        "content": "Explore the world of shapes! Students will identify and describe basic geometric shapes including circles, squares, triangles, and rectangles. They will learn about shape properties, symmetry, and spatial relationships through hands-on activities.",
                        "created_at": datetime.utcnow()
                    }
                ])
            elif subject_name == "English":
                chapters_data.extend([
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Alphabets and Phonics",
                        "description": "Learn letters and sounds",
                        "subject_id": subject_id,
                        "content": "Master the English alphabet and phonics system. Students will learn letter recognition, both uppercase and lowercase, and understand the sounds each letter makes. Interactive activities include letter tracing, sound games, and phonics exercises.",
                        "created_at": datetime.utcnow()
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Reading Comprehension",
                        "description": "Understanding and interpreting text",
                        "subject_id": subject_id,
                        "content": "Develop strong reading skills through engaging stories and exercises. Students will learn to understand main ideas, identify details, make predictions, and answer questions about what they read. Age-appropriate texts and interactive activities enhance comprehension.",
                        "created_at": datetime.utcnow()
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Creative Writing",
                        "description": "Express ideas through writing",
                        "subject_id": subject_id,
                        "content": "Unleash creativity through writing! Students will learn to express their thoughts and ideas through various writing forms including stories, poems, and descriptive paragraphs. Grammar, vocabulary, and creative expression are emphasized.",
                        "created_at": datetime.utcnow()
                    }
                ])
            elif subject_name == "Science":
                chapters_data.extend([
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Living and Non-Living Things",
                        "description": "Understand the difference between living and non-living",
                        "subject_id": subject_id,
                        "content": "Explore the natural world by learning to distinguish between living and non-living things. Students will discover the characteristics of life, observe plants and animals, and understand basic life processes through experiments and observations.",
                        "created_at": datetime.utcnow()
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Weather and Seasons",
                        "description": "Learn about weather patterns and seasonal changes",
                        "subject_id": subject_id,
                        "content": "Discover the fascinating world of weather and seasons! Students will learn about different weather conditions, seasonal changes, and how weather affects our daily lives. Activities include weather observation, seasonal activities, and simple weather experiments.",
                        "created_at": datetime.utcnow()
                    }
                ])
            elif subject_name == "Social Studies":
                chapters_data.extend([
                    {
                        "id": str(uuid.uuid4()),
                        "name": "My Family and Community",
                        "description": "Understanding family structures and community roles",
                        "subject_id": subject_id,
                        "content": "Explore the importance of family and community in our lives. Students will learn about different family structures, community helpers, and how people work together to create a better society. Activities include family tree creation and community exploration.",
                        "created_at": datetime.utcnow()
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Maps and Locations",
                        "description": "Basic geography and map reading skills",
                        "subject_id": subject_id,
                        "content": "Learn to navigate the world through maps! Students will understand basic map concepts, directions (north, south, east, west), and how to locate places on simple maps. Interactive map activities and location games make learning fun.",
                        "created_at": datetime.utcnow()
                    }
                ])
        
        chapters_collection.insert_many(chapters_data)
        
        # Create sample assignments and quizzes
        sample_assignments = []
        sample_quizzes = []
        
        for chapter in chapters_data[:5]:  # Create assignments for first 5 chapters
            assignment = {
                "id": str(uuid.uuid4()),
                "title": f"Assignment: {chapter['name']}",
                "description": f"Complete the exercises related to {chapter['name']}. This assignment will test your understanding of the key concepts covered in this chapter.",
                "chapter_id": chapter["id"],
                "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "points": 100,
                "created_at": datetime.utcnow()
            }
            sample_assignments.append(assignment)
            
            # Create sample quiz
            quiz = {
                "id": str(uuid.uuid4()),
                "title": f"Quiz: {chapter['name']}",
                "description": f"Test your knowledge of {chapter['name']} with this interactive quiz.",
                "chapter_id": chapter["id"],
                "questions": [
                    {
                        "question": f"What is the main topic of {chapter['name']}?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": 0,
                        "points": 5
                    },
                    {
                        "question": f"Which concept is most important in {chapter['name']}?",
                        "options": ["Concept 1", "Concept 2", "Concept 3", "Concept 4"],
                        "correct_answer": 1,
                        "points": 5
                    }
                ],
                "time_limit": 30,
                "created_at": datetime.utcnow()
            }
            sample_quizzes.append(quiz)
        
        assignments_collection.insert_many(sample_assignments)
        quizzes_collection.insert_many(sample_quizzes)

# Initialize data on startup
initialize_sample_data()

# Routes
@app.get("/")
async def root():
    return {"message": "Enhanced E-Learning Platform API - Full Featured"}

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
    
    # Get assignments for this chapter
    assignments = list(assignments_collection.find({"chapter_id": chapter_id}, {"_id": 0}))
    
    # Get quizzes for this chapter
    quizzes = list(quizzes_collection.find({"chapter_id": chapter_id}, {"_id": 0}))
    
    return {
        "chapter": chapter,
        "subject": subject,
        "class": class_info,
        "content": content,
        "assignments": assignments,
        "quizzes": quizzes
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

@app.get("/api/assignments/{chapter_id}")
async def get_chapter_assignments(chapter_id: str):
    assignments = list(assignments_collection.find({"chapter_id": chapter_id}, {"_id": 0}))
    return assignments

@app.get("/api/quizzes/{chapter_id}")
async def get_chapter_quizzes(chapter_id: str):
    quizzes = list(quizzes_collection.find({"chapter_id": chapter_id}, {"_id": 0}))
    return quizzes

@app.post("/api/progress/update")
async def update_progress(progress_data: ProgressUpdate, current_user: dict = Depends(get_current_user)):
    # Check if chapter exists
    chapter = chapters_collection.find_one({"id": progress_data.chapter_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Update or create progress record
    progress_record = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "chapter_id": progress_data.chapter_id,
        "completed": progress_data.completed,
        "score": progress_data.score,
        "completed_at": datetime.utcnow()
    }
    
    # Check if progress already exists
    existing_progress = progress_collection.find_one({
        "user_id": current_user["id"],
        "chapter_id": progress_data.chapter_id
    })
    
    if existing_progress:
        progress_collection.update_one(
            {"id": existing_progress["id"]},
            {"$set": {"completed": progress_data.completed, "score": progress_data.score, "completed_at": datetime.utcnow()}}
        )
    else:
        progress_collection.insert_one(progress_record)
    
    return {"message": "Progress updated successfully"}

@app.get("/api/progress/user/{user_id}")
async def get_user_progress(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    progress_records = list(progress_collection.find({"user_id": user_id}, {"_id": 0}))
    return progress_records

# Admin routes
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

@app.post("/api/admin/assignment")
async def create_assignment(assignment_data: AssignmentCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    assignment_record = {
        "id": str(uuid.uuid4()),
        "title": assignment_data.title,
        "description": assignment_data.description,
        "chapter_id": assignment_data.chapter_id,
        "due_date": assignment_data.due_date,
        "points": assignment_data.points,
        "created_at": datetime.utcnow()
    }
    
    assignments_collection.insert_one(assignment_record)
    
    return {"message": "Assignment created successfully", "assignment_id": assignment_record["id"]}

@app.post("/api/admin/quiz")
async def create_quiz(quiz_data: QuizCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    quiz_record = {
        "id": str(uuid.uuid4()),
        "title": quiz_data.title,
        "description": quiz_data.description,
        "chapter_id": quiz_data.chapter_id,
        "questions": quiz_data.questions,
        "time_limit": quiz_data.time_limit,
        "created_at": datetime.utcnow()
    }
    
    quizzes_collection.insert_one(quiz_record)
    
    return {"message": "Quiz created successfully", "quiz_id": quiz_record["id"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)