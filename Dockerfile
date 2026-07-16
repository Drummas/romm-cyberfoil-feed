FROM python:3.11-slim
WORKDIR /app
COPY cyberfoil.py .
RUN pip install flask requests
CMD ["python", "cyberfoil.py"]