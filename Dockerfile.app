# Slim Python base
FROM python:3.12-slim


# Install system deps (git for uv to resolve VCS packages if needed; curl to install uv)
RUN apt-get update && apt-get install -y --no-install-recommends \
git curl ca-certificates && \
rm -rf /var/lib/apt/lists/*


# Install uv (https://github.com/astral-sh/uv)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"


WORKDIR /app


# Copy only metadata first for better caching
COPY pyproject.toml ./


# Pre-resolve & cache wheels
RUN uv sync --frozen --no-install-project || true


# Copy source code
COPY src ./src


# Install project deps into the environment
RUN uv sync --no-dev


# Default command is set in docker-compose to run the scraper