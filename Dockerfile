FROM python:3.12-alpine
ADD . ./

RUN pip install -r requirements.txt
CMD python3 main.py