FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY search_mcp ./search_mcp

ENV PORT=7879

EXPOSE 7879

CMD ["python", "-m", "search_mcp"]
