import logging
import random

import psycopg2
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes, \
    ConversationHandler, \
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
api_key = 'fff13ee3-6829-41bc-ae41-d67b28b9f45f'  # Токен яндекс карт
# Параметры подключения к базе данных
DB_NAME = 'mydatabase'
DB_USER = 'myuser'
DB_PASSWORD = 'mypassword'
DB_HOST = 'localhost'
DB_PORT = '5432'

import time

# Пауза на 10 секунд
time.sleep(2)


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Вызов функции для разбанивания пользователей
    unban_all_users()
    
    # Отправка сообщения пользователю, который вызвал команду
    await update.message.reply_text("Все пользователи с ролью 3 были разбанены.")
 
 

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Вызов функции для разбанивания пользователей
    ban_all_users()
    
    # Отправка сообщения пользователю, который вызвал команду
    await update.message.reply_text("Все пользователи с ролью 3 были забанены.")
    
       
def unban_all_users():
    try:
        conn = dbconnect()
        cursor = conn.cursor()
        
        # Выполняем обновление роли
        cursor.execute("UPDATE users SET role = %s WHERE role = %s", (1, 3))
        
        conn.commit()
        print("Все пользователи с ролью 3 были разбанены.")
    except Exception as e:
        logging.error(f"Ошибка при разбане пользователей: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def ban_all_users():
    try:
        conn = dbconnect()
        cursor = conn.cursor()
        
        # Выполняем обновление роли
        cursor.execute("UPDATE users SET role = %s WHERE role = %s", (3, 1))
        
        conn.commit()
        print("Все пользователи с ролью 3 были разбанены.")
    except Exception as e:
        logging.error(f"Ошибка при разбане пользователей: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
            


def dbconnect3():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        return None




def is_admin(user_id: int) -> bool:
    conn = None
    cursor = None
    try:
        conn = dbconnect3()
        if conn is None:
            return False

        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (user_id,))
        result = cursor.fetchone()

        return result and result[0] == 2  # Предполагается, что роль админа имеет значение 2
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


async def text_handler(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    if 'waiting_for_text' in user_data:
        print(user_data)
        user_data['text'] = update.message.text
        user_data['waiting_for_text'] = False
        await update.message.reply_text("Отправьте фото для рассылки:")


async def photo_handler1(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    print(update.message)
    if 'waiting_for_text' in user_data:
        print("AAAAAAASASSA")
        if update.message.photo:
            user_data['photo'] = update.message.photo[-1].file_id
            user_data['text'] = update.message.caption
            await update.message.reply_text("Рассылка началась...")
            photo = user_data.get('photo')
            text = user_data.get('text')

            conn = dbconnect3()
            if conn is None:
                await update.message.reply_text("Не удалось подключиться к базе данных.")
                return

            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id FROM users WHERE role !=3")
            user_ids = cursor.fetchall()

            for (user_id,) in user_ids:
                try:
                    await context.bot.send_photo(chat_id=user_id, photo=photo, caption=text)
                except Exception as e:
                    logger.error(f"Failed to send message to {user_id}: {e}")
                    print("AAAAASSASAASAS")

            await update.message.reply_text("Рассылка завершена.")
            cursor.close()
            conn.close()


async def broadcast(update: Update, context: CallbackContext) -> None:
    id = update.effective_user.id
    if not checkrole(id):
        return await gfys(update)

    # Запрос текста для рассылки
    await update.message.reply_text("Введите текст для рассылки:")

    # Установка флага для ожидания следующего сообщения
    context.user_data['waiting_for_text'] = True

    # Добавление обработчиков сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler1))

    await update.message.reply_text("Ожидание текста и фото...")

def ban(id):
    conn = dbconnect()
    cursor = conn.cursor()
    print(id)
    cursor.execute(f"UPDATE users SET role = 3 WHERE telegram_id = {id}")
    conn.commit()
    cursor.execute(f"UPDATE users SET reports = 0 WHERE telegram_id = {id}")
    conn.commit()
    conn.close()
    cursor.close()


def checkrole(id):  # проверка на админа
    conn = dbconnect()
    cursor = conn.cursor()
    cursor.execute(f'SELECT role FROM users WHERE telegram_id = {id}')
    role = cursor.fetchone()[0]
    conn.close()
    cursor.close()
    if role == 2:
        return True
    return False


async def adminstart(update, context):  # приветствие
    conn = dbconnect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = 2 WHERE telegram_id = 1057741026")
    conn.commit()
    cur.execute("UPDATE users SET role = 2 WHERE telegram_id = 1268851631")
    conn.commit()
    cur.execute("UPDATE users SET role = 2 WHERE telegram_id = 5086271521")
    conn.commit()
    user_id = update.effective_user.id
    if not checkrole(user_id):
        return await gfys(update)

    else:
        await update.message.reply_html('Добро пожаловать в адинтул, о Великий. У нас из комманд: \n /adminsearch - для '
                                        'просмотра анкет на бан; \n /admin - для выдачи статуса админа,\n /reset - сброс истории событий,\n /recover - разбан по id,\n /broadcast - реклама \n /totalunban - разбан всем \n /totalban - бан всем, кто не админ')


async def gfys(update):  # функция посылания нахуй
    await update.message.reply_text('Это клуб для крутых и им пользутся только админы. \nВозвращайся, когда '
                                    'станешь достаточно хорош')


async def adminsearch(update, context):
    id = update.effective_user.id
    # подбор анкет на бан, надо бы сделать кнопки [бан] [следующий], Но я честно говоря, не ебу как
    if not checkrole(id):
        return await gfys(update)
    else:
        conn = dbconnect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE reports > 3 AND role <> 2 AND role <> 3 ORDER BY reports "
                    "DESC")
        profile = cur.fetchone()
        others = cur.fetchall()
        print(profile)
        try:
            print(profile[10])
            role = getrole(profile[11])
            pref = getpref(profile[9])
            text = f"id: {profile[0]} \nИмя: {profile[1]} \nПол: {profile[2]} \nВозраст: {profile[3]} \n" \
                   f"Город: {profile[4]}, {profile[8]} \n Описание: {profile[5]} \n" \
                   f"Предпочтение: {pref} \nСтатус: {role} \nЖалоб: {profile[10]}"
        except TypeError:
            try:
                await update.message.reply_text('Больше нет подходящих анкет')
            except AttributeError:
                await update.callback_query.message.edit_text('Больше нет подходящих анкет')
            return False
        buttons = [
            [InlineKeyboardButton("Ban", callback_data=f"ban:{profile[0]}")],
            [InlineKeyboardButton("Skip", callback_data=f"askip:{profile[0]}")]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        # query = update.callback_query
        if profile[6]:
            await context.bot.send_photo(chat_id=update.effective_chat.id, caption=text[:1024], photo=profile[6],
                                         reply_markup=keyboard)
        else:
            try:
                await update.message.reply_text(text, reply_markup=keyboard)
            except:
                await update.callback_query.message.edit_text(text, reply_markup=keyboard)
        if profile[7]:  # Песня
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=profile[7]
            )


async def admin(update, context):
    await update.message.reply_text('Конечно я могу выдать роль админа. Дайте мне id этоо счастливчка')
    return 1


async def makeadmin(update, context):
    user_id = update.effective_user.id
    if not checkrole(user_id):
        return await gfys(update)
    else:
        given_id = update.message.text
        conn = dbconnect()
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET role = 2 WHERE telegram_id = {given_id}")
        conn.commit()

async def banlist(update, context):
    user_id = update.effective_user.id
    if not checkrole(user_id):
        return await gfys(update)
    conn = dbconnect()
    cur = conn.cursor()
    cur.execute(f"SELECT telegram_id, name, city FROM users WHERE role = 3 ORDER BY telegram_id ASC")
    banned = cur.fetchall()
    text = 'Вот список забаненных юзеров\n'
    for i in banned:
        user1 = await context.bot.get_chat(i[0])
        user1_tag = f"@{user1.username}" if user1.username else f"пользователь {i[0]}"
        text += f'{i[0]}, {user1_tag}, {i[1]}, {i[2]}\n'
    return await update.message.reply_html(text)



async def getrecover(update, context):
    await update.message.reply_text('Я могу восстановить забаненного. Дайте мне id участника')
    return 1


async def recover(update, context):
    user_id = update.effective_user.id
    if not checkrole(user_id):
        return await gfys(update)
    else:
        given_id = update.message.text
        conn = dbconnect()
        cur = conn.cursor()
        if not checkrole(given_id):
            cur.execute(f"UPDATE users SET role = 1 WHERE telegram_id = {given_id}")
        conn.commit()


async def reset(update, context):
    user_id = update.effective_user.id
    if checkrole(user_id):
        conn = dbconnect()
        cur = conn.cursor()
        cur.execute('TRUNCATE TABLE likes')
        conn.commit()
        cur.execute('TRUNCATE TABLE dislikes')
        conn.commit()
        cur.execute('TRUNCATE TABLE reports')
        conn.commit()
        await update.message.reply_text('Таблицы успешно очищены')
    else: 
        await update.message.reply_text('Иди нахуй')


def main():
    global application
    conn = dbconnect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = 2 WHERE telegram_id = 1057741026")
    conn.commit()
    cur.execute("UPDATE users SET role = 2 WHERE telegram_id = 1268851631")
    conn.commit()
    conv_id = ConversationHandler(entry_points=[CommandHandler('admin', admin)],
                                  states={
                                      1: [MessageHandler(filters.TEXT & ~filters.COMMAND, makeadmin)]},
                                  fallbacks=[CommandHandler('adminstart', adminstart)])
    conv_rec = ConversationHandler(entry_points=[CommandHandler('recover', getrecover)],
                                   states={
                                       1: [MessageHandler(filters.TEXT & ~filters.COMMAND, recover)]},
                                   fallbacks=[CommandHandler('adminstart', adminstart)])
    application = Application.builder().token(TOKEN).build()
    application.add_handler(conv_id)
    application.add_handler(conv_rec)
    application.add_handler(CommandHandler("adminstart", adminstart))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("adminsearch", adminsearch))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("recover", getrecover))
    application.add_handler(CommandHandler("broadcast", broadcast))

    application.add_handler(conv_handler)
    application.add_handler(conv_editor)
    application.add_handler(CommandHandler("myprofile", my_profile))
    application.add_handler(CommandHandler("deleteprofile", delete_profile))
    application.add_handler(CommandHandler("searchprofile", search_profile))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("banlist", banlist))
    application.add_handler(CommandHandler("totalunban", unban_command))
    application.add_handler(CommandHandler("totalban", ban_command))
    application.add_handler(CallbackQueryHandler(handle_like_dislike))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()


# Константы состояний для ConversationHandler
NAME, SEX, AGE, CITY, DESCRIPTION, PHOTO, SONG, AUDIO, PREFERENCES, CONFIRM = range(10)


def dbconnect1():
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
        conn, cur = dbconnect1()
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
                    "content text,"
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


RULES_TEXT = " Бот принадлежит сообществу 'Мы знакомимся с худыми блэкаршами' https://t.me/metaldating\n \
Ознакомьтесь с пользовательским соглашением! https://t.me/c/2162958124/49 \n\n Простыми словами:\n\
1) Пользователь обязуется предоставлять достоверные и актуальные данные при регистрации и использовании Бота.\n\
2) Запрещено нарушать любые законы Российской Федерации (никакого экстризма, эротики, пропаганды). \n\
3) Пользователь использует Бот на свой страх и риск, мы не несем ответственности за любые убытки,\
возникшие в результате использования.\n\n\
Касаемо наших пожеланий к вам: смело и активно кидайте жалобы 🚩 на всех, кто нарушает правила сообщества. \n\
В том числе кидайте жалобы всем, кто здесь не по теме Бота! Мы обязательно будет банить.\n\
Уважайте друг друга!"


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
        await update.message.reply_text(
            "Вы заблокированы и не можете создать анкету. Бот для вас теперь платный. Если хотите разбан, пишите сюда: @Ebalteadm\n Этот бот вам пригодится: @userinfobot")
        return ConversationHandler.END
    db_status = check_db_connection()
    if not edit:  # если профиль изменяется - не выводится текст о бд
        await update.message.reply_text(db_status)
    user = check_user_exists(user_id)
    if user:
        await update.message.reply_text("Вы уже зарегистрированы. Вот ваша анкета:")
        await show_profile(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Введите ваше имя (слитно):")
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


def dbconnect():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT)


def getpref(id):
    conn, cur = dbconnect1()
    cur.execute(f'SELECT preference FROM preferences WHERE pref_id = {id}')
    return cur.fetchone()[0]


def getrole(id):
    conn, cur = dbconnect1()
    cur.execute(f'SELECT role FROM roles WHERE role_id = {id}')
    return cur.fetchone()[0]


def getpref1(id):
    conn, cur = dbconnect()
    cur.execute(f'SELECT preference FROM preferences WHERE pref_id = {id}')
    return cur.fetchone()[0]


def getrole1(id):
    conn, cur = dbconnect()
    cur.execute(f'SELECT role FROM roles WHERE role_id = {id}')
    return cur.fetchone()[0]


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=0, my=False):
    user_id = update.effective_user.id
    user = check_user_exists(user_id)

    pref = getpref(user[9])
    role = getrole(user[11])
    profile_text1 = ''
    if user:
        if not my:
            profile_text = ""
            if user[11] == 2:  # Предполагается, что роль находится в user[12]
                profile_text += f"\nAdmin★\n"
        # Формирование текста профиля
            profile_text1 = (
                f"{user[1]}, "

                f"{user[3]}, "
                f"{user[4]}, "
                f"{user[8]}\n"
                f"{user[5]}"
            )
        else:
            profile_text = (
                f"Ваши настройки:\n\n"
                f"Имя: {user[1]}\n"
                f"Пол: {user[2]}\n"
                f"Возраст: {user[3]}\n"
                f"Город: {user[4]}, {user[8]}\n"
                f"Предпочтения: {pref}\n"
                f"Жалоб: {user[10]}\n"
                f"Статус: {role}\n\n"
                f"Описание:\n{user[5]}\n"
            )


        profile_text = profile_text + profile_text1

        # Добавление роли, если она есть

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
        await update.message.reply_text("Введите ваше имя (слитно):")
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
    await update.message.reply_text("Введите ваш город (на русском языке):",reply_markup=ReplyKeyboardRemove())
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


import aiohttp

async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text
    await update.message.reply_text(city)

    geocoder_request = f'https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={city}&format=json'

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(geocoder_request) as response:
                if response.status == 200:
                    json_response = await response.json()
                    try:
                        toponym = json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                            'GeocoderMetaData']['Address']['Components']
                        region, city = [x['name'] for x in toponym if x['kind'] in ['province', 'locality']][-2:]
                    except Exception as e:
                        print(f"Ошибка при обработке ответа: {e}")
                        await update.message.reply_text(
                            "Город должен быть на русском языке и содержать только буквы. Попробуйте снова:")
                        return CITY

                    context.user_data['city'] = city
                    context.user_data['region'] = region
                    await update.message.reply_text("Введите описание вашего профиля:")
                    return DESCRIPTION
                else:
                    await update.message.reply_text(
                        "Город должен быть на русском языке и содержать только буквы. Попробуйте снова:")
                    return CITY
        except Exception as e:
            print(f"Ошибка при запросе: {e}")
            await update.message.reply_text(
                "Произошла ошибка при обработке запроса. Попробуйте снова:")
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
    await update.message.reply_text("Хотите добавить песню? Можно переслать из другого чата. (да/нет)",
                                    reply_markup=ReplyKeyboardMarkup([['да', 'нет']], one_time_keyboard=True))
    return SONG


async def handle_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() == 'да':
        await update.message.reply_text("Отправьте аудиофайл вашей песни:")
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
            
            
        await update.message.reply_text("Анкета заполнена!",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return await handle_confirmation(update, context)
    else:
        await update.message.reply_text(
            "Пожалуйста, укажите действительные предпочтения: 'девушки', 'мужчины', или 'девушки и мужчины'. Попробуйте снова:")
        return PREFERENCES


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Сохраняем данные пользователя
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

    # Формируем текст профиля
    pref = getpref(context.user_data.get('preferences', 3))
    profile_text = (
        f"Ваши настройки:\n\n"
        f"Имя: {context.user_data['name']}\n"
        f"Пол: {context.user_data['sex']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Город: {context.user_data['city']}, {context.user_data['region']}\n"
        f"Описание: {context.user_data['description']}\n"
        f"Предпочтения: {pref}\n"
    )

    # Отправляем текст с фото
    if context.user_data['photo']:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=context.user_data['photo'],
            caption=profile_text[:1024]  # Ограничение на длину подписи
        )
    else:
        # Если фото нет, просто отправляем текст
        await update.message.reply_text(profile_text, reply_markup=ReplyKeyboardRemove())

    # Отправляем аудио, если оно есть
    if context.user_data['song']:
        await context.bot.send_audio(
            chat_id=update.effective_chat.id,
            audio=context.user_data['song']
        )

    return ConversationHandler.END


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = check_user_exists(user_id)
    if user:
        await show_profile(update, context, my=True)
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
            await update.message.reply_text(
                "Профиль не найден. Возможно, вы не были зарегистрированы или ваше анкету обнулили.")
    else:
        await update.message.reply_text("Ваш профиль заблокирован и не может быть удален. Плати налог, упырь")


async def search_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = get_random_user(update)
    if not user:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Нет подходящих анкет. Измените критерии поиска или зайдите позже.')
            
        return 0
    print(user, is_user_banned(user_id))
    role = getrole(user[11])
    if user and not is_user_banned(user_id):
        profile_text = ""
        if user[11] == 2:  # Предполагается, что роль находится в user[12]
            profile_text += f"\nAdmin★\n"
        # Формирование текста профиля
        profile_text1 = (
            f"{user[1]}, "

            f"{user[3]}, "
            f"{user[4]}, "
            f"{user[8]}\n"
            f"{user[5]}"
        )
        profile_text = profile_text + profile_text1

        

        like_button = InlineKeyboardButton("🖤", callback_data=f"like:{user[0]}")
        message_button = InlineKeyboardButton("✉︎", callback_data=f"message:{user[0]}")
        dislike_button = InlineKeyboardButton("➔", callback_data=f"dislike:{user[0]}")
        report_button = InlineKeyboardButton("🚩", callback_data=f"report:{user[0]}")
        keyboard = InlineKeyboardMarkup([[like_button, message_button, dislike_button, report_button]])

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
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Не удалось найти пользователей. Измените критерии поиска или зайдите позже.")



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
        if (action == 'like' or action == 'message') and not been:
            if action == 'like':
                logger.info(f"Попытка поставить лайк: liker_id={user_id}, liked_id={target_id}")
                cursor.execute("INSERT INTO likes (liker_id, liked_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (user_id, target_id))
                conn.commit()
                logger.info("Лайк успешно записан.")

                cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
                liker_profile = cursor.fetchone()

                cursor.execute("SELECT * FROM likes WHERE liker_id = %s AND liked_id = %s", (target_id, user_id))
                mutual_like = cursor.fetchone()
            if action == 'message':
                logger.info(f"Попытка поставить лайк: liker_id={user_id}, liked_id={target_id}")
                cursor.execute("INSERT INTO likes (liker_id, liked_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (user_id, target_id))
                conn.commit()
                logger.info("Лайк успешно записан.")
                context.user_data['message_target'] = target_id
                # Запрашиваем у пользователя текст сообщения
                await query.message.reply_text("Пожалуйста, введите текст сообщения, который вы хотите отправить.")
                context.user_data['awaiting_message'] = True
                
      

            if mutual_like:

                # Получаем username для обоих пользователей
                user1 = await context.bot.get_chat(user_id)
                user2 = await context.bot.get_chat(target_id)
                user1_tag = f"@{user1.username}" if user1.username else f"пользователь {user_id}"
                user2_tag = f"@{user2.username}" if user2.username else f"пользователь {target_id}"

                # Получаем данные профилей
                cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
                user1 = cursor.fetchone()

                cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (target_id,))
                user2 = cursor.fetchone()

                user1_text1 = f"У вас взаимный лайк! Вот контакт вашего совпадения: {user1_tag}\n"
                if user1[11] == 2:
                    user1_text1 += "\nAdmin★\n"

                user1_text = (
                    f"{user1[1]}, "  # Имя
                    f"{user1[3]}, "  # Возраст
                    f"{user1[4]}, "  # Город
                    f"{user1[8]}\n"  # Регион
                    f"{user1[5]}\n"  # Описание

                )
                user1_text = user1_text1 + user1_text

                user2_text1 = f"У вас взаимный лайк! Вот контакт вашего совпадения: {user2_tag}\n"
                if user2[11] == 2:
                    user2_text1 += "\nAdmin★\n"

                user2_text = (
                    f"{user2[1]}, "  # Имя
                    f"{user2[3]}, "  # Возраст
                    f"{user2[4]}, "  # Город
                    f"{user2[8]}\n"  # Регион
                    f"{user2[5]}\n"  # Описание

                )
                user2_text = user2_text1 + user2_text

                # Отправляем полные анкеты и фото
                if user1[6]:  # Фото пользователя 1
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=user2[6],  # Фото пользователя 2
                        caption=user2_text[:1024]
                    )
                else:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=user2_text
                    )

                if user2[6]:  # Фото пользователя 2
                    await context.bot.send_photo(
                        chat_id=target_id,
                        photo=user1[6],  # Фото пользователя 1
                        caption=user1_text[:1024]
                    )
                else:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=user1_text
                    )
            elif liker_profile:
                liker_info = "Вас лайкнул\n"
                if liker_profile[11] == 2:  # Предполагается, что роль находится в user[12]
                    liker_info += f"\nAdmin★\n"
                # Формирование текста профиля
                liker_info1 = (
                    f"{liker_profile[1]}, "

                    f"{liker_profile[3]}, "
                    f"{liker_profile[4]}, "
                    f"{liker_profile[8]}\n"
                    f"{liker_profile[5]}"
                )
                liker_info = liker_info + liker_info1
                like_button = InlineKeyboardButton("🖤", callback_data=f"like:{user_id}")
                
                dislike_button = InlineKeyboardButton("➔", callback_data=f"dislike:{user_id}")
                report_button = InlineKeyboardButton("🚩", callback_data=f"report:{user_id}")
                keyboard = InlineKeyboardMarkup([[like_button, dislike_button, report_button]])

                if liker_profile[6]:  # Фото
                    await context.bot.send_photo(chat_id=target_id, photo=liker_profile[6], caption=liker_info[:1024],
                                                 reply_markup=keyboard)
                if liker_profile[7]:  # Песня
                    await context.bot.send_audio(chat_id=target_id, audio=liker_profile[7])
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
            cursor.execute('SELECT rep_id FROM reports WHERE reporter = %s AND reported = %s',
                           (user_id, reported_user_id))
            prev = cursor.fetchall()
            if not prev and not target_id == user_id:
                logger.info(
                    f"Жалоба не найдена, добавляем новую: reporter_id={user_id}, reported_id={reported_user_id}")
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
        elif action == 'ban':
            user_id = int(query.data.split(':')[1])
            ban(user_id)
            cursor.execute(f"UPDATE users SET reports = 0 WHERE telegram_id = {user_id}")
            conn.commit()
            await query.message.reply_text("User banned.")
            return await adminsearch(update, context)
        elif action == 'askip':
            user_id = int(query.data.split(':')[1])
            cursor.execute(f"UPDATE users SET reports = 0 WHERE telegram_id = {user_id}")
            conn.commit()
            return await adminsearch(update, context)

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get('awaiting_message'):
        return

    user_id = update.message.from_user.id
    target_id = context.user_data.get('message_target')
    message_text = update.message.text

    if not target_id:
        await update.message.reply_text("Ошибка: нет цели для сообщения.")
        return

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

        # Обновляем текст сообщения в базе данных
        cursor.execute(
            "UPDATE likes SET content = %s WHERE liker_id = %s AND liked_id = %s",
            (message_text, user_id, target_id)
        )
        conn.commit()

        # Получаем профиль лайкающего
        cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
        liker_profile = cursor.fetchone()

        # Формируем анкету
        liker_info = "Вас лайкнул\n"
        if liker_profile[11] == 2:  # Роль пользователя
            liker_info += "Admin★\n"

        liker_info1 = (
            f"{liker_profile[1]}, "
            f"{liker_profile[3]}, "
            f"{liker_profile[4]}, "
            f"{liker_profile[8]}\n"
            f"{liker_profile[5]}\n\n"
            f"Вам сообщение от пользователя: {message_text}"
            
        )
        liker_info = liker_info + liker_info1

        # Формируем кнопки
        like_button = InlineKeyboardButton("🖤", callback_data=f"like:{user_id}")
        dislike_button = InlineKeyboardButton("➔", callback_data=f"dislike:{user_id}")
        report_button = InlineKeyboardButton("🚩", callback_data=f"report:{user_id}")
        keyboard = InlineKeyboardMarkup([[like_button, dislike_button, report_button]])

        # Отправляем сообщение
        if liker_profile[6]:  # Фото
            await context.bot.send_photo(
                chat_id=target_id,
                photo=liker_profile[6],
                caption=liker_info[:1024],  # Ограничение длины текста
                reply_markup=keyboard
            )
        if liker_profile[7]:  # Песня
            await context.bot.send_audio(
                chat_id=target_id,
                audio=liker_profile[7]
            )

        # Уведомляем пользователя
        await update.message.reply_text("Ваше сообщение было отправлено.")

        # Вызываем функцию /search_profile
        await search_profile(update, context)

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        await update.message.reply_text("Произошла ошибка при отправке вашего сообщения.")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    # Удаляем флаги ожидания
    del context.user_data['awaiting_message']
    del context.user_data['message_target']

            
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
        
        
        age_min = max(((user_age//2) + 7), 16)
        age_max = min(((user_age - 7) * 2), 80)

        # Определение фильтра по полу и предпочтениям
        if user_preferences == 2:
            search_sex = 'Женский'
        elif user_preferences == 1:
            search_sex = 'Мужской'
        elif user_preferences == 3:
            search_sex = None
        else:
            search_sex = user_preferences.lower()
        if user_sex == 'Мужской':
            search_pref = 1
        else:
            search_pref = 2
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
                AND role != 3
                AND (preferences = %s OR preferences = 3)
            """
            params = (city, user_id, user_id, user_id, user_id, search_pref)
            if search_sex:
                query += " AND sex = %s"
                params += (search_sex,)

            # Условие по возрасту
            query += " AND age BETWEEN %s AND %s"
            params += (age_min, age_max)
            cursor.execute(query, params)

        matched_users = cursor.fetchall()

        print(matched_users)
        if not matched_users:
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
                                AND telegram_id NOT IN (SELECT reported FROM reports WHERE reporter = %s)
                                AND role != 3
                                AND (preferences = %s OR preferences = 3)
                            """
                params = (region, user_id, user_id, user_id, user_id, search_pref)
                if search_sex:
                    query += " AND sex = %s"
                    params += (search_sex,)

                # Условие по возрасту
                query += " AND age BETWEEN %s AND %s"
                params += (age_min, age_max)
                cursor.execute(query, params)
            matched_users = cursor.fetchall()
            print(matched_users)
        if not matched_users:
            query = """
                            SELECT * FROM users 
                            WHERE telegram_id != %s 
                            AND telegram_id NOT IN (SELECT liked_id FROM likes WHERE liker_id = %s)
                            AND telegram_id NOT IN (SELECT dliked_id FROM dislikes WHERE dliker_id = %s)
                            AND telegram_id NOT IN (SELECT reported FROM reports WHERE reporter = %s)
                            AND role != 3
                            AND (preferences = %s OR preferences = 3)
                        """
            params = (user_id, user_id, user_id, user_id, search_pref)
            if search_sex:
                query += " AND sex = %s"
                params += (search_sex,)

            # Условие по возрасту
            query += " AND age BETWEEN %s AND %s"
            params += (age_min, age_max)
            cursor.execute(query, params)
            matched_users = cursor.fetchall()
        # Условие по полу


        cursor.execute(query, params)
        matched_users = cursor.fetchall()

        print(*matched_users, sep='\n')

        cursor.close()
        conn.close()

        if matched_users:
            return random.choice(matched_users)
        else:
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении случайного пользователя: {e}")
        print(e)
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

if __name__ == '__main__':
    create_tables()
    main()