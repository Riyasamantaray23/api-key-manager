API Key Management System
This project implements a foundational API Key Management System using Django, Django REST Framework, and Redis. It provides core functionalities for issuing, revoking, and authenticating API keys to secure access to your APIs.

🧩 What the Project Does
This system acts as a centralized manager for controlling access to your various APIs. Its primary functions include:

API Key Issuance: Generates unique, secure API keys for clients to access your services.

API Key Revocation: Allows immediate deactivation of API keys to block access when needed.

Fast Authentication: Verifies incoming API requests by checking for valid, active, and unexpired API keys using high-speed Redis lookups, with a fallback to the database.

✨ Key Features
Secure Key Generation: Automatically generates unique hexadecimal API keys.

Key Lifecycle Management: Supports active and revoked statuses, along with optional expiration dates.

Redis Caching: Leverages Redis for extremely fast API key validation, reducing database load on every request.

Django Admin Integration: Provides a user-friendly interface for administrators to manage API keys (issue, view, revoke).

DRF Permissions: Integrates seamlessly with Django REST Framework to protect your API endpoints.

🚀 Technologies Used
Python: The core programming language.

Django: The high-level Python web framework.

Django REST Framework (DRF): For building powerful and flexible APIs.

Redis: An in-memory data structure store, used for fast API key lookups and status caching.

🛠️ Setup Instructions
Note: Assumes global Python installation.

1. Install Python
Ensure Python 3.8+ is installed and added to PATH.

2. Install Redis Server
Install Redis for your OS (Windows/WSL: sudo apt install redis-server; macOS: brew install redis; Linux: sudo apt install redis-server). Verify with redis-cli ping.

3. Install Python Dependencies
Navigate to project directory (api_key_manager_project) and run: pip install Django djangorestframework redis.

4. Configure Django Settings
In api_key_manager_system/settings.py, add api_key_manager and rest_framework to INSTALLED_APPS, and add Redis config (REDIS_HOST, REDIS_PORT, REDIS_DB).

5. Database Setup
Navigate to project directory and run: python manage.py migrate and python manage.py createsuperuser.

6. Run Application
Navigate to project directory and run: python manage.py runserver. Access Django Admin at http://127.0.0.1:8000/admin/.

💡 Using the API Endpoints
Use an API client (Postman/Insomnia).

1. Issue an API Key
URL: http://127.0.0.1:8000/api/v1/keys/issue/

Method: POST

Headers: Content-Type: application/json

Body: {"name": "MyNewClientAppKey"}

Response: JSON with generated key.

2. Revoke an API Key
URL: http://127.0.0.1:8000/api/v1/keys/revoke/

Method: POST

Headers: Content-Type: application/json

Body: {"key": "YOUR_API_KEY_TO_REVOKE"}

Response: {"detail": "API Key revoked successfully."}

3. Access a Protected Endpoint
URL: http://127.0.0.1:8000/api/v1/keys/test-protected/

Method: GET

Headers: X-API-KEY: YOUR_VALID_API_KEY

Expected Responses:

No Key: 403 Forbidden ("API Key is missing...")

Invalid Key: 403 Forbidden ("Invalid API Key.")

Valid Key: 200 OK ("Hello from protected endpoint...")

Revoked Key: 403 Forbidden ("API Key is not active or has been revoked.")