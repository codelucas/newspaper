FROM python:3.7-slim

RUN apt-get update && \
    apt-get -y install gcc git

RUN pip install --no-cache-dir flask uwsgi
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8080
CMD ["uwsgi", "./wsgi.ini"]
