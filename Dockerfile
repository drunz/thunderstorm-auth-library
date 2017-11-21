FROM themattrix/tox

COPY thunderstorm_auth /src/thunderstorm_auth/
COPY test /src/test/
COPY Makefile .flake8 /src/
