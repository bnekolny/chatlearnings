FROM python:3.13-alpine

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["fastapi", "run", "./api.py", "--port=8080"]
