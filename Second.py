import psycopg2
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler
from telegram.ext import ContextTypes

TOKEN = '7377984448:AAENm-8FJ6wpDnOnoR4dcOuPZuncBD30Jd0'

# Параметры подключения к базе данных
DB_NAME = 'mydatabase'
DB_USER = 'myuser'
DB_PASSWORD = 'mypassword'
DB_HOST = 'localhost'
DB_PORT = '5433'

async def show_user_with_max_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Запрос на получение пользователя с максимальным количеством репортов
        cursor.execute("SELECT * FROM users ORDER BY reports DESC LIMIT 1")
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            # Формирование текста профиля
            profile_text = (
                f"Профиль пользователя:\n\n"
                f"Имя: {user[2]}\n"
                f"Пол: {user[3]}\n"
                f"Возраст: {user[4]}\n"
                f"Город: {user[5]}\n"
                f"Описание: {user[6]}\n"
            )
            if user[12]:  # Роль
                profile_text += f"Роль: {user[12]}\n"

            # Отправка текста профиля пользователю
            await context.bot.send_message(chat_id=update.effective_chat.id, text=profile_text)

            # Отправка фото, если оно есть
            if user[7]:  # Фото
                try:
                    photo_url = user[7]
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url)
                except Exception as e:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ошибка при отправке фото: {e}")

            # Отправка аудио, если оно есть
            if user[8]:  # Песня
                try:
                    audio_url = user[8]
                    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_url)
                except Exception as e:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ошибка при отправке аудио: {e}")

        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Пользователей в базе нет.")

    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ошибка: {e}")

def main():
    application = Application.builder().token(TOKEN).build()

    # Определение обработчиков команд
    application.add_handler(CommandHandler("showmaxreports", show_user_with_max_reports))

    application.run_polling()

if __name__ == '__main__':
    main()
