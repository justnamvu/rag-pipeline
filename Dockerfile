# Stage 1: Build the React frontend, only exist to produce dist/
FROM node:20-slim AS frontend-builder

WORKDIR /frontend

# Install dependencies first, cached unless package.json changes
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build


# Stage 2: Install Python packages into a clean layer
FROM python:3.11-slim AS backend-builder

WORKDIR /build

COPY backend/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# System dependencies required by docling
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy install Python packages from builder stage
# This avoids re-running pip install in the final image
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages \
        /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application code
COPY backend/app ./app

# Copy compiled frontend from the frontend builder stage
COPY --from=frontend-builder /frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]