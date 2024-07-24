import logging
from datetime import datetime

import httpx

from src.config import settings
from src.controllers.models import User


async def send_notification(users: list[User], start: datetime, end: datetime):
    async with httpx.AsyncClient() as client:
        for user in users:
            subject = "Padel court reservation complited"
            body = f"Dear {user.username}, your reservation of padel court from {start} to {end} is confirmed"
            request = {"email": user.email, "subject": subject, "body": body}

            try:
                response = await client.post(settings.notifications_url, data=request)
                if response.status_code != 200:
                    logging.error(f"error sending notification: {response.text}")
            except Exception as e:
                logging.error(f"error sending notification: {e}")
