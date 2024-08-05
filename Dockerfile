# Используем официальный образ PostgreSQL как базовый
FROM postgres:13

# Устанавливаем необходимые пакеты для вашего скрипта (например, Python и необходимые библиотеки)
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# Создаем виртуальное окружение
RUN python3 -m venv /usr/src/app/venv

# Устанавливаем Python зависимости в виртуальное окружение
COPY requirements.txt /usr/src/app/requirements.txt
RUN /usr/src/app/venv/bin/pip install -r /usr/src/app/requirements.txt

# Копируем ваш скрипт в контейнер
COPY main.py /usr/src/app/main.py

# Устанавливаем переменные окружения для PostgreSQL
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword
ENV POSTGRES_DB=mydatabase

# Создаем папку для данных PostgreSQL, если она не создана
RUN mkdir -p /var/lib/postgresql/data

# Открываем порт PostgreSQL
EXPOSE 5432

# Запускаем PostgreSQL и ваш скрипт
CMD ["sh", "-c", "docker-entrypoint.sh postgres & /usr/src/app/venv/bin/python /usr/src/app/main.py"]