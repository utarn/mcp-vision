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

# Preload EasyOCR models during build to cache them in the image
RUN --mount=type=cache,target=/root/.cache/easyocr \
    python -c "
import easyocr
import numpy as np
print('Downloading and caching EasyOCR models for English and Thai...')
reader = easyocr.Reader(['en', 'th'])
print('EasyOCR models downloaded successfully.')
# Warm up the reader to ensure models are fully loaded
dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
reader.readtext(dummy_image)
print('EasyOCR reader warmed up successfully.')
"


FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=uv --chown=app:app /app/.venv /app/.venv
# Copy EasyOCR model cache
COPY --from=uv --chown=app:app /root/.cache/easyocr /root/.cache/easyocr

ENV PATH="/app/.venv/bin:$PATH"

RUN ls -la /app/.venv/bin

ENTRYPOINT ["mcp-vision"]