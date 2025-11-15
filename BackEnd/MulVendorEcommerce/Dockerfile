# Use Python with Windows compatibility
FROM python:3.9-windowsservercore-ltsc2019

WORKDIR /app

# Install system dependencies
RUN pip install --upgrade pip

# Handle Windows path issues
RUN setx /M PATH "%PATH%;C:\Python39\Scripts"

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Fix line endings (critical for Windows)
RUN find . -type f -name "*.py" -exec dos2unix {} \;

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=MulVendorEcommerce.settings

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]