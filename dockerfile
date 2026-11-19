\# Stage 1: Build de dependencias Python
FROM python:3.11-slim AS builder

WORKDIR /app
RUN apt-get update &amp;&amp; apt-get install -y --no-install-recommends \\
build-essential \\
libpango-1.0-0 \\
libharfbuzz0b \\
libpangoft2-1.0-0 \\
libpangocairo-1.0-0 \\
libgdk-pixbuf-2.0-0 \\
libffi-dev \\
shared-mime-info \\
&amp;&amp; rm -rf /var/lib/apt/lists/\*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

\# Stage 2: Imagen final de ejecución
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update &amp;&amp; apt-get install -y --no-install-recommends \\
    libpango-1.0-0 \\
    libharfbuzz0b \\
    libpangoft2-1.0-0 \\ 
    libpangocairo-1.0-0 \\
    libgdk-pixbuf-2.0-0 \\
    shared-mime-info \\
    fonts-liberation \\ 
    &amp;&amp; rm -rf /var/lib/apt/lists/\*
COPY --from=builder /install /usr/local
COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]