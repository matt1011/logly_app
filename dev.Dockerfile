FROM python:3.7
RUN mkdir /code
ADD . /code/
RUN pip install --upgrade pip
RUN cd /code \
    && pip install -e /code \
    && pip install -r requirements.txt \
    && pip install -r dev.requirements.txt \
    && jupyter nbextension enable --py --sys-prefix widgetsnbextension
ENV TINI_VERSION v0.6.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini && \
    mkdir /etc/ssl/logly && \
    openssl req -new -newkey rsa:2048 -nodes -out /etc/ssl/logly/logly.csr \
        -keyout /etc/ssl/logly/logly.key \
        -subj "/C=US/ST=New york/L=Rochester/O=Optimax/OU=optimax/CN=logly" && \
    openssl x509 -req -days 365 \
        -in /etc/ssl/logly/logly.csr \
        -signkey /etc/ssl/logly/logly.key \
        -out /etc/ssl/logly/logly.crt
EXPOSE 8888 8787
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["jupyter", "notebook", \
    "--port=8888", "--no-browser", \
    "--ip=0.0.0.0", "--allow-root", \
    "--certfile=/etc/ssl/logly/logly.crt", \
    "--keyfile", "/etc/ssl/logly/logly.key"]