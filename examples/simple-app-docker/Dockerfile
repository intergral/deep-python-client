FROM python:3.14.0a1-slim

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python",  "src/simple-app/main.py" ]
