FROM python:3.11.10-alpine3.20

WORKDIR /fastapi-task-manager

COPY ./requirements.txt /fastapi-task-manager/requirements.txt

# install psycopg2 dependencies for production usage.
# For development/testing purposes psycopg2-binary package is enough
#RUN apk update
#RUN apk add postgresql-dev gcc python3-dev musl-dev

RUN pip install --no-cache-dir --upgrade -r /fastapi-task-manager/requirements.txt

COPY . .

EXPOSE 8000

# CMD ["python", "main.py"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
