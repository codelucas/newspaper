#
# dockerfile-dev and dockerfile-prod common (try to keep this section identical)
#

FROM python:3.8

# Install dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        jq && \
    apt-get autoremove -y && \
    apt-get clean

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Create the User and app directory.
RUN useradd -ms /bin/bash newspaper
USER newspaper
ENV SRC_PATH=/
ENV APP_PATH=/home/newspaper/app
RUN mkdir -p ${APP_PATH}
WORKDIR ${APP_PATH}

# Configure Python.
ENV PYTHONPATH=${APP_PATH} \
    PYTHONUNBUFFERED=1

# Add local bin path to PATH
ENV BIN_PATH=/home/snewspaper/.local/bin
ENV PATH="${BIN_PATH}:${PATH}"

# Copy the current source file/directories to the app directory (will be shadowed after start).
COPY ${SRC_PATH} ${APP_PATH}

RUN pip install --user --no-cache-dir --compile --requirement ${APP_PATH}/requirements.txt
RUN python install_punkt.py
