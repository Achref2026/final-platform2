import requests
import sys
import json
from datetime import datetime
import uuid
import time
import random

class DrivingSchoolAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_data = None
        self.test_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.created_school_id = None
        self.enrollment_id = None
        self.course_id = None
        self.document_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # For multipart/form-data (file uploads)
                    response = requests.post(url, data=data, files=files, headers={k: v for k, v in headers.items() if k != 'Content-Type'})
                else:
                    response = requests.post(url, json=data, headers=headers)
            
            print(f"URL: {url}")
            print(f"Status Code: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response: {response.text}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")

            try:
                return success, response.json()
            except:
                return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_endpoint(self):
        """Test the health endpoint"""
        success, response = self.run_test(
            "Health Endpoint",
            "GET",
            "health",
            200
        )
        return success
    
    def test_get_states(self):
        """Test getting the list of Algerian states"""
        success, response = self.run_test(
            "Get Algerian States",
            "GET",
            "states",
            200
        )
        
        if success and 'states' in response and len(response['states']) == 58:
            print(f"✅ Successfully retrieved {len(response['states'])} Algerian states")
        else:
            print("❌ Failed to retrieve all 58 Algerian states")
            success = False
            
        return success

    def test_register_user(self, role="student"):
        """Test user registration"""
        random_suffix = f"{random.randint(1000, 9999)}"
        email = f"test{role}{random_suffix}@example.com"
        password = "TestPass123!"
        
        # Create form data for registration
        form_data = {
            "email": email,
            "password": password,
            "first_name": f"Test{role.capitalize()}",
            "last_name": f"User{random_suffix}",
            "phone": "1234567890",
            "address": "Test Address",
            "date_of_birth": "1990-01-01",
            "gender": "male" if random.random() > 0.5 else "female",
            "state": "Alger"
        }
        
        # For multipart/form-data, we need to remove Content-Type header
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        # Use requests directly for form data
        self.tests_run += 1
        print(f"\n🔍 Testing Register {role.capitalize()} User...")
        
        try:
            url = f"{self.base_url}/auth/register"
            response = requests.post(url, data=form_data, headers=headers)
            
            print(f"URL: {url}")
            print(f"Status Code: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response: {response.text}")
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                self.token = response_data.get('access_token')
                self.user_data = response_data.get('user')
                print(f"✅ User registered successfully with email: {email}")
                return True, {"email": email, "password": password}
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                return False, None
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            print(f"✅ User registered successfully with email: {email}")
            return True, {"email": email, "password": password}
        else:
            print(f"❌ User registration failed")
            return False, None

    def test_login(self, email, password):
        """Test user login"""
        login_data = {
            "email": email,
            "password": password
        }
        
        success, response = self.run_test(
            f"Login as {email}",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            print(f"✅ Login successful for {email} with role: {response['user']['role']}")
            return True
        else:
            print(f"❌ Login failed for {email}")
            return False
    
    def test_get_driving_schools(self, state=None):
        """Test retrieving driving schools with optional state filter"""
        endpoint = "driving-schools" if state is None else f"driving-schools?state={state}"
        
        success, response = self.run_test(
            f"Get Driving Schools{' in ' + state if state else ''}",
            "GET",
            endpoint,
            200
        )
        
        if success and 'schools' in response:
            print(f"✅ Retrieved {len(response['schools'])} driving schools{' in ' + state if state else ''}")
            return True, response['schools']
        else:
            print(f"❌ Failed to retrieve driving schools{' in ' + state if state else ''}")
            return False, []
    
    def test_create_driving_school(self, school_data):
        """Test creating a new driving school (requires manager role or guest)"""
        # For multipart/form-data, we need to remove Content-Type header
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        success, response = self.run_test(
            "Create Driving School",
            "POST",
            "driving-schools",
            200,
            data=school_data,
            headers=headers
        )
        
        if success and 'id' in response:
            self.created_school_id = response['id']
            print(f"✅ Driving school created successfully with ID: {response['id']}")
            return True
        else:
            print("❌ Failed to create driving school")
            return False
    
    def test_get_driving_school_details(self, school_id):
        """Test retrieving details of a specific driving school"""
        success, response = self.run_test(
            f"Get Driving School Details (ID: {school_id})",
            "GET",
            f"driving-schools/{school_id}",
            200
        )
        
        if success and 'id' in response and response['id'] == school_id:
            print(f"✅ Retrieved details for driving school: {response['name']}")
            return True, response
        else:
            print(f"❌ Failed to retrieve driving school details for ID: {school_id}")
            return False, {}
    
    def test_student_enrollment(self, school_id):
        """Test student enrollment in a driving school"""
        enrollment_data = {
            "school_id": school_id
        }
        
        success, response = self.run_test(
            f"Enroll in Driving School (ID: {school_id})",
            "POST",
            "enrollments",
            200,
            data=enrollment_data
        )
        
        if success and 'enrollment_id' in response:
            self.enrollment_id = response['enrollment_id']
            print(f"✅ Enrollment successful with ID: {response['enrollment_id']}")
            return True
        else:
            print(f"❌ Failed to enroll in driving school")
            return False
    
    def test_get_student_enrollments(self):
        """Test retrieving student enrollments"""
        success, response = self.run_test(
            "Get Student Enrollments",
            "GET",
            "enrollments/my",
            200
        )
        
        if success:
            print(f"✅ Retrieved {len(response)} student enrollments")
            return True, response
        else:
            print("❌ Failed to retrieve student enrollments")
            return False, []
    
    def test_complete_payment(self, enrollment_id):
        """Test completing a payment for an enrollment"""
        form_data = {'enrollment_id': enrollment_id}
        
        # Set up headers without Content-Type (will be set by requests for form data)
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        success, response = self.run_test(
            f"Complete Payment for Enrollment (ID: {enrollment_id})",
            "POST",
            "payments/complete",
            200,
            data=form_data,
            headers=headers
        )
        
        if success:
            print(f"✅ Payment completed successfully")
            return True
        else:
            print("❌ Failed to complete payment")
            return False
    
    def test_upload_document(self, document_type="profile_photo"):
        """Test uploading a document"""
        # Create a simple test file
        file_content = b"This is a test file for document upload API testing."
        files = {
            'file': ('test_document.txt', file_content, 'text/plain')
        }
        
        # Set up headers without Content-Type (will be set by requests for multipart)
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        success, response = self.run_test(
            f"Upload Document ({document_type})",
            "POST",
            "documents/upload",
            200,
            data={'document_type': document_type},
            headers=headers,
            files=files
        )
        
        if success and 'document_id' in response:
            self.document_id = response['document_id']
            print(f"✅ Document uploaded successfully with ID: {response['document_id']}")
            return True
        else:
            print("❌ Failed to upload document")
            return False
    
    def test_get_my_documents(self):
        """Test retrieving current user's documents"""
        success, response = self.run_test(
            "Get My Documents",
            "GET",
            "documents/my",
            200
        )
        
        if success:
            print(f"✅ Retrieved {len(response)} documents")
            return True, response
        else:
            print("❌ Failed to retrieve documents")
            return False, []
    
    def test_get_dashboard_data(self, role):
        """Test retrieving dashboard data for a specific role"""
        success, response = self.run_test(
            f"Get {role.capitalize()} Dashboard",
            "GET",
            f"dashboard/{role}",
            200
        )
        
        if success:
            print(f"✅ Retrieved {role} dashboard data")
            return True, response
        else:
            print(f"❌ Failed to retrieve {role} dashboard data")
            return False, {}

def test_student_workflow(tester):
    """Test the complete student workflow"""
    print("\n" + "="*50)
    print("TESTING STUDENT WORKFLOW")
    print("="*50)
    
    # 1. Register a new student
    success, student_creds = tester.test_register_user("student")
    if not success:
        print("❌ Could not register as student")
        return False
    
    # 2. Get student dashboard
    tester.test_get_dashboard_data("student")
    
    # 3. Get available driving schools
    success, schools = tester.test_get_driving_schools()
    if not success or not schools:
        print("❌ No driving schools available for enrollment")
        return False
    
    # 4. Enroll in a driving school
    school_id = schools[0]['id']
    if not tester.test_student_enrollment(school_id):
        print("❌ Student workflow failed at enrollment")
        return False
    
    # 5. Get student enrollments
    success, enrollments = tester.test_get_student_enrollments()
    
    # 6. Complete payment (if enrollment was successful)
    if tester.enrollment_id:
        tester.test_complete_payment(tester.enrollment_id)
    
    # 7. Upload required documents
    for doc_type in ["profile_photo", "id_card", "medical_certificate"]:
        tester.test_upload_document(doc_type)
        time.sleep(1)  # Add a small delay between uploads
    
    # 8. Get student documents
    tester.test_get_my_documents()
    
    # 9. Get student enrollments again (should now show pending approval)
    tester.test_get_student_enrollments()
    
    # 10. Get student dashboard again (should now have enrollment data)
    tester.test_get_dashboard_data("student")
    
    print("✅ Student workflow completed successfully")
    return True

def test_manager_workflow(tester):
    """Test the complete manager workflow"""
    print("\n" + "="*50)
    print("TESTING MANAGER WORKFLOW")
    print("="*50)
    
    # 1. Register a new user (will be guest role by default)
    success, manager_creds = tester.test_register_user("manager")
    if not success:
        print("❌ Could not register as guest")
        return False
    
    # 2. Create a driving school (this should upgrade the user to manager)
    school_data = {
        "name": f"Test Driving School {tester.test_timestamp}",
        "address": "123 Test Street",
        "state": "Alger",
        "phone": "0555123456",
        "email": f"school{tester.test_timestamp}@example.com",
        "description": "A test driving school for API testing",
        "price": "25000.0"
    }
    
    if not tester.test_create_driving_school(school_data):
        print("❌ Manager workflow failed at school creation")
        return False
    
    # 3. Get school details
    if tester.created_school_id:
        tester.test_get_driving_school_details(tester.created_school_id)
    
    # 4. Get manager dashboard
    tester.test_get_dashboard_data("manager")
    
    print("✅ Manager workflow completed successfully")
    return True

def main():
    # Get the backend URL from the frontend .env file
    backend_url = "https://7dc8e0f1-b318-4bc8-bc0b-4a00b0580d84.preview.emergentagent.com"
    
    tester = DrivingSchoolAPITester(f"{backend_url}/api")
    
    # Test basic endpoints
    print("\n" + "="*50)
    print("TESTING BASIC ENDPOINTS")
    print("="*50)
    tester.test_health_endpoint()
    tester.test_get_states()
    
    # Test student workflow
    test_student_workflow(tester)
    
    # Test manager workflow
    test_manager_workflow(tester)
    
    # Print test results
    print("\n" + "="*50)
    print(f"📊 SUMMARY: Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("="*50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())