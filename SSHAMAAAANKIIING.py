import logging
import random

import psycopg2
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, \
    CallbackQueryHandler

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s',
    level=logging.INFO
)

#Выдать роль
"""UPDATE users
SET role = 'Admin'
WHERE telegram_id = 5086271521;"""

logger = logging.getLogger(__name__)

# Токен Telegram
# TOKEN = '7377984448:AAENm-8FJ6wpDnOnoR4dcOuPZuncBD30Jd0'
TOKEN = '7477964182:AAGrsvu1z8BsfmBeeGrzUmZcCB6AUh2T2V0'
# Токен яндекс карт
api_key = 'fff13ee3-6829-41bc-ae41-d67b28b9f45f'
# Параметры подключения к базе данных
DB_NAME = 'mydatabase'
DB_USER = 'myuser'
DB_PASSWORD = 'mypassword'
DB_HOST = 'localhost'
DB_PORT = '5433'

# Константы состояний для ConversationHandler
# Константы состояний для ConversationHandler
NAME, SEX, AGE, CITY, DESCRIPTION, PHOTO, SONG, PREFERENCES, CONFIRM = range(9)

def create_tables():
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
        cursor.execute('CREATE TABLE IF NOT EXISTS users(' \
                       'id serial NOT NULL, ' \
                       'telegram_id bigint NOT NULL, ' \
                       'name character varying NOT NULL, ' \
                       'sex character varying NOT NULL, ' \
                       'age smallint NOT NULL, ' \
                       'city character varying NOT NULL, ' \
                       'description text, ' \
                       'photo text, ' \
                       'song text, ' \
                       'region character varying, ' \
                       'preferences character varying, ' \
                       'reports integer DEFAULT 0, ' \
                       'role character varying, ' \
                       'PRIMARY KEY (id));')

        conn.commit()

        cursor.execute('CREATE TABLE IF NOT EXISTS bans(' \
                       'id serial NOT NULL, ' \
                       'telegram_id bigint NOT NULL, ' \
                       'name character varying NOT NULL, ' \
                       'sex character varying NOT NULL, ' \
                       'age smallint NOT NULL, ' \
                       'city character varying NOT NULL, ' \
                       'description text, ' \
                       'photo text, ' \
                       'song text, ' \
                       'region character varying, ' \
                       'preferences character varying, ' \
                       'reports integer DEFAULT 0, ' \
                       'role character varying, ' \
                       'PRIMARY KEY (id));')

        conn.commit()
        
        # и таблицы likes
        cursor.execute('CREATE TABLE IF NOT EXISTS likes (\
                            id SERIAL PRIMARY KEY,\
                            liker_id BIGINT NOT NULL,\
                            liked_id BIGINT NOT NULL,\
                            UNIQUE(liker_id, liked_id));')

        conn.commit()

        cursor.execute('CREATE TABLE reports('
                       'rep_id serial NOT NULL,'
                       'reporter integer NOT NULL,'
                       'reported integer NOT NULL,'
                       'PRIMARY KEY (rep_id),'
                       'CONSTRAINT reporter FOREIGN KEY (reporter)'
                       'REFERENCES users (id) MATCH SIMPLE'
                       'ON UPDATE NO ACTION'
                       'ON DELETE NO ACTION'
                       'NOT VALID,'
                       'CONSTRAINT reported FOREIGN KEY (reported)'
                       'REFERENCES users (id) MATCH SIMPLE'
                       'ON UPDATE NO ACTION'
                       'ON DELETE NO ACTION'
                       'NOT VALID);')
        cursor.close()
        conn.close()
        logger.info("Все таблицы успешно созданы.")
        print('Все таблицы успешно созданы')
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
        print(f"Ошибка при подключении к базе данных: {e}")
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

def is_user_banned(telegram_id: int) -> bool:
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
        
        # Выполнение запроса для проверки, заблокирован ли пользователь
        cursor.execute(f'SELECT role FROM users WHERE id = {telegram_id}')
        is_banned = cursor.fetchone()[0] == 'Banned'
        
        # Закрытие соединения
        cursor.close()
        conn.close()
        
        return is_banned
    except Exception as e:
        logger.error(f"Ошибка при проверке бана: {e}")
        return False
    
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Проверка, находится ли пользователь в списке заблокированных
    if is_user_banned(user_id):  # Удален await
        await update.message.reply_text("Вы заблокированы и не можете создать анкету.")
        return ConversationHandler.END

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
async def save_data(user_id, name, sex, age, city, description, photo, song, region, preferences):
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
            "INSERT INTO users (telegram_id, name, sex, age, city, description, photo, song, region, preferences) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, name, sex, age, city, description, photo, song, region, preferences)
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
        # Инициализация profile_text
        profile_text = (
            f"Ваш профиль:\n\n"
            f"Имя: {user[2]}\n"
            f"Пол: {user[3]}\n"
            f"Возраст: {user[4]}\n"
            f"Город: {user[5]}\n"
            f"Описание: {user[6]}\n"
            f"Предпочтения: {user[10]}\n"
        )
        
        # Добавление роли, если она есть
        if user[12]:  # Предполагается, что роль находится в user[12]
            profile_text += f"Роль: {user[12]}\n"
            
        await update.message.reply_text(profile_text)
        
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
    await update.message.reply_text("Выберите ваш пол:",
                                    reply_markup=ReplyKeyboardMarkup([['Мужской', 'Женский']], one_time_keyboard=True))
    return SEX



async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    age = update.message.text
    if not age.isdigit() or not (16 <= int(age) <= 80):
        await update.message.reply_text("Возраст должен быть числом от 16 до 80. Попробуйте снова:")
        return AGE
    context.user_data['age'] = int(age)
    await update.message.reply_text("Введите ваш город (на русском языке):")
    return CITY

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


async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text
    geocoder_request = f'https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={city}&format=json'
    response = requests.get(geocoder_request)
    if response:
        json_response = response.json()
        toponym = json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
            'GeocoderMetaData']['Address']['Components']
        try:
            region, city = [x['name'] for x in toponym if x['kind'] in ['province', 'locality']][-2:]
        except:
            await update.message.reply_text(
                "Город должен быть на русском языке и содержать только буквы. Попробуйте снова:")
            return CITY
        context.user_data['city'] = city
        context.user_data['region'] = region
        await update.message.reply_text("Введите описание вашего профиля (на русском языке):")
        return DESCRIPTION
    else:
        await update.message.reply_text("Город должен быть на русском языке и содержать только буквы. Попробуйте снова:")
        return CITY

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
    await update.message.reply_text("Хотите добавить любимую песню? (да/нет)",
                                    reply_markup=ReplyKeyboardMarkup([['да', 'нет']], one_time_keyboard=True))
    return SONG

async def handle_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == 'да':
        await update.message.reply_text("Отправьте аудиофайл вашей любимой песни:")
        return CONFIRM
    else:
        context.user_data['song'] = None
        return await handle_preferences(update, context)

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'song' in context.user_data:
        context.user_data['song'] = update.message.audio.file_id
    return await handle_preferences(update, context)


async def handle_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    preferences = update.message.text
    
    # Проверка, выбраны ли кнопки с предпочтениями
    if preferences.lower() in ['Девушки', 'мужчины', 'нет предпочтений']:
        context.user_data['preferences'] = preferences
        # Переход к следующему этапу
        return await handle_confirmation(update, context)
    else:
        # Отправка сообщения с кнопками выбора предпочтений
        reply_markup = ReplyKeyboardMarkup(
            [['девушки', 'мужчины', 'девушки и мужчины']],
            one_time_keyboard=True
        )
        await update.message.reply_text(
            "Пожалуйста, выберите предпочтения по полу:",
            reply_markup=reply_markup
        )
        return PREFERENCES

async def handle_preferences_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    preferences = update.message.text.lower()
    if 'м' in preferences or 'п' in preferences:
        context.user_data['preferences'] = 'мужчины'
    elif 'ж' or 'д' in preferences:
        context.user_data['preferences'] = 'девушки'
    else:
        context.user_data['preferences'] = 'нет предпочтений'
    return PREFERENCES

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
        context.user_data['song'],
        context.user_data['region'],
        context.user_data.get('preferences', 'девушки и мужчины')  # Добавление предпочтений
    )
    profile = (
        f"Ваш профиль:\n\n"
        f"Имя: {context.user_data['name']}\n"
        f"Пол: {context.user_data['sex']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Город: {context.user_data['city']}, {context.user_data['region']}\n"
        f"Описание: {context.user_data['description']}\n"
        f"Предпочтения: {context.user_data.get('preferences', 'девушки и мужчины')}\n"
    )
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
        await update.message.reply_text(
            "Вы еще не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.")


async def delete_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = check_user_exists(user_id)
    if user:
        await delete_data(user_id)
        await update.message.reply_text("Ваш профиль был успешно удален.")
    else:
        await update.message.reply_text("Профиль не найден. Возможно, вы не были зарегистрированы.")


async def search_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_random_user(update)

    if user:
        profile_text = (
            f"Случайный профиль:\n\n"
            f"Имя: {user[2]}\n"
            f"Пол: {user[3]}\n"
            f"Возраст: {user[4]}\n"
            f"Город: {user[5]}\n"
            f"Описание: {user[6]}\n"
        )
        if user[12]:  # Предполагается, что роль находится в user[12]
            profile_text += f"Роль: {user[12]}\n"
            
        like_button = InlineKeyboardButton("👍 Лайк", callback_data=f"like:{user[1]}")
        dislike_button = InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike:{user[1]}")
        report_button = InlineKeyboardButton("🚩 Пожаловаться", callback_data=f"report:{user[1]}")
        keyboard = InlineKeyboardMarkup([[like_button, dislike_button, report_button]])

        # Отправляем фото с подписью и кнопками
        if user[7]:  # Фото
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=user[7],
                caption=profile_text[:1024],  # Telegram имеет ограничение на длину подписи в 1024 символа
                reply_markup=keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=profile_text,
                reply_markup=keyboard
            )

        if user[8]:  # Песня
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=user[8])

    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Не удалось найти пользователей.")


async def handle_like_dislike(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action, target_id = query.data.split(':')
    target_id = int(target_id)
    user_id = query.from_user.id

    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        if action == 'like':
            logger.info(f"Попытка поставить лайк: liker_id={user_id}, liked_id={target_id}")
            cursor.execute("INSERT INTO likes (liker_id, liked_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                           (user_id, target_id))
            conn.commit()
            logger.info("Лайк успешно записан.")

            cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
            liker_profile = cursor.fetchone()

            if liker_profile:
                liker_info = (
                    f"Вас лайкнул пользователь:\n\n"
                    f"Имя: {liker_profile[2]}\n"
                    f"Пол: {liker_profile[3]}\n"
                    f"Возраст: {liker_profile[4]}\n"
                    f"Город: {liker_profile[5]}\n"
                    f"Описание: {liker_profile[6]}\n"
                )
                like_button = InlineKeyboardButton("👍 Лайк", callback_data=f"like:{user_id}")
                dislike_button = InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike:{user_id}")
                report_button = InlineKeyboardButton("🚩 Пожаловаться", callback_data=f"report:{target_id}")
                keyboard = InlineKeyboardMarkup([[like_button, dislike_button, report_button]])

                await context.bot.send_message(chat_id=target_id, text=liker_info, reply_markup=keyboard)
                if liker_profile[7]:  # Фото
                    await context.bot.send_photo(chat_id=target_id, photo=liker_profile[7])
                if liker_profile[8]:  # Песня
                    await context.bot.send_audio(chat_id=target_id, audio=liker_profile[8])

            cursor.execute("SELECT * FROM likes WHERE liker_id = %s AND liked_id = %s", (target_id, user_id))
            mutual_like = cursor.fetchone()

            if mutual_like:
                user_link = f"https://web.telegram.org/a/#{user_id}"
                target_link = f"https://web.telegram.org/a/#{target_id}"
                await context.bot.send_message(chat_id=user_id,
                                               text=f"У вас взаимный лайк! Вот контакт вашего совпадения: {target_link}")
                await context.bot.send_message(chat_id=target_id,
                                               text=f"У вас взаимный лайк! Вот контакт вашего совпадения: {user_link}")
            else:
                # Изменяем текст только если он существует
                if query.message and query.message.text:
                    await query.edit_message_text(text="Вы поставили лайк этому профилю.")

        elif action == 'dislike':
            if query.message and query.message.text:
                await query.edit_message_text(text="Вы поставили дизлайк этому профилю.")

        elif action == 'report':
            reported_user_id = int(query.data.split(':')[1])
            logger.info(f"Попытка подать жалобу на пользователя: {reported_user_id}")
            cursor.execute(f'SELECT rep_id FROM reports WHERE reporter = {user_id} and reported = {reported_user_id}')
            prev = cursor.fetchall()
            if not prev:
                cursor.execute("UPDATE users SET reports = reports + 1 WHERE telegram_id = %s", (reported_user_id,))
                conn.commit()
                cursor.execute(f'INSERT INTO reports (reporter, reported) VALUES ({user_id}, {reported_user_id}')
                conn.commit()
                logger.info("Жалоба успешно записана.")
                if query.message and query.message.text:
                    await query.edit_message_text(text="Вы пожаловались на этот профиль. Мы рассмотрим ваш запрос.")
            else:
                await query.edit_message_text(text="Вы уже жаловались на этот профиль ранее.")


        else:
            if query.message and query.message.text:
                await query.edit_message_text(text="Неизвестное действие.")

        # Запускаем поиск нового профиля
        await context.bot.send_message(chat_id=user_id, text="Ищем новый профиль...")
        await search_profile(update, context)

    except Exception as e:
        logger.error(f"Ошибка при обработке действия: {e}")
        if query.message and query.message.text:
            await query.edit_message_text(text="Произошла ошибка при обработке вашего действия.")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_random_user(update: Update) -> dict:
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        user_id = update.effective_user.id

        # Получаем предпочтения, пол и возраст пользователя
        cursor.execute("SELECT preferences, sex, age FROM users WHERE telegram_id = %s", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            cursor.close()
            conn.close()
            return None

        user_preferences, user_sex, user_age = user_data
        age_min = max(16, user_age - 3)
        age_max = min(80, user_age + 3)

        # Определение фильтра по полу и предпочтениям
        if user_preferences.lower() == 'девушки':
            search_sex = 'Женский'
        elif user_preferences.lower() == 'мужчины':
            search_sex = 'Мужской'
        elif user_preferences.lower() == 'девушки и мужчины':
            search_sex = None
        else:
            search_sex = user_preferences.lower()

        # Поиск пользователей по городу
        cursor.execute("SELECT city FROM users WHERE telegram_id = %s", (user_id,))
        city_result = cursor.fetchone()
        
        if city_result:
            city = city_result[0]
            query = """
                SELECT * FROM users 
                WHERE city = %s 
                AND telegram_id != %s 
                AND telegram_id NOT IN (SELECT liked_id FROM likes WHERE liker_id = %s)
            """
            params = (city, user_id, user_id)
        else:
            # Поиск пользователей по региону
            cursor.execute("SELECT region FROM users WHERE telegram_id = %s", (user_id,))
            region_result = cursor.fetchone()
            
            if region_result:
                region = region_result[0]
                query = """
                    SELECT * FROM users 
                    WHERE region = %s 
                    AND telegram_id != %s 
                    AND telegram_id NOT IN (SELECT liked_id FROM likes WHERE liker_id = %s)
                """
                params = (region, user_id, user_id)
            else:
                # Поиск пользователей по всей базе
                query = """
                    SELECT * FROM users 
                    WHERE telegram_id != %s 
                    AND telegram_id NOT IN (SELECT liked_id FROM likes WHERE liker_id = %s)
                """
                params = (user_id, user_id)

        # Условие по полу
        if search_sex:
            query += " AND sex = %s"
            params += (search_sex,)

        # Условие по возрасту
        query += " AND age BETWEEN %s AND %s"
        params += (age_min, age_max)

        cursor.execute(query, params)
        matched_users = cursor.fetchall()

        if not matched_users:
            # Если не нашлось пользователей по городу или региону, ищем по всей базе
            query = """
                SELECT * FROM users 
                WHERE telegram_id != %s 
                AND telegram_id NOT IN (SELECT liked_id FROM likes WHERE liker_id = %s)
            """
            params = (user_id, user_id)

            # Условие по полу
            if search_sex:
                query += " AND sex = %s"
                params += (search_sex,)

            # Условие по возрасту
            query += " AND age BETWEEN %s AND %s"
            params += (age_min, age_max)

            cursor.execute(query, params)
            matched_users = cursor.fetchall()

        cursor.close()
        conn.close()

        if matched_users:
            return random.choice(matched_users)
        else:
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении случайного пользователя: {e}")
        return None


application = Application.builder().token(TOKEN).build()


# Определение обработчиков команд
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
        SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sex)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)],
        PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
        SONG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song)],
        PREFERENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_preferences_response)],
        CONFIRM: [MessageHandler(filters.AUDIO, handle_confirmation)]
    },
    fallbacks=[CommandHandler('start', start)]
)

application.add_handler(conv_handler)
application.add_handler(CommandHandler("myprofile", my_profile))
application.add_handler(CommandHandler("deleteprofile", delete_profile))
application.add_handler(CommandHandler("searchprofile", search_profile))
application.add_handler(CallbackQueryHandler(handle_like_dislike))

if __name__ == '__main__':
    create_tables()
    application.run_polling()
    
