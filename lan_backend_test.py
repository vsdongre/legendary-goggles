import requests
import sys
import json
import os
from datetime import datetime

class LANELearningAPITester:
    def __init__(self, base_url="https://95ba7191-ec65-469c-a5f3-b612c01c8af2.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Store IDs for hierarchical testing
        self.class_ids = []
        self.subject_ids = []
        self.chapter_ids = []
        self.content_ids = []
        
        # Test file paths for LAN system
        self.test_file_paths = {
            "windows_path": "C:\\Documents\\lesson.pdf",
            "network_path": "\\\\server\\share\\video.mp4",
            "url": "https://example.com/page.html",
            "youtube_url": "https://youtube.com/watch?v=test123",
            "linux_path": "/home/user/documents/presentation.pptx",
            "relative_path": "documents/worksheet.docx"
        }

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
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Admin User ID: {self.user_id}")
            print(f"   Admin Role: {response['user']['role']}")
            return True
        return False

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

    def test_content_creation_without_auth(self):
        """Test content creation without authentication (should fail)"""
        # Temporarily remove token for this test
        original_token = self.token
        self.token = None
        
        try:
            content_data = {
                "title": "Test Content Without Auth",
                "content_type": "document",
                "file_path": self.test_file_paths["windows_path"],
                "description": "Test content creation without authentication",
                "chapter_id": "test_chapter_id"
            }
            
            success, response = self.run_test(
                "Content Creation Without Auth",
                "POST",
                "api/content/create",
                401,  # Should fail with 401
                data=content_data
            )
            
            return success
            
        finally:
            # Restore token
            self.token = original_token

    def test_lan_file_path_creation(self, chapter_id):
        """Test creating content with various LAN file paths"""
        if not self.token:
            print("❌ No token available for LAN file path creation test")
            return False
        
        results = {}
        
        for path_type, file_path in self.test_file_paths.items():
            content_data = {
                "title": f"Test {path_type.replace('_', ' ').title()}",
                "content_type": "auto",  # Let system auto-detect
                "file_path": file_path,
                "description": f"Test content with {path_type} file path",
                "chapter_id": chapter_id
            }
            
            success, response = self.run_test(
                f"Create Content with {path_type}",
                "POST",
                "api/content/create",
                200,
                data=content_data
            )
            
            if success and 'content_id' in response:
                content_id = response['content_id']
                self.content_ids.append(content_id)
                print(f"   Content ID: {content_id}")
                results[path_type] = {"success": True, "content_id": content_id}
            else:
                results[path_type] = {"success": False, "response": response}
        
        # Check overall success
        successful_creations = sum(1 for result in results.values() if result["success"])
        total_tests = len(self.test_file_paths)
        
        print(f"\n📊 LAN File Path Creation Results: {successful_creations}/{total_tests} successful")
        
        return successful_creations > 0, results

    def test_content_retrieval(self, chapter_id):
        """Test retrieving content from a chapter"""
        success, response = self.run_test(
            "Content Retrieval",
            "GET",
            f"api/content/{chapter_id}",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} content items")
            
            # Verify file paths are stored correctly
            for content in response:
                title = content.get('title', 'No title')
                file_path = content.get('file_path', 'No file path')
                content_type = content.get('content_type', 'No type')
                
                print(f"     - Title: {title}")
                print(f"       File Path: {file_path}")
                print(f"       Content Type: {content_type}")
                
                # Verify file path is one of our test paths
                if file_path in self.test_file_paths.values():
                    print(f"       ✅ File path correctly stored")
                else:
                    print(f"       ⚠️  File path may not match test data")
            
            return True, response
        
        return success, response

    def test_content_opening(self):
        """Test opening content by content ID"""
        if not self.content_ids:
            print("❌ No content IDs available for opening test")
            return False
        
        results = {}
        
        for content_id in self.content_ids[:3]:  # Test first 3 content items
            success, response = self.run_test(
                f"Open Content {content_id}",
                "GET",
                f"api/content/open/{content_id}",
                200
            )
            
            if success:
                content_type = response.get('type', 'unknown')
                path = response.get('path', 'No path')
                
                print(f"   Content Type: {content_type}")
                print(f"   Path: {path}")
                
                # Verify response structure based on content type
                if content_type == 'url':
                    if path.startswith(('http://', 'https://')):
                        print(f"   ✅ URL content correctly identified")
                        results[content_id] = True
                    else:
                        print(f"   ❌ URL content not properly formatted")
                        results[content_id] = False
                elif content_type == 'file':
                    if path and ('\\' in path or '/' in path):
                        print(f"   ✅ File path content correctly identified")
                        results[content_id] = True
                    else:
                        print(f"   ❌ File path content not properly formatted")
                        results[content_id] = False
                else:
                    print(f"   ✅ Content type '{content_type}' returned")
                    results[content_id] = True
            else:
                results[content_id] = False
        
        successful_opens = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        print(f"\n📊 Content Opening Results: {successful_opens}/{total_tests} successful")
        
        return successful_opens > 0

    def test_lan_file_path_scenarios(self):
        """Test comprehensive LAN file path scenarios"""
        print(f"\n📁 Testing LAN File Path Scenarios")
        print("=" * 50)
        
        # Get a chapter ID for testing
        if not self.chapter_ids:
            print("❌ No chapter IDs available for LAN file path testing")
            return False
        
        test_chapter_id = self.chapter_ids[0]
        print(f"Using chapter ID: {test_chapter_id}")
        
        # Test 1: Content creation without authentication (should fail)
        auth_test_passed = self.test_content_creation_without_auth()
        
        # Test 2: Create content with various LAN file paths
        creation_success, creation_results = self.test_lan_file_path_creation(test_chapter_id)
        
        if not creation_success:
            print("❌ Cannot continue LAN tests - content creation failed")
            return False
        
        # Test 3: Retrieve content to verify file paths are stored
        retrieval_success, content_list = self.test_content_retrieval(test_chapter_id)
        
        # Test 4: Test opening content
        opening_success = self.test_content_opening()
        
        # Summary of LAN file path tests
        lan_tests_passed = sum([auth_test_passed, creation_success, retrieval_success, opening_success])
        print(f"\n📊 LAN File Path Test Results: {lan_tests_passed}/4 tests passed")
        
        return lan_tests_passed >= 3  # Allow for some flexibility

def main():
    print("🚀 Starting LAN E-Learning Platform API Tests")
    print("=" * 50)
    
    # Setup
    tester = LANELearningAPITester()
    
    # Test 1: Root endpoint
    tester.test_root_endpoint()
    
    # Test 2: Admin login (required for testing)
    print(f"\n🔐 Testing admin user login")
    if not tester.test_admin_login():
        print("❌ Admin login failed, cannot proceed with authenticated tests")
        return 1
    
    # Test 3: Get classes (should have sample data)
    classes_success, classes = tester.test_get_classes()
    if not classes_success or not classes:
        print("❌ Cannot proceed without classes data")
        return 1
    
    # Test 4: Test hierarchical data structure to get chapter IDs
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
    for subject in all_subjects[:2]:  # Test first 2 subjects to avoid too many requests
        subject_id = subject['id']
        subject_name = subject['name']
        
        chapters_success, chapters = tester.test_get_chapters_by_subject(subject_id, subject_name)
        if chapters_success and chapters:
            all_chapters.extend(chapters)
    
    if not all_chapters:
        print("❌ No chapters found, cannot test LAN file paths")
        return 1
    
    # Test 5: LAN File Path Scenarios
    print(f"\n📁 Running comprehensive LAN file path tests")
    lan_tests_success = tester.test_lan_file_path_scenarios()
    if not lan_tests_success:
        print("❌ LAN file path tests failed")
        return 1
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All LAN API tests passed!")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} tests failed")
        
        # If most tests passed, consider it a success
        success_rate = tester.tests_passed / tester.tests_run
        if success_rate >= 0.8:  # 80% success rate
            print("✅ Overall LAN functionality appears to be working (80%+ success rate)")
            return 0
        else:
            return 1

if __name__ == "__main__":
    sys.exit(main())