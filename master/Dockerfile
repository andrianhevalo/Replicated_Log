FROM python:3.8-alpine

RUN apk add --no-cache gcc musl-dev linux-headers libffi-dev g++

WORKDIR /master

ENV FLASK_APP=master.py
ENV FLASK_RUN_HOST=0.0.0.0

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY *.py .

CMD ["python", "master.py"]
