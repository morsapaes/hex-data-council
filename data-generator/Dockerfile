FROM python:3.8-slim

COPY requirements.txt .

RUN set -ex; \
  	pip install --no-cache-dir -r requirements.txt

ADD twitter_stream.py twitter_historical.py ./

CMD ["python", "-u", "./twitter_stream.py"]
