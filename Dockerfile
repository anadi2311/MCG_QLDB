
FROM ubuntu:20.04

RUN apt update -y && \
    apt install -y python3-pip 

WORKDIR /

COPY ./requirements.txt /requirements.txt

RUN pip3 install -r requirements.txt

COPY ./src /

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION
ARG AWS_SESSION_TOKEN

ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}\
    AWS_DEFAULT_REGION='us-west-2'


CMD [ "./script.sh"]

