FROM python:3.12-slim

COPY . /padel-api

WORKDIR /padel-api

RUN pip install -r requirements.txt

CMD python3 run.py
