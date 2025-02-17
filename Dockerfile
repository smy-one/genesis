# Use an official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose only one port (8000) since Render only supports a single exposed port
EXPOSE 8000

# Start both FastAPI and Streamlit, forcing Streamlit to use port 8000
CMD ["bash", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8000 --server.enableCORS false --server.enableXsrfProtection false"]
