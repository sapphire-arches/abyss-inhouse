FROM python:3.9-slim-bullseye

RUN apt update
RUN apt install -y python3-psycopg2 && pip install 'psycopg2-binary==2.8.6'

WORKDIR /opt/apps/abyss-bot
COPY requirements.txt .
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "-u", "-m", "abyss_bot"]

COPY abyss_bot abyss_bot
