FROM python:3.10-bullseye
LABEL authors="ash"

RUN pip install pipenv
RUN apt-get update -qq && apt-get install ffmpeg -y

WORKDIR /app

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy

COPY main.py ./

VOLUME /app/input
VOLUME /app/output
VOLUME /app/removing_music.log

# cache model
ENTRYPOINT ["python3", "main.py"]