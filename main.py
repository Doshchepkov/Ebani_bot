from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import psycopg2
import logging
import random
import requests


# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен Telegram
TOKEN = '7477964182:AAGrsvu1z8BsfmBeeGrzUmZcCB6AUh2T2V0'

api_key = 'fff13ee3-6829-41bc-ae41-d67b28b9f45f'

# Параметры подключения к базе данных
DB_NAME = 'mydatabase'
DB_USER = 'myuser'
DB_PASSWORD = 'mypassword'
DB_HOST = 'localhost'
DB_PORT = '5433'
MAPSTOK = '40d1649f-0493-4b7098ba-98533de7710b'



# Константы состояний для ConversationHandler
NAME, SEX, AGE, CITY, DESCRIPTION, PHOTO, SONG, CONFIRM = range(8)

def create_tables(): # литералли вырвал из старого кода, хз че не работает
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        # создание таблицы users
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, telegram_id BIGINT '
                       'UNIQUE NOT NULL, name VARCHAR(255) NOT NULL, sex VARCHAR(10) NOT NULL, age '
                       'INTEGER NOT NULL, city VARCHAR(255) NOT NULL, description TEXT, photo TEXT, '
                       'song TEXT);')
        conn.commit()
        # и таблицы likes
        cursor.execute('CREATE TABLE IF NOT EXISTS public."Likes" (id_like integer NOT NULL GENERATED ALWAYS AS '
                       'IDENTITY, sender integer NOT NULL, receiver integer, is_mutual boolean, '
                       'PRIMARY KEY (id_like), CONSTRAINT sender FOREIGN KEY (sender) REFERENCES '
                       'public.users (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT '
                       'VALID, CONSTRAINT receiver FOREIGN KEY (receiver) REFERENCES public.users '
                       '(id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID);')
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Все таблицы успешно созданы.")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")


def check_db_connection() -> str:
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.close()
        logger.info("Подключение к базе данных успешно установлено.")
        return "Подключение к базе данных успешно установлено. Код ответа: 200"
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        return f"Ошибка при подключении к базе данных: {e}"

def check_user_exists(user_id):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        logger.error(f"Ошибка при проверке пользователя: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Проверка подключения к базе данных
    db_status = check_db_connection()
    await update.message.reply_text(db_status)

    # Проверка, существует ли пользователь
    user = check_user_exists(user_id)
    if user:
        await update.message.reply_text("Вы уже зарегистрированы. Вот ваша анкета:")
        await show_profile(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Введите ваше имя (слитно, на русском):")
        return NAME

# Сохранение данных пользователя
async def save_data(user_id, name, sex, age, city, description, photo, song):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (telegram_id, name, sex, age, city, description, photo, song) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, name, sex, age, city, description, photo, song)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Данные пользователя успешно сохранены.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных: {e}")

# Удаление данных пользователя
async def delete_data(user_id):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE telegram_id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Данные пользователя успешно удалены.")
    except Exception as e:
        logger.error(f"Ошибка при удалении данных: {e}")

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = check_user_exists(user_id)
    if user:
        profile = (
            f"Ваш профиль:\n\n"
            f"Имя: {user[2]}\n"  # Проверьте правильность индексов
            f"Пол: {user[3]}\n"
            f"Возраст: {user[4]}\n"
            f"Город: {user[5]}\n"
            f"Описание: {user[6]}\n"
        )
        await update.message.reply_text(profile)
        if user[7]:  # Фото
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=user[7])
        if user[8]:  # Песня
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=user[8])
    else:
        await update.message.reply_text("Профиль не найден. Пожалуйста, зарегистрируйтесь.")

async def change_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user = check_user_exists(user_id)
    if user:
        await delete_data(user_id)
        await update.message.reply_text("Ваши данные удалены из базы. Пожалуйста, начните регистрацию заново.")
        await update.message.reply_text("Введите ваше имя (слитно, на русском):")
        return NAME
    else:
        await update.message.reply_text("Профиль не найден. Пожалуйста, зарегистрируйтесь.")
        return ConversationHandler.END

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text
    if not name.isalpha():  # Проверка на слитность и только алфавитные символы
        await update.message.reply_text("Имя должно быть слитным и содержать только буквы. Попробуйте снова:")
        return NAME
    context.user_data['name'] = name
    await update.message.reply_text("Выберите ваш пол:", reply_markup=ReplyKeyboardMarkup([['Мужской', 'Женский']], one_time_keyboard=True))
    return SEX

async def handle_sex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sex = update.message.text
    if 'м' in sex.lower():
        context.user_data['sex'] = 'Мужской'
    elif 'ж' in sex.lower():
        context.user_data['sex'] = 'Женский'
    else:
        await update.message.reply_text("Выберите пол из предложенных вариантов: Мужской или Женский.")
        return SEX
    await update.message.reply_text("Введите ваш возраст (от 16 до 80 лет):")
    return AGE

async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    age = update.message.text
    if not age.isdigit() or not (16 <= int(age) <= 80):
        await update.message.reply_text("Возраст должен быть числом от 16 до 80. Попробуйте снова:")
        return AGE
    context.user_data['age'] = int(age)
    await update.message.reply_text("Введите ваш город (на русском языке):")
    return CITY

async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text
    geocoder_request = f'https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={city}&format=json'
    response = requests.get(geocoder_request)
    if response:
        json_response = response.json()
        toponym = json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
            'GeocoderMetaData']['Address']['Components'][-1]['name']
        context.user_data['city'] = toponym
    else:
        await update.message.reply_text(
            "Город должен быть на русском языке и содержать только буквы. Попробуйте снова:")
        return CITY
    await update.message.reply_text("Введите описание вашего профиля (на русском языке):")
    return DESCRIPTION

async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = update.message.text
    if not description.strip():
        await update.message.reply_text("Описание не должно быть пустым. Попробуйте снова:")
        return DESCRIPTION
    context.user_data['description'] = description
    await update.message.reply_text("Загрузите ваше фото. Не размещайте запрещенный контент.")
    return PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo_file = update.message.photo[-1].file_id
    context.user_data['photo'] = photo_file
    await update.message.reply_text("Хотите добавить любимую песню? (да/нет)", reply_markup=ReplyKeyboardMarkup([['да', 'нет']], one_time_keyboard=True))
    return SONG

async def handle_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == 'да':
        await update.message.reply_text("Отправьте аудиофайл вашей любимой песни:")
        return CONFIRM
    else:
        context.user_data['song'] = None
        return await handle_confirmation(update, context)

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'song' not in context.user_data:
        context.user_data['song'] = update.message.audio.file_id if update.message.audio else None

    user_id = update.effective_user.id
    await save_data(
        user_id,
        context.user_data['name'],
        context.user_data['sex'],
        context.user_data['age'],
        context.user_data['city'],
        context.user_data['description'],
        context.user_data['photo'],
        context.user_data['song']
    )
    profile = (
        f"Ваш профиль:\n\n"
        f"Имя: {context.user_data['name']}\n"
        f"Пол: {context.user_data['sex']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Город: {context.user_data['city']}\n"
        f"Описание: {context.user_data['description']}\n"
    )

    await update.message.reply_text(profile, reply_markup=ReplyKeyboardRemove())
    if context.user_data['photo']:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=context.user_data['photo'])
    if context.user_data['song']:
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=context.user_data['song'])
    return ConversationHandler.END

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = check_user_exists(user_id)
    if user:
        await show_profile(update, context)
    else:
        await update.message.reply_text("Вы еще не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.")

async def delete_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = check_user_exists(user_id)
    if user:
        await delete_data(user_id)
        await update.message.reply_text("Ваш профиль был успешно удален.")
    else:
        await update.message.reply_text("Профиль не найден. Возможно, вы не были зарегистрированы.")
        


async def search_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_random_user()
    if user:
        profile = (
            f"Случайный профиль:\n\n"
            f"Имя: {user[2]}\n"
            f"Пол: {user[3]}\n"
            f"Возраст: {user[4]}\n"
            f"Город: {user[5]}\n"
            f"Описание: {user[6]}\n"
        )
        like_button = InlineKeyboardButton("👍 Лайк", callback_data=f"like:{user[1]}")
        dislike_button = InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike:{user[1]}")
        keyboard = InlineKeyboardMarkup([[like_button, dislike_button]])

        # Используем context.bot.send_message вместо update.message.reply_text
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=profile,
            reply_markup=keyboard
        )
        if user[7]:  # Фото
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=user[7])
        if user[8]:  # Песня
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=user[8])
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Не удалось найти пользователей.")
        
        
               
      
async def like_dislike_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = update.effective_user.id
    target_id = int(query.data.split(":")[1])

    if query.data.startswith("like"):
        await update_likes(user_id, target_id, True)
        await query.message.reply_text("👍 Вы поставили лайк!")
    elif query.data.startswith("dislike"):
        await update_likes(user_id, target_id, False)
        await query.message.reply_text("👎 Вы поставили дизлайк!")

    # Удаляем клавиатуру с кнопками лайка/дизлайка
    await query.message.edit_reply_markup(reply_markup=None)

    # Показываем следующий профиль
    await search_profile(update, context)

#ДО СЮДА ВСЕ ФУНКЦИИ РАБОТАЮТ ХОРОШО!!!!!!!!!!


async def update_likes(user_id, target_id, like):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Проверка, лайкнул ли целевой пользователь обратно
        cursor.execute("SELECT is_mutual FROM likes WHERE user_telegram_id = %s AND liked_user_telegram_id = %s", (target_id, user_id))
        mutual_like = cursor.fetchone()

        is_mutual = False
        if mutual_like and mutual_like[0]:  # Если целевой пользователь лайкнул и is_mutual True
            is_mutual = True

        # Обновление или вставка записи
        cursor.execute(
            "INSERT INTO likes (user_telegram_id, liked_user_telegram_id, is_mutual) VALUES (%s, %s, %s) "
            "ON CONFLICT (user_telegram_id, liked_user_telegram_id) DO UPDATE SET is_mutual = %s",
            (user_id, target_id, like, is_mutual)
        )

        conn.commit()
        cursor.close()
        conn.close()

        if is_mutual:
            await notify_mutual_like(user_id, target_id)
        elif like:  # Отправить уведомление только если это был лайк
            await notify_new_like(user_id, target_id)

    except Exception as e:
        logger.error(f"Ошибка при обновлении лайков: {e}")


async def notify_new_like(context, user_id, target_id):
    try:
        user_info = get_user_info(user_id)
        if user_info:
            message = f"Вы получили новый лайк от {user_info['name']}! Зайдите в приложение, чтобы посмотреть профиль и ответить."
            await context.bot.send_message(chat_id=target_id, text=message)
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о новом лайке: {e}")

async def notify_mutual_like(context, user_id, target_id):
    try:
        user_info = get_user_info(user_id)
        target_info = get_user_info(target_id)
        if user_info and target_info:
            message_user = f"У вас взаимный лайк с {target_info['name']}!"
            message_target = f"У вас взаимный лайк с {user_info['name']}!"
            await context.bot.send_message(chat_id=user_id, text=message_user)
            await context.bot.send_message(chat_id=target_id, text=message_target)
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о взаимном лайке: {e}")

def get_user_info(user_id):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE telegram_id = %s", (user_id,))
        user_info = cursor.fetchone()
        cursor.close()
        conn.close()
        if user_info:
            return {'name': user_info[0]}
        else:
            return None
    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе: {e}")
        return None

def get_random_user():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        if users:
            return random.choice(users)
        else:
            return None
    except Exception as e:
        logger.error(f"Ошибка при получении случайного пользователя: {e}")
        return None





def main():
    app = Application.builder().token(TOKEN).build()

    create_tables()
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sex)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)],
            SONG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song),
                MessageHandler(filters.AUDIO, handle_confirmation)
            ],
            CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirmation),
                MessageHandler(filters.AUDIO, handle_confirmation)
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    app.add_handler(conversation_handler)
    app.add_handler(CommandHandler('myprofile', my_profile))
    app.add_handler(CommandHandler('deleteprofile', delete_profile))
    app.add_handler(CommandHandler('changeprofile', change_profile))
    app.add_handler(CommandHandler('search', search_profile))
    app.add_handler(CallbackQueryHandler(like_dislike_callback))

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == '__main__':
    main()
