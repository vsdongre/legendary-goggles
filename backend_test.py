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

    def test_admin_login(self):
        """Test admin user login"""
        login_data = {
            "email": "admin@example.com",
            "password": "Admin123!"
        }
        
        success, response = self.run_test(
            "Admin User Login",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            print(f"   Admin User ID: {self.admin_user_id}")
            print(f"   Admin Role: {response['user']['role']}")
            return True
        return False

    def test_create_demo_student(self):
        """Create demo student if it doesn't exist"""
        signup_data = {
            "username": "demo_user",
            "email": "demo@example.com",
            "password": "Demo123!",
            "role": "student"
        }
        
        success, response = self.run_test(
            "Create Demo Student",
            "POST",
            "api/auth/signup",
            200,
            data=signup_data
        )
        
        if success and 'access_token' in response:
            print(f"   Demo student created successfully")
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
    
    # Test 2: Get classes (should have sample data)
    classes_success, classes = tester.test_get_classes()
    if not classes_success or not classes:
        print("❌ Cannot proceed without classes data")
        return 1
    
    # Test 3: Demo user login
    print(f"\n🔐 Testing demo user login")
    if not tester.test_demo_login():
        print("❌ Demo login failed, trying signup")
        
        # Test 4: User signup as fallback
        if not tester.test_signup():
            print("❌ Signup failed, stopping tests")
            return 1
    
    # Test 5: Get user info (verify JWT token works)
    if not tester.test_get_user_info():
        print("❌ User info retrieval failed")
        return 1
    
    # Test 6: Test hierarchical data structure
    print(f"\n📚 Testing hierarchical data structure")
    
    # Test subjects for each class
    all_subjects = []
    for class_item in classes:
        class_id = class_item['id']
        class_name = class_item['name']
        
        subjects_success, subjects = tester.test_get_subjects_by_class(class_id, class_name)
        if subjects_success and subjects:
            all_subjects.extend(subjects)
    
    if not all_subjects:
        print("❌ No subjects found, cannot test chapters")
        return 1
    
    # Test chapters for each subject
    all_chapters = []
    for subject in all_subjects[:3]:  # Test first 3 subjects to avoid too many requests
        subject_id = subject['id']
        subject_name = subject['name']
        
        chapters_success, chapters = tester.test_get_chapters_by_subject(subject_id, subject_name)
        if chapters_success and chapters:
            all_chapters.extend(chapters)
    
    if not all_chapters:
        print("❌ No chapters found, cannot test chapter details")
        return 1
    
    # Test chapter details for first few chapters
    print(f"\n📖 Testing chapter details")
    for chapter in all_chapters[:3]:  # Test first 3 chapters
        chapter_id = chapter['id']
        chapter_name = chapter['name']
        
        details_success, details = tester.test_get_chapter_details(chapter_id, chapter_name)
        if not details_success:
            print(f"❌ Failed to get details for chapter: {chapter_name}")
            return 1
    
    # Test 7: Content upload
    if all_chapters:
        first_chapter_id = all_chapters[0]['id']
        print(f"\n📤 Testing content upload")
        if not tester.test_content_upload(first_chapter_id):
            print("❌ Content upload failed")
            return 1
    
    # Test 8: Test login with new user (if we created one)
    if tester.test_user_email != "demo@example.com":
        print(f"\n🔐 Testing login with created user")
        if not tester.test_login():
            print("❌ Login with created user failed")
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