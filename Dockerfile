FROM python:3.11-slim

WORKDIR /app

# Giữ Python output được in ra
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DOCKER_ENV=true

# Cài đặt các dependency
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn vào container
COPY . .

# Mở cổng cho FastAPI
EXPOSE 8000

# Tạo script khởi động
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Chạy migrations\n\
alembic upgrade head\n\
\n\
# Tạo super admin nếu chưa tồn tại\n\
python -m app.scripts.create_super_admin\n\
\n\
# Chạy ứng dụng\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload\n\
' > /app/entrypoint.sh \
&& chmod +x /app/entrypoint.sh

# Command để chạy ứng dụng
CMD ["/app/entrypoint.sh"] 