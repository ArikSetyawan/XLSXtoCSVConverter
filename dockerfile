FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port your Flask app will run on
EXPOSE 5000

# Use gunicorn as the production WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]