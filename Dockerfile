# The hosted JSON API (ADR-256).
#
# ⭐⭐ **One image, two runtime profiles.** Scale-to-zero and always-on differ by a platform setting, not by
# what is built here — which is the whole reason it is safe to start at zero and change one number later.
#
# ⚠️ **Slim, not alpine.** `psycopg[binary]` and `pulp` ship compiled wheels built against glibc; on musl
# they either fall back to a source build or fail outright. ⭐ *An image that is smaller because its wheels
# do not work is not smaller.*

FROM python:3.13-slim AS base

# ⭐ Bytecode written at build time, not on every cold start — the one thing that matters on a platform
# that keeps starting the process from scratch.
ENV PYTHONDONTWRITEBYTECODE=0 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ⚠️ Requirements first, and alone: this layer is cached until the file changes, so a source edit rebuilds
# in seconds rather than reinstalling 193 MB of wheels.
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# ⭐ Only what the API reads. The web app, the tests, the spikes and the committed sample data are all
# excluded — see .dockerignore, which is where that decision is actually enforced.
COPY src/ ./src/
COPY pyproject.toml ./

# ⚠️ **Non-root**, because an image that runs as root is one CVE away from mattering.
RUN useradd --create-home --shell /usr/sbin/nologin madboots
USER madboots

# ⭐ `$PORT` with a default: every host injects it, and a hard-coded port is the commonest first-deploy
# failure — the container starts, listens on the wrong number, and the platform reports it as unhealthy
# with no clue why.
ENV PORT=8080
EXPOSE 8080

# ⚠️ **No `--reload`.** It watches the filesystem, doubles the process count and serves stale code from a
# read-only layer — the opposite of every reason it exists in development.
#
# ⭐ One worker on purpose: the service is stateless and the platform scales by adding *instances*, so a
# second worker inside one container buys nothing and doubles the memory (87 MB measured, per worker).
CMD ["sh", "-c", "exec uvicorn src.service.http:app --host 0.0.0.0 --port ${PORT} --workers 1"]
