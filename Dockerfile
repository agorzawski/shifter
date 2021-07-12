FROM python:3.8-slim
LABEL maintainer="anders.harrisson@ess.eu"

RUN groupadd -r -g 1000 ops &&\
    useradd --no-log-init -r -g ops -u 1000 ops

RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN python -m venv /venv \
  && . /venv/bin/activate \
  && pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r /requirements.txt

COPY --chown=ops:ops . /app/

WORKDIR /app
ENV PATH /venv/bin:$PATH
EXPOSE 8000

CMD ["python", "/app/manage.py", "runserver", "0.0.0.0:8000"]
