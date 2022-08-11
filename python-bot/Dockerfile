FROM python:3.10-slim-bullseye

WORKDIR /opt/apps/abyss-bot
COPY requirements.txt .
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "-u", "-m", "abyss-bot"]

COPY abyss-bot abyss-bot
