from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import psycopg2
from SSHAMAAAANKIIING import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, ContextTypes, show_profile

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
    if role == 'Admin':
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
        cur.execute("SELECT * FROM users WHERE reports > 3 AND role <> 'Admin' AND role <> 'Banned' ORDER BY reports "
                    "DESC")
        profile = cur.fetchone()
        others = cur.fetchall()
        print(profile)
        try:
            text = f"id: {profile[1]} \nИмя: {profile[2]} \nПол: {profile[3]} \nВозраст: {profile[4]} \n" \
                   f"Город: {profile[5]}, {profile[9]} \n Описание: {profile[6]} \n" \
                   f"Предпочтение: {profile[10]} \nСтатус: {profile[11]}"
        except TypeError:
            await update.message.reply_text('Больше нет подходящих анкет')
            return False
        buttons = [
            [InlineKeyboardButton("Ban", callback_data=f"ban_{profile[0]}")],
            [InlineKeyboardButton("Skip", callback_data=f"skip_{profile[0]}")]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        # query = update.callback_query
        if profile[7]:  # If there's a photo URL
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=profile[7])
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
        cur.execute(f"UPDATE users SET role = 'Admin' WHERE telegram_id = {given_id}")
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
        cursor.execute(f"UPDATE users SET reports = 0 WHERE id = {user_id}")
        conn.commit()
        await search(update, context)



def main():
    conv_id =  ConversationHandler(entry_points=[CommandHandler('admin', admin)],
                                   states={
                                       1: [MessageHandler(filters.TEXT & ~filters.COMMAND, makeadmin)]},
                                   fallbacks=[CommandHandler('start', start)])

    application = Application.builder().token(TOKEN).build()
    application.add_handler(conv_id)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == '__main__':
    main()