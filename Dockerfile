FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

FROM nvidia/cuda:12.9.1-runtime-ubuntu24.04

WORKDIR /app

COPY --from=uv --chown=app:app /app/.venv /app/.venv
RUN .venv/bin/python -c "import easyocr; import numpy as np; print('Downloading and caching EasyOCR models for English and Thai...'); reader = easyocr.Reader(['en', 'th']); print('EasyOCR models downloaded successfully.'); dummy_image = np.zeros((100, 100, 3), dtype=np.uint8); reader.readtext(dummy_image); print('EasyOCR reader warmed up successfully.')"

# Install curl for health checks and Python
RUN apt-get update && apt-get install -y curl python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -s /usr/bin/python3 /usr/bin/python

ENV PATH="/app/.venv/bin:$PATH"
# Ensure unbuffered output for proper stdio communication
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port for HTTP server
EXPOSE 8080

RUN ls -la /app/.venv/bin

# Use exec form to ensure proper signal handling and stdio
# Default to HTTP server for cloud deployment
ENTRYPOINT ["python", "-u", "-m", "mcp_vision.http_server"]