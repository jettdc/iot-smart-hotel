FROM python:3.7.3

COPY /app /etc/usr/src/app

WORKDIR /etc/usr/src/app

RUN pip install requests Flask Flask-Cors mysql-connector-python

ENTRYPOINT ["python"]
CMD ["rmm_api.py"]