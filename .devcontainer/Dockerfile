FROM mcr.microsoft.com/devcontainers/python:3.11

WORKDIR /workspace

COPY ../requirements.txt /workspace/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /workspace/requirements.txt