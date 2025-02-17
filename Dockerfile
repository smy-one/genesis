# Use an official Python image
FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose ports
EXPOSE 8000  # FastAPI
EXPOSE 8501  # Streamlit

# Run FastAPI & Streamlit together
CMD ["bash", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501 --server.enableCORS false --server.enableXsrfProtection false"]
