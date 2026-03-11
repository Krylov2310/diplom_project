FROM python:3.13


WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt


COPY . .


CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]