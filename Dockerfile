# Docker file for a slim Ubuntu-based Python3 image

FROM selenium/standalone-chrome-debug:latest
LABEL maintainer="cooper@pobox.com"
USER root

# Needed for string substitution
SHELL ["/bin/bash", "-c"]

ARG USE_PYTHON_3_NOT_2=True
ARG _PY_SUFFIX=${USE_PYTHON_3_NOT_2:+3}
ARG PYTHON=python${_PY_SUFFIX}
ARG PIP=pip${_PY_SUFFIX}

# See http://bugs.python.org/issue19846
ENV LANG C.UTF-8

RUN apt-get update && apt-get install -y  ${PYTHON}-pip

RUN ${PIP} --no-cache-dir install --upgrade pip setuptools

# Some TF tools expect a "python" binary
RUN ln -s $(which ${PYTHON}) /usr/local/bin/python

COPY requirements.txt .
RUN ${PIP} --no-cache-dir install virtualenv
RUN ${PIP} --no-cache-dir install -r requirements.txt

COPY bashrc /etc/bash.bashrc
RUN chmod a+rwx /etc/bash.bashrc

#ENV TZ=UTC
#RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
#RUN apt-get install -y tzdata

EXPOSE 4444

WORKDIR /mnt
USER seluser

# Define default command.
CMD ["bash"]

