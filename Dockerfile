FROM python:3

COPY docker_requirements.txt /docker_requirements.txt
RUN pip install -U pip && pip install -r /docker_requirements.txt

COPY nextrelease /nextrelease

RUN echo '#!/bin/sh -e\nPYTHONPATH=/ python -m nextrelease ci' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
