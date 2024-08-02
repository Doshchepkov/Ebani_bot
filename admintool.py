from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import psycopg2
from SSHAMAAAANKIIING import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, ContextTypes, show_profile
from newdb import getrole, getpref
from REPORTS import getrole, getpref

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
    print(id)
    cursor.execute(f"UPDATE users SET role = 'Banned' WHERE id = {id}")
    conn.commit()
    cursor.execute(f"UPDATE users SET reports = 0 WHERE id = {id}")
    conn.commit()
    conn.close()
    cursor.close()


def checkrole(id): # проверка на админа
    conn = dbconnect()
    cursor = conn.cursor()
    cursor.execute(f'SELECT role FROM users WHERE telegram_id = {id}')
    role = cursor.fetchone()[0]
    conn.close()
    cursor.close()
    if role == 2:
        return True
    return False

async def start(update, context): # приветствие
    user_id = update.effective_user.id
    if not checkrole(user_id):
        await gfys(update)

    else:
        await update.message.reply_html('Добро пожаловать в адинтул, о Великий. У нас из комманд: \n /search - для '
                                        'просмотра анкет на бан; \n /admin - для выдачи статуса админа')

async def gfys(update): # функция посылания нахуй
    await update.message.reply_text('Это клуб для крутых и им пользутся только админы. \nВозвращайся, когда '
                                    'станешь достаточно хорош')

async def search(update, context):
    id = update.effective_user.id
    # подбор анкет на бан, надо бы сделать кнопки [бан] [следующий], Но я честно говоря, не ебу как
    if not checkrole(id):
        await gfys(update)
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
            [InlineKeyboardButton("Ban", callback_data=f"ban_{profile[0]}")],
            [InlineKeyboardButton("Skip", callback_data=f"skip_{profile[0]}")]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        # query = update.callback_query
        if profile[6]:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=profile[6])
        try:
            await update.message.reply_text(text, reply_markup=keyboard)
        except:
            await update.callback_query.message.edit_text(text, reply_markup=keyboard)








async def admin(update, context):
    await update.message.reply_text('Конечно я могу выдать роль админа. Дайте мне id этоо счастливчка')
    return 1

async def makeadmin(update, context):
    user_id = update.effective_user.id
    if not checkrole(user_id):
        await gfys(update)
    else:
        given_id = update.message.text
        conn = dbconnect()
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET role = 2 WHERE telegram_id = {given_id}")
        conn.commit()

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = int(data.split("_")[1])
    conn = dbconnect()
    cursor = conn.cursor()
    if data.startswith("ban_"):
        ban(user_id)
        cursor.execute(f"UPDATE users SET reports = 0 WHERE id = {user_id}")
        conn.commit()
        await query.message.reply_text("User banned.")
        await search(update, context)
    elif data.startswith("skip_"):
        cursor.execute(f"UPDATE users SET reports = 0 WHERE telegram_id = {user_id}")
        conn.commit()
        await search(update, context)

async def reset(update, context):
    conn = dbconnect()
    cur = conn.cursor()
    cur.execute('TRUNCATE TABLE likes')
    conn.commit()
    cur.execute('TRUNCATE TABLE dislikes')
    conn.commit()
    cur.execute('TRUNCATE TABLE reports')
    conn.commit()
    await update.message.reply_text('Таблицы успешно очищены')



def main():
    conn = dbconnect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = 2 WHERE telegram_id = 1057741026")
    conn.commit()
    cur.execute("UPDATE users SET role = 2 WHERE telegram_id = 1268851631")
    conn.commit()
    conv_id =  ConversationHandler(entry_points=[CommandHandler('admin', admin)],
                                   states={
                                       1: [MessageHandler(filters.TEXT & ~filters.COMMAND, makeadmin)]},
                                   fallbacks=[CommandHandler('start', start)])
    application = Application.builder().token(TOKEN).build()
    application.add_handler(conv_id)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == '__main__':
    main()