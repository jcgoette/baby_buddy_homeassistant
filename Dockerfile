# Stage 1: Build dependencies
FROM python:3.11-slim AS build
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt requirements-test.txt ./
RUN python -m venv /venv && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install -r requirements.txt -r requirements-test.txt

# Stage 2: Production
FROM python:3.11-slim AS production
WORKDIR /app

COPY --from=build /venv /venv
COPY . .

ENV PATH="/venv/bin:$PATH"

EXPOSE 8000
CMD ["python", "src/main.py"]

