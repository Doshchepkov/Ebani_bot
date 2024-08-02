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

logger = logging.getLogger(__name__)

# Токен Telegram
# TOKEN = '7377984448:AAENm-8FJ6wpDnOnoR4dcOuPZuncBD30Jd0'
TOKEN = '7477964182:AAGrsvu1z8BsfmBeeGrzUmZcCB6AUh2T2V0'
api_key = 'fff13ee3-6829-41bc-ae41-d67b28b9f45f' # Токен яндекс карт
# Параметры подключения к базе данных
DB_NAME = 'mydatabase'
DB_USER = 'myuser'
DB_PASSWORD = 'mypassword'
DB_HOST = 'localhost'
DB_PORT = '5433'

# Константы состояний для ConversationHandler
NAME, SEX, AGE, CITY, DESCRIPTION, PHOTO, SONG, AUDIO, PREFERENCES, CONFIRM = range(10)

def dbconnect():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    return conn, cursor

def create_tables():
    try:
        conn, cur = dbconnect()
        # создание таблицы users
        cur.execute("CREATE TABLE IF NOT EXISTS preferences ("
                       "pref_id integer NOT NULL,"
                       "preference character varying(32) NOT NULL,"
                       "PRIMARY KEY (pref_id));")
        conn.commit()
        cur.execute('SELECT * FROM preferences')
        check = cur.fetchall()
        if not check:
            cur.execute("INSERT INTO preferences (pref_id, preference) VALUES (1, 'Мужчины')")
            conn.commit()
            cur.execute("INSERT INTO preferences (pref_id, preference) VALUES (2, 'Девушки')")
            conn.commit()
            cur.execute("INSERT INTO preferences (pref_id, preference) VALUES (3, 'Все')")
            conn.commit()

        cur.execute("CREATE TABLE IF NOT EXISTS roles ("
                       "role_id integer NOT NULL,"
                       "role character varying(8) NOT NULL,"
                       "PRIMARY KEY (role_id));")
        conn.commit()
        cur.execute('SELECT * FROM roles')
        check = cur.fetchall()
        if not check:
            cur.execute("INSERT INTO roles (role_id, role) VALUES (1, 'User')")
            conn.commit()
            cur.execute("INSERT INTO roles (role_id, role) VALUES (2, 'Admin')")
            conn.commit()
            cur.execute("INSERT INTO roles (role_id, role) VALUES (3, 'Banned')")
            conn.commit()
            cur.execute("INSERT INTO roles (role_id, role) VALUES (4, 'Premium')")
            conn.commit()


        cur.execute("CREATE TABLE IF NOT EXISTS users ("
                       "telegram_id bigint NOT NULL,"
                       "name character varying(16) NOT NULL,"
                       "sex character varying(8) NOT NULL,"
                       "age integer NOT NULL,"
                       "city character varying(32) NOT NULL,"
                       "description text,"
                       "photo text,"
                       "song text,"
                       "region character varying(32),"
                       "preferences integer DEFAULT 3,"
                       "reports integer DEFAULT 0,"
                       "role integer DEFAULT 1,"
                       "PRIMARY KEY (telegram_id),"
                       "CONSTRAINT preferences FOREIGN KEY (preferences)"
                       "REFERENCES preferences (pref_id)"
                       "NOT VALID,"
                       "CONSTRAINT roles FOREIGN KEY (role)"
                       "REFERENCES roles (role_id)"
                       "NOT VALID);")

        conn.commit()

        # таблицы likes
        cur.execute("CREATE TABLE IF NOT EXISTS likes ("
                    "like_id serial NOT NULL,"
                    "liker_id bigint,"
                    "liked_id bigint,"
                    "PRIMARY KEY (like_id),"
                    "CONSTRAINT liker_id FOREIGN KEY (liker_id)"
                    "REFERENCES users (telegram_id)"
                    "NOT VALID,"
                    "CONSTRAINT liked_id FOREIGN KEY (liked_id)"
                    "REFERENCES users (telegram_id) "
                    "NOT VALID);")
        conn.commit()

        cur.execute("CREATE TABLE IF NOT EXISTS dislikes ("
                    "dlike_id serial NOT NULL,"
                    "dliker_id bigint,"
                    "dliked_id bigint,"
                    "PRIMARY KEY (dlike_id),"
                    "CONSTRAINT dliker_id FOREIGN KEY (dliker_id)"
                    "REFERENCES users (telegram_id)"
                    "NOT VALID,"
                    "CONSTRAINT dliked_id FOREIGN KEY (dliked_id)"
                    "REFERENCES users (telegram_id) "
                    "NOT VALID);")
        conn.commit()

        # таблицы reports
        cur.execute("CREATE TABLE IF NOT EXISTS reports ("
                    "rep_id serial NOT NULL,"
                    "reporter bigint,"
                    "reported bigint,"
                    "PRIMARY KEY (rep_id),"
                    "CONSTRAINT reporter FOREIGN KEY (reporter)"
                    "REFERENCES users (telegram_id)"
                    "NOT VALID,"
                    "CONSTRAINT reported FOREIGN KEY (reported)"
                    "REFERENCES users (telegram_id) "
                    "NOT VALID);")
        conn.commit()

        cur.close()
        conn.close()
        logger.info("Все таблицы успешно созданы.")
        print('Все таблицы успешно созданы')
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")


def check_db_connection() -> str:
    try:
        # Проверяем соединение с базой данных
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        # Получаем количество пользователей в системе
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        conn.close()

        # Логируем успешное подключение
        logger.info(f"Подключение к базе данных успешно установлено. В системе {user_count} пользователя.")

        # Формируем сообщение
        return f"Приветствую! Подключение к базе данных успешно установлено. Количество пользователей в системе: {user_count}."
    except Exception as e:
        # Логируем ошибку
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


RULES_TEXT = "ыуу \n eea"


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Отправляем сообщение с правилами
    await update.message.reply_text(RULES_TEXT)


def is_user_banned(telegram_id: int) -> bool: 
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE telegram_id = %s', (telegram_id,))
        role = cursor.fetchone()
        cursor.close()
        conn.close()
        return role and role[0] == 3
    except Exception as e:
        logger.error(f"Ошибка при проверке бана: {e}")
        return False



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False) -> int:
    user_id = update.effective_user.id
    # Проверка, находится ли пользователь в списке заблокированных
    if is_user_banned(user_id):
        await update.message.reply_text("Вы заблокированы и не можете создать анкету.")
        return ConversationHandler.END
    db_status = check_db_connection()
    if not edit: # если профиль изменяется - не выводится текст о бд
        await update.message.reply_text(db_status)
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


def dbuid(id):  # возвращает id в бд по tg_id
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    cursor.execute(f'SELECT id FROM users WHERE telegram_id = {id}')
    return cursor.fetchone()[0]


# Удаление данных пользователя
async def delete_data(user_id: int):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Удаление связанных записей
        cursor.execute("DELETE FROM likes WHERE liker_id = %s OR liked_id = %s", (user_id, user_id))
        cursor.execute("DELETE FROM dislikes WHERE dliker_id = %s OR dliked_id = %s", (user_id, user_id))
        cursor.execute("DELETE FROM reports WHERE reporter = %s OR reported = %s", (user_id, user_id))

        # Удаление пользователя
        cursor.execute("DELETE FROM users WHERE telegram_id = %s", (user_id,))
        conn.commit()

        cursor.close()
        conn.close()
        logger.info("Данные пользователя успешно удалены.")
    except Exception as e:
        logger.error(f"Ошибка при удалении данных: {e}", exc_info=True)
        
def getpref(id):
    conn, cur = dbconnect()
    cur.execute(f'SELECT preference FROM preferences WHERE pref_id = {id}')
    return cur.fetchone()[0]

def getrole(id):
    conn, cur = dbconnect()
    cur.execute(f'SELECT role FROM roles WHERE role_id = {id}')
    return cur.fetchone()[0]

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=0):
    user_id = update.effective_user.id
    user = check_user_exists(user_id)

    pref = getpref(user[9])
    role = getrole(user[11])

    if user:
        # Формирование текста профиля
        profile_text = (
            f"Имя: {user[1]}\n"
            f"Пол: {user[2]}\n"
            f"Возраст: {user[3]}\n"
            f"Город: {user[4]}\n"
            f"Описание: {user[5]}\n"
            f"Предпочтения: {pref}\n"
        )


        # Добавление роли, если она есть
        if user[11] != 1:  # Предполагается, что роль находится в user[12]
            profile_text += f"Роль: {role}\n"

        # Отправляем фото с подписью
        if user[6]:  # Фото
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=user[6],
                caption=profile_text[:1024]  # Ограничение на длину подписи
            )
        else:
            # Если фото нет, отправляем текст
            await update.callback_query.message.edit_text(
                chat_id=update.effective_chat.id,
                text=profile_text
            )

        # Отправляем аудио отдельно
        if user[7]:  # Песня
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=user[7]
            )

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Профиль не найден. Пожалуйста, зарегистрируйтесь."
        )


async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=0):
    user_id = update.effective_user.id
    user = check_user_exists(user_id)
    if user:
        await delete_profile(update, context, edit=True)
        return await start(update, context, edit=True)


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
        try:
            toponym = \
                json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                    'GeocoderMetaData']['Address']['Components']
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
        await update.message.reply_text(
            "Город должен быть на русском языке и содержать только буквы. Попробуйте снова:")
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
        return AUDIO
    else:
        context.user_data['song'] = None
        return await handle_preferences(update, context)


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'song' in context.user_data:
        context.user_data['song'] = update.message.audio.file_id
    if 'song' not in context.user_data:
        context.user_data['song'] = update.message.audio.file_id if update.message.audio else None

    return await handle_preferences(update, context)


async def handle_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    preferences = update.message.text
    if preferences.lower() in ['девушки', 'мужчины', 'девушки и мужчины']:
        if preferences.lower() == 'мужчины':
            context.user_data['preferences'] = 1
        elif preferences.lower() == 'девушки':
            context.user_data['preferences'] = 2
        else:
            context.user_data['preferences'] = 3
        return await handle_confirmation(update, context)
    else:
        await update.message.reply_text(
            "Пожалуйста, укажите действительные предпочтения: 'девушки', 'мужчины', или 'девушки и мужчины'. Попробуйте снова:")
        return PREFERENCES


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        context.user_data.get('preferences', 3)  # Добавление предпочтений
    )
    pref = getpref(context.user_data.get('preferences', 3))
    profile = (
        f"Ваш профиль:\n\n"
        f"Имя: {context.user_data['name']}\n"
        f"Пол: {context.user_data['sex']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Город: {context.user_data['city']}, {context.user_data['region']}\n"
        f"Описание: {context.user_data['description']}\n"
        f"Предпочтения: {pref}\n"
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
        await update.message.reply_text(
            "Вы еще не зарегистрированы. Пожалуйста, используйте команду /start для регистрации.")


async def delete_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=0) -> None:
    user_id = update.effective_user.id
    if not is_user_banned(user_id):
        user_exists = check_user_exists(user_id)
        if user_exists:
            await delete_data(user_id)
            await update.message.reply_text("Ваш профиль был успешно удален.")
            if edit:
                await update.message.reply_text("Внесите изменения:")
        else:
            await update.message.reply_text("Профиль не найден. Возможно, вы не были зарегистрированы или ваше анкету обнулили.")
    else:
        await update.message.reply_text("Ваш профиль заблокирован и не может быть удален. Плати налог, упырь")


async def search_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = get_random_user(update)
    if not user:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Нет подходящих анкет')
        return 0
    print(user, is_user_banned(user_id))
    role = getrole(user[11])
    if user and not is_user_banned(user_id):
        profile_text = (
            f"Имя: {user[1]}\n"
            f"Пол: {user[2]}\n"
            f"Возраст: {user[3]}\n"
            f"Город: {user[4]}\n"
            f"Описание: {user[5]}\n"
        )
        if user[11] != 1:  # Предполагается, что роль находится в user[12]
            profile_text += f"Роль: {role}\n"

        like_button = InlineKeyboardButton("👍 Лайк", callback_data=f"like:{user[0]}")
        dislike_button = InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike:{user[0]}")
        report_button = InlineKeyboardButton("🚩 Пожаловаться", callback_data=f"report:{user[0]}")
        keyboard = InlineKeyboardMarkup([[like_button, dislike_button, report_button]])

        # Отправляем фото с подписью и кнопками
        if user[6]:  # Фото
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=user[6],
                caption=profile_text[:1024],  # Telegram имеет ограничение на длину подписи в 1024 символа
                reply_markup=keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=profile_text,
                reply_markup=keyboard
            )

        if user[7]:  # Песня
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=user[7])

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
        cursor.execute(f'SELECT like_id FROM likes where liker_id = {user_id} and liked_id = {target_id}')
        been = len(cursor.fetchall())
        if action == 'like' and not been:
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
                    f"Имя: {liker_profile[1]}\n"
                    f"Пол: {liker_profile[2]}\n"
                    f"Возраст: {liker_profile[3]}\n"
                    f"Город: {liker_profile[4]}\n"
                    f"Описание: {liker_profile[5]}\n"
                )
                like_button = InlineKeyboardButton("👍 Лайк", callback_data=f"like:{user_id}")
                dislike_button = InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike:{user_id}")
                report_button = InlineKeyboardButton("🚩 Пожаловаться", callback_data=f"report:{user_id}")
                keyboard = InlineKeyboardMarkup([[like_button, dislike_button, report_button]])

                await context.bot.send_message(chat_id=target_id, text=liker_info, reply_markup=keyboard)
                if liker_profile[6]:  # Фото
                    await context.bot.send_photo(chat_id=target_id, photo=liker_profile[6])
                if liker_profile[7]:  # Песня
                    await context.bot.send_audio(chat_id=target_id, audio=liker_profile[7])

            cursor.execute("SELECT * FROM likes WHERE liker_id = %s AND liked_id = %s", (target_id, user_id))
            mutual_like = cursor.fetchone()



            if mutual_like:
                # Получаем username для обоих пользователей
                user1 = await context.bot.get_chat(user_id)
                user2 = await context.bot.get_chat(target_id)
                user1_tag = f"@{user1.username}" if user1.username else f"пользователь {user_id}"
                user2_tag = f"@{user2.username}" if user2.username else f"пользователь {target_id}"

                await context.bot.send_message(chat_id=user_id,
                                               text=f"У вас взаимный лайк! Вот контакт вашего совпадения: {user2_tag}")
                await context.bot.send_message(chat_id=target_id,
                                               text=f"У вас взаимный лайк! Вот контакт вашего совпадения: {user1_tag}")
            else:
                if query.message and query.message.text:
                    await query.edit_message_text(text="Вы поставили лайк этому профилю.")

        elif action == 'dislike':
            logger.info(f"Попытка поставить дизлайк: dliker_id={user_id}, dliked_id={target_id}")
            cursor.execute("INSERT INTO dislikes (dliker_id, dliked_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                           (user_id, target_id))
            conn.commit()
            logger.info("Дизлайк успешно записан.")
            if query.message and query.message.text:
                await query.edit_message_text(text="Вы поставили дизлайк этому профилю.")

        elif action == 'report':
            reported_user_id = int(query.data.split(':')[1])
            logger.info(f"Обработка действия 'report': reported_user_id={reported_user_id}")

            # Проверка на предыдущие жалобы
            cursor.execute('SELECT rep_id FROM reports WHERE reporter = %s AND reported = %s', (user_id, reported_user_id))
            prev = cursor.fetchall()
            if not prev and not target_id == user_id:
                logger.info(f"Жалоба не найдена, добавляем новую: reporter_id={user_id}, reported_id={reported_user_id}")
                # Обновление колонки reports
                cursor.execute("UPDATE users SET reports = reports + 1 WHERE telegram_id = %s", (reported_user_id,))
                conn.commit()
                # Вставка новой жалобы
                cursor.execute('INSERT INTO reports (reporter, reported) VALUES (%s, %s)', (user_id, reported_user_id))
                conn.commit()
                logger.info("Жалоба успешно записана.")
                if query.message and query.message.text:
                    await query.edit_message_text(text="Вы пожаловались на этот профиль. Мы рассмотрим ваш запрос.")
            else:
                await query.edit_message_text(text="Вы уже жаловались на этот профиль ранее.")

        else:
            if query.message and query.message.text:
                await query.edit_message_text(text="Неизвестное действие.")

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
        age_min = max(16, user_age - 5)
        age_max = min(80, user_age + 5)

        # Определение фильтра по полу и предпочтениям
        if user_preferences == 2:
            search_sex = 'Женский'
        elif user_preferences == 1:
            search_sex = 'Мужской'
        elif user_preferences == 3:
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
                AND telegram_id NOT IN (SELECT dliked_id FROM dislikes WHERE dliker_id = %s)
                AND telegram_id NOT IN (SELECT reported FROM reports WHERE reporter = %s)
            """
            params = (city, user_id, user_id, user_id, user_id)
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
                    AND telegram_id NOT IN (SELECT dliked_id FROM dislikes WHERE dliker_id = %s)
                """
                params = (region, user_id, user_id, user_id)
            else:
                # Поиск пользователей по всей базе
                query = """
                    SELECT * FROM users 
                    WHERE telegram_id != %s 
                    AND telegram_id NOT IN (SELECT liked_id FROM likes WHERE liker_id = %s)
                    AND telegram_id NOT IN (SELECT dliked_id FROM dislikes WHERE dliker_id = %s)
                """
                params = (user_id, user_id, user_id)

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
                AND telegram_id NOT IN (SELECT dliked_id FROM dislikes WHERE dliker_id = %s)
            """
            params = (user_id, user_id, user_id)

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
        AUDIO: [MessageHandler(filters.AUDIO, handle_audio)],
        PREFERENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_preferences_response)],
        CONFIRM: [MessageHandler(filters.AUDIO, handle_confirmation)]
    },
    fallbacks=[CommandHandler('start', start)]
)

conv_editor = ConversationHandler(
    entry_points=[CommandHandler('editprofile', editprofile)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
        SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sex)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)],
        PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
        SONG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song)],
        AUDIO: [MessageHandler(filters.AUDIO, handle_audio)],
        PREFERENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_preferences_response)],
        CONFIRM: [MessageHandler(filters.AUDIO, handle_confirmation)]
    },
    fallbacks=[CommandHandler('editprofile', editprofile)]
)

application.add_handler(conv_handler)
application.add_handler(conv_editor)
application.add_handler(CommandHandler("myprofile", my_profile))
application.add_handler(CommandHandler("deleteprofile", delete_profile))
application.add_handler(CommandHandler("searchprofile", search_profile))
application.add_handler(CommandHandler("rules", rules))
application.add_handler(CallbackQueryHandler(handle_like_dislike))

if __name__ == '__main__':
    create_tables()
    application.run_polling()
