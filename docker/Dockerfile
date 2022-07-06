FROM python:3-slim

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y build-essential libldap2-dev libsasl2-dev python3-dev pip net-tools tcpdump
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
COPY . ./nodes_app
WORKDIR ./nodes_app
RUN pip install -r requirements.txt
RUN pip install uwsgi
RUN chmod +x boot.sh

EXPOSE 6699/tcp

ENTRYPOINT ["./boot.sh"]