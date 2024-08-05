# ���������� ����������� ����� PostgreSQL ��� �������
FROM postgres:13

# ������������� ����������� ������ ��� ������ ������� (��������, Python � ����������� ����������)
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# ������� ����������� ���������
RUN python3 -m venv /usr/src/app/venv

# ������������� Python ����������� � ����������� ���������
COPY requirements.txt /usr/src/app/requirements.txt
RUN /usr/src/app/venv/bin/pip install -r /usr/src/app/requirements.txt

# �������� ��� ������ � ���������
COPY main.py /usr/src/app/main.py

# ������������� ���������� ��������� ��� PostgreSQL
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword
ENV POSTGRES_DB=mydatabase

# ������� ����� ��� ������ PostgreSQL, ���� ��� �� �������
RUN mkdir -p /var/lib/postgresql/data

# ��������� ���� PostgreSQL
EXPOSE 5432

# ��������� PostgreSQL � ��� ������
CMD ["sh", "-c", "docker-entrypoint.sh postgres & /usr/src/app/venv/bin/python /usr/src/app/main.py"]