# padel-api microservice

Microservice is able to collect player availabilities and when reach 4 players, it will create a game and notify all players.

Service use a local sqlite database which is created on the first run, and located in the working directory.

## Requirements

- python 3.12 or higher

## Installation

Clone the repository:

```bash
git clone https://github.com/halon176/padel-api.git
```

now you have two options to install the service:

### Docker

```bash
docker build -t padel-api .
docker run -d -p 8000:8000 padel-api
```

### Manual

```bash
# Install dependencies (if using pip)
pip install -r requirements.txt

# OR install with Poetry (recommended)
poetry install

# Run the service
python3 run.py
```

**Note**: If dependencies have changed in `pyproject.toml`, regenerate `requirements.txt`:
```bash
poetry lock
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## Configuration

**IMPORTANT**: Before running the service, you must create a `.env` file with your configuration.

Copy the example configuration:
```bash
cp .env.example .env
```

Then edit `.env` and configure the following parameters:

```bash
SECRET_KEY=your-super-secret-key  # REQUIRED - Generate with: openssl rand -hex 32
ALGORITHM=HS256                    # Optional (default: HS256)
ACCESS_TOKEN_EXPIRE_MINUTES=60     # Optional (default: 60)
SERVICE_PORT=8000                  # Optional (default: 8000)
NOTIFICATIONS_URL=http://localhost:7777/v1/email_service  # Optional
```

**Security Note**: `SECRET_KEY` is **REQUIRED** and must be a strong random value. Never use weak values in production!

## Security Features

- **JWT Authentication**: Secure token-based authentication for protected endpoints
- **Rate Limiting**: Brute force protection on login (10 attempts/minute) and registration (5/minute)
- **CORS**: Cross-Origin Resource Sharing enabled (configure allowed origins in production)
- **Password Hashing**: Bcrypt for secure password storage

## API

API documentation is available at http://localhost:8000/docs

