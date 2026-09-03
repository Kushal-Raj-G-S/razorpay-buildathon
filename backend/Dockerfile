# Slim, single-stage: this is a FastAPI service, not a build-heavy
# frontend, so there's nothing meaningful to multi-stage away.
FROM python:3.12-slim

WORKDIR /app

# psycopg2-binary needs libpq at runtime for the Postgres path; skip it
# entirely and you're stuck on SQLite inside the container.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite default lives here if DATABASE_URL isn't set to Postgres --
# named as a volume mount point so a container restart doesn't silently
# wipe it, same concern the in-memory-to-SQLite migration earlier in
# this project was about in the first place.
VOLUME ["/app/data"]
ENV DATABASE_URL=sqlite:///./data/warrant.db

EXPOSE 8000

# No reload, no --workers 1 debug assumptions -- this is meant to be run
# for real, not just demoed. Bump --workers if you actually need
# concurrency; SQLModel's engine is safe to share across them.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
