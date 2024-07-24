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
pip install -r requirements.txt
python3 run.py
```

## Configuration

It is possible configure following environment variables of .env file parameters:

```bash
SECRET_KEY=secret # secret key for JWT token
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
SERVICE_PORT=8000
NOTIFICATIONS_URL=http://localhost:8001 # url for notifications service
```

all parameters are optional, and have default build-in values. It is strongly recommended to change `SECRET_KEY` value
and `NOTIFICATIONS_URL` to the correct value.

## API

API documentation is available at http://localhost:8000/docs

