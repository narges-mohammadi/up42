FROM python:3.11.6

WORKDIR /usr/src/app
COPY ./requirement.txt ./
RUN pip install -r "requirement.txt"







