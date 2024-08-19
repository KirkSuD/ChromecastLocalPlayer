FROM python:3.12

WORKDIR /usr/src/app/

# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt
RUN  \
    pip install --no-cache-dir \
        bottle==0.12.25 \
        pychromecast==14.0.1 \
        requests==2.32.3 \
        waitress==3.0.0

COPY . .

ENTRYPOINT [ "python", "./chromecast_control.py" ]
