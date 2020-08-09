FROM python:3.7
RUN mkdir /code
ADD ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip \
    && cd /code \
    && pip install -r /code/requirements.txt \
    && rm -rf /code/requirements.txt

EXPOSE 8050
ADD . /code/

ENTRYPOINT python3 /code/logly/app.py