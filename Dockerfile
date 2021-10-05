FROM python:3.9

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./ ./
WORKDIR /app/src

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
