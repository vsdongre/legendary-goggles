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

    def test_get_courses(self):
        """Test getting all courses"""
        success, response = self.run_test("Get All Courses", "GET", "api/courses", 200)
        if success and isinstance(response, list):
            print(f"   Found {len(response)} courses")
            if len(response) > 0:
                course = response[0]
                print(f"   Sample course: {course.get('title', 'No title')}")
                return True, response
        return success, response

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

    def test_enroll_in_course(self, course_id):
        """Test enrolling in a course"""
        if not self.token:
            print("❌ No token available for enrollment test")
            return False
            
        enrollment_data = {
            "course_id": course_id
        }
        
        success, response = self.run_test(
            "Enroll in Course",
            "POST",
            "api/enrollments",
            200,
            data=enrollment_data
        )
        
        return success

    def test_get_user_enrollments(self):
        """Test getting user enrollments"""
        if not self.token or not self.user_id:
            print("❌ No token or user_id available for enrollments test")
            return False, []
            
        success, response = self.run_test(
            "Get User Enrollments",
            "GET",
            f"api/enrollments/user/{self.user_id}",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} enrollments")
            return True, response
        return False, []

    def test_update_progress(self, course_id, lesson_id):
        """Test updating lesson progress"""
        if not self.token:
            print("❌ No token available for progress test")
            return False
            
        progress_data = {
            "course_id": course_id,
            "lesson_id": lesson_id,
            "completed": True
        }
        
        success, response = self.run_test(
            "Update Progress",
            "POST",
            "api/progress",
            200,
            data=progress_data
        )
        
        return success

    def test_get_course_progress(self, course_id):
        """Test getting user course progress"""
        if not self.token or not self.user_id:
            print("❌ No token or user_id available for progress test")
            return False
            
        success, response = self.run_test(
            "Get Course Progress",
            "GET",
            f"api/progress/user/{self.user_id}/course/{course_id}",
            200
        )
        
        return success

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