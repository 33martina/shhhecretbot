
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters
import re

TOKEN = "8024513443:AAHiK41BD_kSZZ5uKQtIWK0MthPqfrDIe1Y"

secret_messages = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Usa @shhhecretbot messaggio [@username] per inviare un messaggio segreto."
    )

def parse_command(text):
    pattern = r'^@shhhecretbot\s+(.+?)(?:\s+@(\w+))?$'
    match = re.match(pattern, text, re.IGNORECASE)
    if match:
        msg = match.group(1).strip()
        usertag = match.group(2)
        return msg, usertag
    return None, None

async def secret_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    msg, usertag = parse_command(text)
    if not msg:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    if usertag:
        new_text = f"🔒 Messaggio per @{usertag}, solo lui/lei potrà aprire il messaggio."
        keyboard = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("Mostra il messaggio 🔐", callback_data=f"show|{chat_id}|{message_id}|only|{usertag}")
        )
        secret_messages[(chat_id, message_id)] = {
            "text": msg,
            "mode": "only",
            "allowed_user": usertag,
            "sender_id": user.id,
            "opened_by": set(),
        }
        await update.message.edit_text(new_text, reply_markup=keyboard)
    else:
        new_text = "🔒 Messaggio segreto. Scegli come renderlo visibile:"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Solo il primo che apre", callback_data=f"mode|{chat_id}|{message_id}|first")],
            [InlineKeyboardButton("Tutti possono aprire", callback_data=f"mode|{chat_id}|{message_id}|all")]
        ])
        secret_messages[(chat_id, message_id)] = {
            "text": msg,
            "mode": None,
            "allowed_user": None,
            "sender_id": user.id,
            "opened_by": set(),
        }
        await update.message.edit_text(new_text, reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    action = data[0]
    chat_id = int(data[1])
    message_id = int(data[2])

    key = (chat_id, message_id)
    if key not in secret_messages:
        await query.edit_message_text("Messaggio scaduto o non trovato.")
        return

    msg_data = secret_messages[key]
    user = query.from_user

    if action == "mode":
        mode = data[3]
        msg_data["mode"] = mode

        if mode == "first":
            new_text = "🔒 Messaggio segreto. Solo il primo che cliccherà potrà aprire il messaggio."
        else:
            new_text = "🔒 Messaggio segreto. Tutti possono cliccare per aprire il messaggio."

        keyboard = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("Mostra il messaggio 🔐", callback_data=f"show|{chat_id}|{message_id}|{mode}")
        )
        await query.edit_message_text(new_text, reply_markup=keyboard)

    elif action == "show":
        mode = data[3]
        allowed_user = msg_data.get("allowed_user")
        sender_id = msg_data.get("sender_id")
        opened_by = msg_data.get("opened_by")

        can_view = False
        if user.id == sender_id:
            can_view = True
        else:
            if mode == "only":
                if user.username == allowed_user:
                    can_view = True
            elif mode == "first":
                if not opened_by:
                    opened_by.add(user.id)
                    can_view = True
                elif user.id in opened_by:
                    can_view = True
            elif mode == "all":
                can_view = True

        if can_view:
            text_to_show = f"🔓 Messaggio segreto:\n\n{msg_data['text']}"
            await query.edit_message_text(text_to_show)
        else:
            await query.answer("Non puoi vedere questo messaggio.", show_alert=True)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Comando non riconosciuto.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    pattern = re.compile(r'^@shhhecretbot', re.IGNORECASE)
    app.add_handler(MessageHandler(filters.Regex(pattern), secret_message_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    print("Bot avviato.")
    app.run_polling()

if __name__ == '__main__':
    main()
