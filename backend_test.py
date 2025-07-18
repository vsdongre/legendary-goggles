import requests
import sys
import json
from datetime import datetime

class ELearningAPITester:
    def __init__(self, base_url="https://fcddef90-9f88-49d8-b843-8e55bf0c7946.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_email = f"test_user_{datetime.now().strftime('%H%M%S')}@example.com"
        self.test_user_password = "TestPass123!"
        self.test_username = f"testuser_{datetime.now().strftime('%H%M%S')}"
        
        # Store IDs for hierarchical testing
        self.class_ids = []
        self.subject_ids = []
        self.chapter_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response: {len(response_data)} items returned")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")

            return success, response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_get_classes(self):
        """Test getting all classes"""
        success, response = self.run_test("Get All Classes", "GET", "api/classes", 200)
        if success and isinstance(response, list):
            print(f"   Found {len(response)} classes")
            self.class_ids = [cls['id'] for cls in response]
            if len(response) > 0:
                class_item = response[0]
                print(f"   Sample class: {class_item.get('name', 'No name')}")
                return True, response
        return success, response

    def test_demo_login(self):
        """Test demo user login"""
        login_data = {
            "email": "demo@example.com",
            "password": "Demo123!"
        }
        
        success, response = self.run_test(
            "Demo User Login",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Demo User ID: {self.user_id}")
            return True
        return False

    def test_signup(self):
        """Test user signup"""
        signup_data = {
            "username": self.test_username,
            "email": self.test_user_email,
            "password": self.test_user_password,
            "role": "student"
        }
        
        success, response = self.run_test(
            "User Signup",
            "POST",
            "api/auth/signup",
            200,
            data=signup_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   User ID: {self.user_id}")
            return True
        return False

    def test_login(self):
        """Test user login"""
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_get_user_info(self):
        """Test getting current user info"""
        if not self.token:
            print("❌ No token available for user info test")
            return False
            
        success, response = self.run_test(
            "Get User Info",
            "GET",
            "api/auth/user",
            200
        )
        
        if success and 'id' in response:
            print(f"   User: {response.get('username')} ({response.get('email')})")
            return True
        return False

    def test_get_subjects_by_class(self, class_id, class_name):
        """Test getting subjects for a specific class"""
        success, response = self.run_test(
            f"Get Subjects for {class_name}",
            "GET",
            f"api/subjects/{class_id}",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} subjects for {class_name}")
            if len(response) > 0:
                subject_ids = [subj['id'] for subj in response]
                self.subject_ids.extend(subject_ids)
                for subject in response:
                    print(f"     - {subject.get('name', 'No name')}")
                return True, response
        return success, response

    def test_get_chapters_by_subject(self, subject_id, subject_name):
        """Test getting chapters for a specific subject"""
        success, response = self.run_test(
            f"Get Chapters for {subject_name}",
            "GET",
            f"api/chapters/{subject_id}",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} chapters for {subject_name}")
            if len(response) > 0:
                chapter_ids = [chap['id'] for chap in response]
                self.chapter_ids.extend(chapter_ids)
                for chapter in response:
                    print(f"     - {chapter.get('name', 'No name')}")
                return True, response
        return success, response

    def test_get_chapter_details(self, chapter_id, chapter_name):
        """Test getting detailed chapter information"""
        success, response = self.run_test(
            f"Get Chapter Details for {chapter_name}",
            "GET",
            f"api/chapter/{chapter_id}",
            200
        )
        
        if success and isinstance(response, dict):
            chapter = response.get('chapter', {})
            subject = response.get('subject', {})
            class_info = response.get('class', {})
            content = response.get('content', [])
            
            print(f"   Chapter: {chapter.get('name', 'No name')}")
            print(f"   Subject: {subject.get('name', 'No name')}")
            print(f"   Class: {class_info.get('name', 'No name')}")
            print(f"   Content items: {len(content)}")
            return True, response
        return success, response

    def test_content_upload(self, chapter_id):
        """Test content upload functionality"""
        if not self.token:
            print("❌ No token available for content upload test")
            return False
            
        upload_data = {
            "chapter_id": chapter_id,
            "title": "Test Content Upload",
            "content_type": "text",
            "content_data": "This is a test content upload to verify the API functionality."
        }
        
        success, response = self.run_test(
            "Content Upload",
            "POST",
            "api/content/upload",
            200,
            data=upload_data
        )
        
        if success and 'content_id' in response:
            print(f"   Content ID: {response['content_id']}")
            return True
        return False

def main():
    print("🚀 Starting E-Learning Platform API Tests")
    print("=" * 50)
    
    # Setup
    tester = ELearningAPITester()
    
    # Test 1: Root endpoint
    tester.test_root_endpoint()
    
    # Test 2: Get courses (should have sample data)
    courses_success, courses = tester.test_get_courses()
    if not courses_success or not courses:
        print("❌ Cannot proceed without courses data")
        return 1
    
    # Test 3: User signup
    if not tester.test_signup():
        print("❌ Signup failed, stopping tests")
        return 1
    
    # Test 4: Get user info (verify JWT token works)
    if not tester.test_get_user_info():
        print("❌ User info retrieval failed")
        return 1
    
    # Test 5: Enroll in first course
    first_course = courses[0]
    course_id = first_course['id']
    print(f"\n📚 Testing enrollment in course: {first_course['title']}")
    
    if not tester.test_enroll_in_course(course_id):
        print("❌ Course enrollment failed")
        return 1
    
    # Test 6: Get user enrollments
    enrollments_success, enrollments = tester.test_get_user_enrollments()
    if not enrollments_success:
        print("❌ Getting enrollments failed")
        return 1
    
    # Test 7: Update progress for first lesson
    if enrollments and len(enrollments) > 0:
        enrolled_course = enrollments[0]['course']
        if enrolled_course and 'content' in enrolled_course and len(enrolled_course['content']) > 0:
            first_lesson_id = enrolled_course['content'][0]['id']
            print(f"\n📖 Testing progress update for lesson: {enrolled_course['content'][0]['title']}")
            
            if not tester.test_update_progress(course_id, first_lesson_id):
                print("❌ Progress update failed")
                return 1
            
            # Test 8: Get course progress
            if not tester.test_get_course_progress(course_id):
                print("❌ Getting course progress failed")
                return 1
    
    # Test 9: Test login with existing user
    print(f"\n🔐 Testing login with existing user")
    if not tester.test_login():
        print("❌ Login with existing user failed")
        return 1
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All API tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())