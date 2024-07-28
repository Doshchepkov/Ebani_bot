from telegram.ext import Application, MessageHandler, filters, CommandHandler
import logging
import psycopg2
from SSHAMAAAANKIIING import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, ContextTypes

TOKEN = '7468745351:AAF9rCCQPDBLCMyajy0_LWwN7Vb5ztrdVwU' # https://web.telegram.org/a/#7468745351 вот чат

def dbconnect():
    return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT)


conn = dbconnect()
cursor = conn.cursor()

def ban(id):
    conn = dbconnect()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET role = 'Banned' WHERE telegram_id = {id}")
    conn.commit()
    conn.close()
    cursor.close()


def checkrole(id): # проверка на админа
    conn = dbconnect()
    cursor = conn.cursor()
    cursor.execute(f'SELECT role FROM users WHERE telegram_id = {id}')
    role = cursor.fetchone()
    conn.close()
    cursor.close()
    if role == 'Admin':
        return True
    return False
async def start(update, context): # приветствие
    user_id = update.effective_user.id
    if not checkrole(user_id):
        gfys(update)
    else:
        await update.message.reply_html('Добро пожаловать в адинтул, о Великий. У нас из комманд: \n /search - для '
                                        'просмотра анкет на бан; \n /admin - для выдачи статуса админа')

def gfys(update): # функция посылания нахуй
    await update.message.reply_html('Это клуб для крутых и им пользутся только админы. \n Возвращайся, когда '
                                    'станешь достаточно хорош')

async def search(update, context, user_id):
    # подбор анкет на бан, надо бы сделать кнопки [бан] [следующий], Но я честно говоря, не ебу как
    if not checkrole(user_id):
        gfys(update)
    else:
        conn = dbconnect()
        cur = conn.cursor()
        cur.execute('SELECT id FROM users ORDER BY reports')
        qu = cur.fetchall()
        print(qu)

async def showprofile(id):
    conn = dbconnect()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM users WHERE telegram_id = {id}')
    info = cur.fetchone()
    print(info)

async def admin(update, context):
    user_id = update.effective_user.id
    if not checkrole(user_id):
        gfys(update)
    else:
        await update.message.reply_html('Конечно  могу выдать роль админа. Дайте мне id этоо счастливчка')
        given_id = update.message.text
        conn = dbconnect()
        cur = conn.cursor()
        cur.execute(f'UPDATE users SET role = "Admin" WHERE telegram_id = {given_id}')

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("search", admin))
    application.run_polling()


if __name__ == '__main__':
    main()