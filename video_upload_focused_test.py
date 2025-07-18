#!/usr/bin/env python3
"""
Focused test for video upload and serving functionality
"""
import requests
import json

def test_video_upload_and_serving():
    base_url = "https://6359bc25-627c-4dce-8575-b81593bd4fe0.preview.emergentagent.com"
    
    # Login as admin
    login_data = {
        "email": "admin@example.com",
        "password": "Admin123!"
    }
    
    print("🔐 Logging in as admin...")
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get a chapter ID
    print("📚 Getting classes and chapters...")
    classes_response = requests.get(f"{base_url}/api/classes")
    classes = classes_response.json()
    
    if not classes:
        print("❌ No classes found")
        return False
    
    # Get subjects for first class
    subjects_response = requests.get(f"{base_url}/api/subjects/{classes[0]['id']}")
    subjects = subjects_response.json()
    
    if not subjects:
        print("❌ No subjects found")
        return False
    
    # Get chapters for first subject
    chapters_response = requests.get(f"{base_url}/api/chapters/{subjects[0]['id']}")
    chapters = chapters_response.json()
    
    if not chapters:
        print("❌ No chapters found")
        return False
    
    chapter_id = chapters[0]['id']
    print(f"✅ Using chapter: {chapters[0]['name']} (ID: {chapter_id})")
    
    # Test 1: Upload a video file
    print("\n🎥 Testing video file upload...")
    test_video_content = b"FAKE_MP4_CONTENT_FOR_TESTING_PURPOSES_ONLY"
    
    url = f"{base_url}/api/content/upload-file?chapter_id={chapter_id}&title=Focused Test Video"
    files = {'file': ('focused_test.mp4', test_video_content, 'video/mp4')}
    
    upload_response = requests.post(url, files=files, headers=headers)
    
    if upload_response.status_code == 200:
        upload_data = upload_response.json()
        content_id = upload_data.get('content_id')
        print(f"✅ Video uploaded successfully! Content ID: {content_id}")
    else:
        print(f"❌ Upload failed: {upload_response.text}")
        return False
    
    # Test 2: Verify content is stored in database
    print("\n📊 Testing database storage...")
    content_response = requests.get(f"{base_url}/api/content/{chapter_id}")
    
    if content_response.status_code == 200:
        content_list = content_response.json()
        
        # Find our uploaded video
        uploaded_video = None
        for item in content_list:
            if item.get('filename') == 'focused_test.mp4':
                uploaded_video = item
                break
        
        if uploaded_video:
            print(f"✅ Video found in database:")
            print(f"   - Title: {uploaded_video.get('title')}")
            print(f"   - Content Type: {uploaded_video.get('content_type')}")
            print(f"   - File Path: {uploaded_video.get('content_data')}")
            print(f"   - Original Filename: {uploaded_video.get('filename')}")
            
            file_path = uploaded_video.get('content_data')
        else:
            print("❌ Uploaded video not found in database")
            return False
    else:
        print(f"❌ Failed to retrieve content: {content_response.text}")
        return False
    
    # Test 3: Test static file serving
    print("\n🌐 Testing static file serving...")
    if file_path:
        static_url = f"{base_url}/{file_path}"
        static_response = requests.get(static_url)
        
        if static_response.status_code == 200:
            print(f"✅ File served successfully!")
            print(f"   - Status: {static_response.status_code}")
            print(f"   - Content-Type: {static_response.headers.get('content-type', 'Not specified')}")
            print(f"   - Content-Length: {len(static_response.content)} bytes")
            print(f"   - Content matches: {static_response.content == test_video_content}")
        else:
            print(f"❌ Static file serving failed: {static_response.status_code}")
            print(f"   Response: {static_response.text}")
            return False
    
    # Test 4: Test content type detection
    print("\n🔍 Testing content type detection...")
    
    # Test different file extensions
    test_files = [
        ('test.jpg', b'fake_jpg_content', 'image/jpeg', 'image'),
        ('test.pdf', b'fake_pdf_content', 'application/pdf', 'document'),
        ('test.avi', b'fake_avi_content', 'video/avi', 'video'),
    ]
    
    for filename, content, mime_type, expected_type in test_files:
        url = f"{base_url}/api/content/upload-file?chapter_id={chapter_id}&title=Test {filename}"
        files = {'file': (filename, content, mime_type)}
        
        response = requests.post(url, files=files, headers=headers)
        if response.status_code == 200:
            print(f"✅ {filename} uploaded successfully")
        else:
            print(f"❌ {filename} upload failed: {response.text}")
    
    # Verify content types in database
    final_content_response = requests.get(f"{base_url}/api/content/{chapter_id}")
    if final_content_response.status_code == 200:
        final_content = final_content_response.json()
        
        print("\n📋 Final content summary:")
        content_types = {}
        for item in final_content:
            content_type = item.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        for content_type, count in content_types.items():
            print(f"   - {content_type}: {count} items")
    
    print("\n🎉 All video upload and serving tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_video_upload_and_serving()
    exit(0 if success else 1)