FROM python:3.12-slim

WORKDIR /app

# system deps kept minimal - httpx/motor don't need extra native libs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# worker dyno - no port to expose, this is a polling bot
CMD ["python", "main.py"]
