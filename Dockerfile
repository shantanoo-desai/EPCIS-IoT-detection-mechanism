FROM python:3

LABEL maintainer="Shan Desai<shantanoo.desai@gmail.com"

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

CMD ["python", "main.py"]