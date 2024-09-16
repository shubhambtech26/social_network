# Social Networking API

This is a Django-based API for a social networking application built using Django Rest Framework (DRF). The API allows users to sign up, log in, send and manage friend requests, and search for other users by email or name. It supports token-based authentication and is containerized with Docker.

## Features

- User signup and login (case-insensitive email).
- User search by email or name (with pagination).
- Send, accept, and reject friend requests (rate-limited).
- List all friends and pending friend requests.
- Token-based authentication for secure API access.

## Technologies

- Python 3.10
- Django 4.x
- Django Rest Framework
- PostgreSQL
- Docker and Docker Compose

## Prerequisites

- Docker & Docker Compose installed on your machine.
- Python 3.10+ and pip (if not using Docker).

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/shubhambtech26/social_network.git
cd social_network
```

### 2. Set Up the Environment

If you are using Docker (recommended), skip this step. If you're not using Docker, set up a virtual environment and install the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Docker Setup (Recommended)

Ensure that Docker and Docker Compose are installed.

Build and Start the Containers:

```bash
docker-compose up --build
```

Run Database Migrations:

```bash
docker-compose exec web python manage.py migrate
```

Create a Superuser (Optional): To access the Django admin panel, you can create a superuser.

```bash
docker-compose exec web python manage.py createsuperuser
```

Access the Application: Once the containers are up and running, the Django application will be accessible at:

```
http://localhost:8000
```

### 4. Without Docker (Local Setup)

Install dependencies (after setting up a virtual environment):

```bash
pip install -r requirements.txt
```

Create a .env file with the following configuration:

```
DATABASE_URL=postgres://USER:PASSWORD@localhost:5432/social_network_db
```

Run Migrations:

```bash
python manage.py migrate
```

Start the Development Server:

```bash
python manage.py runserver
```

## API Endpoints

1. **Signup**
   - URL: `/api/signup/`
   - Method: POST
   - Body (JSON):
     ```json
     {
       "username": "testuser",
       "email": "test@example.com",
       "password": "strongpassword"
     }
     ```

2. **Login**
   - URL: `/api/login/`
   - Method: POST
   - Body (JSON):
     ```json
     {
       "email": "test@example.com",
       "password": "strongpassword"
     }
     ```

3. **Search Users**
   - URL: `/api/search/?q={query}`
   - Method: GET
   - Authorization: Bearer Token {{token}}
   - Params:
     - q: Search term (e.g., part of a username or exact email).

4. **Send Friend Request**
   - URL: `/api/friend-request/send/`
   - Method: POST
   - Authorization: Bearer Token {{token}}
   - Body (JSON):
     ```json
     {
       "to_user_id": 2
     }
     ```

5. **Manage Friend Request**
   - URL: `/api/friend-request/manage/`
   - Method: POST
   - Authorization: Bearer Token {{token}}
   - Body (JSON):
     ```json
     {
       "request_id": 5,
       "action": "accept"  // or "reject"
     }
     ```

6. **List Friends**
   - URL: `/api/friends/`
   - Method: GET
   - Authorization: Bearer Token {{token}}

7. **List Pending Friend Requests**
   - URL: `/api/friend-requests/pending/`
   - Method: GET
   - Authorization: Bearer Token {{token}}

## Rate Limiting

Users can send a maximum of 3 friend requests per minute. If this limit is exceeded, the API will return a 429 Too Many Requests error.

## Testing

You can test the API using Postman or curl. A Postman collection is provided for easy testing.

### Import Postman Collection

A Postman collection file named `social_network_api_collection.json` is available for quick API testing.
To import it:
1. Open Postman.
2. Click "Import" and upload the .json file.

## Deployment

### Using Docker

1. Ensure Docker is installed on your production server.
2. Clone the repository, and run the following command to start the service:
   ```bash
   docker-compose up --build -d
   ```

### Without Docker

1. Set up a PostgreSQL database and update `settings.py` or `.env` with the correct database credentials.
2. Run migrations and start the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Contributing

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/my-new-feature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/my-new-feature`).
5. Create a new Pull Request.
