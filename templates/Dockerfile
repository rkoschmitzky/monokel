#Deriving the latest base image
FROM python:latest

WORKDIR .

COPY src/main.py config.py requirements.txt docker-compose.yml ./

RUN python3 -m venv /opt/venv
RUN . /opt/venv/bin/activate && pip install -r requirements.txt

CMD . /opt/venv/bin/activate && exec python /main.py