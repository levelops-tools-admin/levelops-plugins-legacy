FROM python:3.8 as base

WORKDIR /app

# We copy just the requirements.txt first to leverage Docker cache
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --install-option="--prefix=/install" -r requirements.txt

FROM python:3.8-slim-buster

COPY --from=base /install /usr/local

COPY plugins/levelops-report_praetorian.py /app/plugins/
COPY plugins/levelops-report_ms_tmt.py /app/plugins/
COPY sdk /app/sdk
WORKDIR /app/plugins

ENTRYPOINT [ "python" ]
