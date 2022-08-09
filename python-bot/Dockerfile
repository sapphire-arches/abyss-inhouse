FROM python:3.10-slim-bullseye

WORKDIR /opt/apps/abyss-bot
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY run.sh .
RUN chmod 755 run.sh

ENTRYPOINT ["./run.sh"]

COPY bot.py .
