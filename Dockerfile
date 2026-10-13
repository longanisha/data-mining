FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends default-jre-headless && rm -rf /var/lib/apt/lists/*
WORKDIR /project
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 SPARK_LOCAL_IP=127.0.0.1
CMD ["python", "src/run_pipeline.py"]
