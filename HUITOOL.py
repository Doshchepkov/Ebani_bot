from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import psycopg2
from main import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, ContextTypes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '7468745351:AAF9rCCQPDBLCMyajy0_LWwN7Vb5ztrdVwU'  # Your bot token

def dbconnect():
    """Connect to the PostgreSQL database."""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def ban(user_id):
    """Ban a user by setting their role to 'Banned' and reset their reports."""
    conn = dbconnect()
    cursor = conn.cursor()
    logger.info(f"Banning user with ID: {user_id}")
    cursor.execute("UPDATE users SET role = 'Banned', reports = 0 WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

def checkrole(user_id):
    """Check if the user is an admin."""
    conn = dbconnect()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (user_id,))
    role = cursor.fetchone()
    cursor.close()
    conn.close()
    return role and role[0] == 'Admin'

async def start(update, context):
    """Handle the /start command."""
    user_id = update.effective_user.id
    if not checkrole(user_id):
        await gfys(update)
    else:
        await update.message.reply_html(
            'Добро пожаловать в адинтул, о Великий. У нас из команд: \n'
            '/search - для просмотра анкет на бан; \n'
            '/admin - для выдачи статуса админа'
        )

async def gfys(update):
    """Send a message to users who are not admins."""
    await update.message.reply_text(
        'Это клуб для крутых и им пользуются только админы. \n'
        'Возвращайся, когда станешь достаточно хорош'
    )

async def search(update, context):
    """Search for profiles that need to be banned."""
    user_id = update.effective_user.id
    if not checkrole(user_id):
        await gfys(update)
        return

    conn = dbconnect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE reports > 0 AND role IS DISTINCT FROM 'Admin' AND role IS DISTINCT FROM 'Banned' ORDER BY reports DESC;"
    )
    profile = cursor.fetchone()
    cursor.close()
    conn.close()

    if profile is None:
        await update.message.reply_text('Больше нет подходящих анкет')
        return

    text = (
        f"id: {profile[1]} \nИмя: {profile[2]} \nПол: {profile[3]} \nВозраст: {profile[4]} \n"
        f"Город: {profile[5]}, {profile[9]} \nОписание: {profile[6]} \n"
        f"Предпочтение: {profile[10]} \nСтатус: {profile[11]}"
    )
    
    buttons = [
        [InlineKeyboardButton("Ban", callback_data=f"ban_{profile[0]}")],
        [InlineKeyboardButton("Skip", callback_data=f"skip_{profile[0]}")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if profile[7]:
        try:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=profile[7])
        except Exception as e:
            logger.error(f"Error sending photo: {e}")

    try:
        await update.message.reply_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error sending text message: {e}")

async def admin(update, context):
    """Prompt for user ID to make an admin."""
    await update.message.reply_text('Конечно, я могу выдать роль админа. Дайте мне ID этого счастливчика.')
    return 1

async def makeadmin(update, context):
    """Make a user an admin."""
    user_id = update.effective_user.id
    if not checkrole(user_id):
        await gfys(update)
        return

    given_id = update.message.text
    conn = dbconnect()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'Admin' WHERE telegram_id = %s", (given_id,))
    conn.commit()
    cursor.close()
    conn.close()
    await update.message.reply_text(f"User with ID {given_id} has been made an admin.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for banning or skipping users."""
    query = update.callback_query
    data = query.data
    user_id = int(data.split("_")[1])
    
    conn = dbconnect()
    cursor = conn.cursor()
    
    if data.startswith("ban_"):
        ban(user_id)
        await query.message.reply_text("User banned.")
        await search(update, context)
    elif data.startswith("skip_"):
        cursor.execute("UPDATE users SET reports = 0 WHERE id = %s", (user_id,))
        conn.commit()
        await search(update, context)
    
    cursor.close()
    conn.close()

async def reset(update, context):
    """Reset likes and dislikes tables."""
    conn = dbconnect()
    cursor = conn.cursor()
    cursor.execute('TRUNCATE TABLE likes')
    cursor.execute('TRUNCATE TABLE dislikes')
    conn.commit()
    cursor.close()
    conn.close()
    await update.message.reply_text('Таблицы успешно очищены')

def main():
    """Start the bot."""
    conv_id = ConversationHandler(
        entry_points=[CommandHandler('admin', admin)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, makeadmin)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
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
