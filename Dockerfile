FROM python:3.13-slim

RUN apt-get update -qq && apt-get install -y -qq libimage-exiftool-perl git

WORKDIR /app
ENV PIP_ROOT_USER_ACTION=ignore

COPY requirements.txt /app/requirements.txt
COPY libs /app/libs
RUN pip install --upgrade pip &&  \
    pip install -r /app/requirements.txt &&  \
    pip install /app/libs/mongodb-markov && \
    pip install /app/libs/covid-19

COPY . /app

EXPOSE 8147
CMD python main.py 1>&2
