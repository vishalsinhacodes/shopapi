# Step 1 - Choose base image
# python: 3.11-slim is Python 3.11 on a minimal Linux OS
FROM python:3.11-slim

# Step 2 - Set working directory inside container
# All commands after this run from /app
WORKDIR /app

# Step 3 - Copy requirements FIRST (Docker caching)
COPY requirements.txt .

# Step 4 - Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5 - Copy rest of the app
COPY . . 

# Step 6 - Tell Docker your app uses port 8000
EXPOSE 8000

# Step 7 - Command to run when container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]