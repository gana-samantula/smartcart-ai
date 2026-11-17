# Production-style image for the API. Not yet built or run: verify with `docker build ./backend`.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv/smartcart

RUN useradd --create-home --uid 10001 smartcart

COPY pyproject.toml ./
COPY app ./app
RUN pip install .

USER smartcart
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
