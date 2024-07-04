FROM python:3.12-slim
ADD . ./

RUN pip install -r requirements.txt
ENTRYPOINT ["python3", "main.py"]