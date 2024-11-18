
FROM python:3.10-slim


WORKDIR /app


COPY . .


RUN pip install jinja2


EXPOSE 3000


CMD ["python", "main.py"]