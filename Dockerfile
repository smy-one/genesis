# Use an official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose only one public port (Render requirement)
EXPOSE 8000

# Start FastAPI (Internal) and Streamlit (Public)
CMD ["bash", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port 8080 & streamlit run frontend/app.py --server.port 8000 --server.enableCORS false --server.enableXsrfProtection false"]
