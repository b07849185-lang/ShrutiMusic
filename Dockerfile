FROM python:3.13-slim

# تثبيت الحزم الأساسية (FFmpeg لتشغيل الصوت، و Git لتحميل المكاتب من جيتهاب)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git bash curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# نسخ ملفات البوت
COPY . /app/
WORKDIR /app/

# تحديث أداة التثبيت (pip) وتثبيت المتطلبات
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# أمر التشغيل الأساسي
CMD ["bash", "start"]
