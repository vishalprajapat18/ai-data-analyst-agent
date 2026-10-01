# Pinned and slim: the same Python everywhere, with no extra OS packages to patch.
FROM python:3.13-slim

WORKDIR /app

# Dependencies first, on their own layer. Docker caches it, so editing your
# code does not reinstall every package on the next build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then the code, which changes far more often.
COPY app ./app

EXPOSE 8000

# 0.0.0.0, not 127.0.0.1 — see below.
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]