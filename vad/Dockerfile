ARG BASE_REGISTRY=registry.redhat.io
ARG BASE_IMAGE=rhel9/python-311
ARG BASE_TAG=1-66.1720018730

FROM ${BASE_REGISTRY}/${BASE_IMAGE}:${BASE_TAG} as build

ADD requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
EXPOSE 7860
ENV VAD_SERVER_NAME="0.0.0.0"

WORKDIR /opt/app-root
COPY --chown=1001:0 vad/ /opt/app-root/vad/