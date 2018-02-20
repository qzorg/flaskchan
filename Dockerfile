FROM debian:latest
RUN apt-get update
RUN apt-get install -y libjpeg-dev zlib1g-dev python python-dev python-pip libtiff5-dev libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev git
RUN git clone https://github.com/qzorg/flaskchan.git
WORKDIR flaskchan
RUN pip install -r requirements.txt
EXPOSE 5000 5000
CMD python app.py

