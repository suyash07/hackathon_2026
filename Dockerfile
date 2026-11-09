FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PORT=8080 HOME=/tmp
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
COPY src/ src/
ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION
# Non-root user by number, so the pod's runAsNonRoot check can verify it.
USER 1000
EXPOSE 8080
CMD ["sh", "-c", "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]
