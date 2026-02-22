FROM python:3.13-slim

# 1. تثبيت الحزم الأساسية + أدوات البناء (مهمة جداً لترجمة مكاتب التشفير)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    bash \
    curl \
    gcc \
    python3-dev \
    build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2. إعداد مجلد العمل ونسخ الملفات
COPY . /app/
WORKDIR /app/

# 3. تحديث pip لأحدث نسخة لبايثون 3.13
RUN pip install --no-cache-dir --upgrade pip

# 4. التثبيت الذكي (Smart Install): 
# السطر ده بيقرأ ملف المتطلبات سطر بسطر، ولو مكتبة فشلت (زي tgcrypto) بيكمل للي بعدها من غير ما يوقع الـ Build
RUN while read -r line || [ -n "$line" ]; do \
        pip install --no-cache-dir "$line" || echo "⚠️ Skipped: $line (Incompatible)"; \
    done < requirements.txt

# 5. أمر التشغيل الأساسي
CMD ["bash", "start"]
