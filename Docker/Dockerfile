FROM python:3.10
ENV DJANGO_ENV=${DJANGO_ENV} \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry:
  POETRY_VERSION=1.3.1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry'

# System deps:
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential \
    libxslt-dev libxml2-dev libpam-dev libedit-dev libhunspell-dev ffmpeg\
    libpoppler-cpp-dev pkg-config poppler-utils pandoc

WORKDIR /ai_home
COPY pyproject.toml poetry.lock /ai_home/

RUN pip install "poetry==$POETRY_VERSION" && poetry --version

# Install dependencies:
RUN poetry install
RUN python -c "import nltk; nltk.download('punkt')"
RUN python -c "import nltk; nltk.download('stopwords')"
