FROM openjdk:11-jre-slim

# Install Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Python environment
ENV PYTHONUNBUFFERED=1
ENV PYSPARK_PYTHON=python3

# Install Spark
ENV SPARK_VERSION=3.4.1
ENV HADOOP_VERSION=3
RUN apt-get update && \
    apt-get install -y wget && \
    wget -q https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    tar -xzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    mv spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark && \
    rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz && \
    apt-get remove -y wget && \
    apt-get clean

ENV SPARK_HOME=/opt/spark
ENV PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

WORKDIR /app

# Copy requirements
COPY requirements-spark.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements-spark.txt

# Copy application code
COPY src/ ./src/

# Create logs directory
RUN mkdir -p /app/logs

# Expose Spark UI port
EXPOSE 4040 8090

# Run Spark application
CMD ["python3", "src/main.py"]