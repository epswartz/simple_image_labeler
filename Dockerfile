FROM python:3.9.1

WORKDIR /app

COPY main.py /app/main.py
COPY static /app/static
COPY templates /app/templates
COPY Makefile /app/Makefile
COPY requirements.txt /app/requirements.txt

RUN make install
RUN mkdir csv

EXPOSE 5000
CMD ["python", "main.py", "--dir", "/images", "--csv", "csv/bboxes.csv"]
