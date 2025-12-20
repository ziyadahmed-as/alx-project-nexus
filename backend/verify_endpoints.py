import requests
import json
import secrets
import time

BASE_URL = "http://localhost:8001/api"

# Generate random user data
random_string = secrets.token_hex(4)
user_data = {
    "username": f"testuser_{random_string}",
    "email": f"testuser_{random_string}@example.com",
    "password": "Password123!",
    "password_confirm": "Password123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "buyer",
    "terms_accepted": True
}

def print_result(step, response):
    status_msg = f"Status Code: {response.status_code}"
    if response.status_code >= 400:
        try:
            msg = f"Error Response: {response.json()}"
        except:
            msg = f"Error Response: {response.text}"
        result = "FAIL"
    else:
        result = "Success"
        msg = ""

    log_entry = f"\n--- {step} ---\n{status_msg}\n{result}\n{msg}\n"
    print(log_entry)
    with open("verification.log", "a") as f:
        f.write(log_entry)

# 1. Register User
print("\nTesting Registration...")
reg_response = requests.post(f"{BASE_URL}/auth/register/", json=user_data)
print_result("Registration", reg_response)

if reg_response.status_code != 201:
    print("Registration failed, aborting basic flow.")
    # Attempt login anyway if user exists
else:
    print("Registration Successful")

# 2. Login
print("\nTesting Login...")
login_data = {
    "username": user_data["email"],  # DRF simplejwt usually uses 'username' key but our custom serializer expects email in it
    "password": user_data["password"]
}
login_response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
print_result("Login", login_response)

tokens = {}
if login_response.status_code == 200:
    tokens = login_response.json()
    print("Login Successful")
    access_token = tokens.get('access')
else:
    print("Login Failed")
    access_token = None

# 3. Forgot Password Request
print("\nTesting Password Reset Request...")
reset_data = {"email": user_data["email"]}
reset_response = requests.post(f"{BASE_URL}/auth/password-reset/", json=reset_data)
print_result("Password Reset Request", reset_response)

# 4. User Profile (Protected)
if access_token:
    print("\nTesting Profile Access (Protected)...")
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_response = requests.get(f"{BASE_URL}/auth/profile/", headers=headers)
    print_result("Profile Fetch", profile_response)

# 5. Super Admin Creation Test
# We can't easily test this without a known superuser credentials. 
# But we can try to hit the endpoint with our normal user and expect 403 Forbidden.
if access_token:
    print("\nTesting Admin User Create (Should fail for Buyer)...")
    admin_create_data = {
        "username": f"newadmin_{random_string}",
        "email": f"newadmin_{random_string}@example.com",
        "first_name": "Admin",
        "last_name": "New",
        "role": "admin"
    }
    create_response = requests.post(f"{BASE_URL}/auth/create/", json=admin_create_data, headers=headers)
    print_result("Admin Create (Buyer)", create_response)
    if create_response.status_code == 403:
        print("PASS: Buyer correctly forbidden from creating admin.")
    else:
        print("FAIL: Buyer should be forbidden.")
