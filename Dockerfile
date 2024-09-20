FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /CanITrustIt

COPY NLP/model/ /CanITrustIt/NLP/model
COPY WebApp/ /CanITrustIt/WebApp
COPY requirements.txt /CanITrustIt/

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

WORKDIR /CanITrustIt/WebApp

CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app"]