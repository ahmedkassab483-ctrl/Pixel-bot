import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters, CallbackQueryHandler
)

# ===== Settings =====
TOKEN = "9062363895:AAENhFnM84ZjBQNREXwqWrURLCOYzn07uO0"
OWNER_ID = 8643133848  # Your Telegram ID

MIN_BUDGET = 1000
MAX_BUDGET = 2500

# Conversation states
(CHOOSE_PACKAGE, CHOOSE_ADDONS, GET_NAME, GET_DETAILS, CONFIRM) = range(5)

logging.basicConfig(level=logging.INFO)

# ===== Packages =====
PACKAGES = {
    "🥉 Starter — $1000": {"price": 1000, "pages": "4 pages", "desc": "Responsive landing site + basic design + contact form"},
    "🥈 Professional — $1500": {"price": 1500, "pages": "7 pages", "desc": "Custom UI/UX design + basic SEO + fast loading"},
    "🥇 Business — $2000": {"price": 2000, "pages": "10 pages", "desc": "Full design + simple store + admin panel + payment integration"},
    "💎 Exclusive — $2500": {"price": 2500, "pages": "Unlimited", "desc": "Everything above + full branding + 3 months support + admin training"},
}

# ===== Add-ons =====
ADDONS = {
    "🌐 Domain + 1 year hosting": 150,
    "📝 Content writing": 200,
    "🔍 Advanced SEO": 250,
    "🎨 Professional logo": 150,
}

def main_menu():
    keyboard = [[KeyboardButton(p)] for p in PACKAGES.keys()]
    keyboard.append([KeyboardButton("📞 Contact the designer")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"Hello {user.first_name}! 👋\n"
        "I'm the *Pixel Design* assistant — professional website design.\n\n"
        f"💡 *Note:* Our prices range from *${MIN_BUDGET}* to *${MAX_BUDGET}*.\n\n"
        "Choose the package that fits you 👇"
    )
    await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")

# ===== Choose package =====
async def choose_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📞 Contact the designer":
        await update.message.reply_text("Direct contact: @YourUsername\nOr email: your@email.com", reply_markup=main_menu())
        return ConversationHandler.END

    if text not in PACKAGES:
        await update.message.reply_text(f"Please choose a package from the list 👇\n(Prices range from ${MIN_BUDGET} to ${MAX_BUDGET})", reply_markup=main_menu())
        return CHOOSE_PACKAGE

    context.user_data["package"] = text
    context.user_data["price"] = PACKAGES[text]["price"]
    context.user_data["addons"] = []

    p = PACKAGES[text]
    keyboard = [[InlineKeyboardButton(f"{k} (+${v})", callback_data=f"add_{k}")] for k, v in ADDONS.items()]
    keyboard.append([InlineKeyboardButton("✅ Continue without add-ons", callback_data="done")])

    await update.message.reply_text(
        f"You selected: *{text}*\n📄 Pages: {p['pages']}\n📝 {p['desc']}\n💰 Base price: *${p['price']}*\n\nWould you like any add-ons?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CHOOSE_ADDONS

# ===== Choose add-ons =====
async def choose_addons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        total = context.user_data["price"] + sum(ADDONS[a] for a in context.user_data["addons"])
        if total > MAX_BUDGET:
            await query.edit_message_text(f"⚠️ The total (${total}) exceeds the maximum of ${MAX_BUDGET}.\nPlease choose a cheaper package or fewer add-ons.")
            return CHOOSE_PACKAGE
        
        context.user_data["total"] = total
        await query.edit_message_text(f"💰 *Final total: ${total}*\n\nWhat is your full name?", parse_mode="Markdown")
        return GET_NAME

    if query.data == "back":
        await query.edit_message_text("Please choose a package from the menu 👇")
        return CHOOSE_PACKAGE

    addon_name = query.data.replace("add_", "")
    if addon_name in ADDONS and addon_name not in context.user_data["addons"]:
        context.user_data["addons"].append(addon_name)

    total = context.user_data["price"] + sum(ADDONS[a] for a in context.user_data["addons"])
    selected = "\n".join(f"✔️ {a}" for a in context.user_data["addons"]) or "None"

    keyboard = [[InlineKeyboardButton(f"{k} (+${v})", callback_data=f"add_{k}")] for k, v in ADDONS.items()]
    keyboard.append([InlineKeyboardButton("✅ Continue", callback_data="done")])

    await query.edit_message_text(
        f"Package: *{context.user_data['package']}*\nSelected add-ons:\n{selected}\n\n💰 Current total: *${total}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CHOOSE_ADDONS

# ===== Name & details =====
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Briefly describe your project (business type, preferred colors, references):")
    return GET_DETAILS

async def get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["details"] = update.message.text
    d = context.user_data

    summary = (
        f"📋 *Your order summary:*\n\n🔹 Package: {d['package']}\n➕ Add-ons: {', '.join(d['addons']) or 'None'}\n"
        f"💰 Total: *${d['total']}*\n👤 Name: {d['name']}\n📝 Details: {d['details']}\n\nIs everything correct?"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Confirm", callback_data="confirm")], [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])
    await update.message.reply_text(summary, reply_markup=keyboard, parse_mode="Markdown")
    return CONFIRM

# ===== Confirm =====
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("Cancelled. Start again with /start")
        return ConversationHandler.END

    d = context.user_data
    user = query.from_user
    owner_msg = (
        f"🔥 *New order — Pixel Design*\n\n🔹 Package: {d['package']}\n➕ Add-ons: {', '.join(d['addons']) or 'None'}\n"
        f"💰 Total: *${d['total']}*\n👤 Name: {d['name']}\n📝 Details: {d['details']}\n🆔 @{user.username or 'N/A'}"
    )
    await context.bot.send_message(chat_id=OWNER_ID, text=owner_msg, parse_mode="Markdown")
    await query.edit_message_text(f"✅ Your order has been received!\n💰 Total: *${d['total']}*\nThe designer will contact you within 24 hours.", parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=main_menu())
    return ConversationHandler.END

# ===== Run =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, choose_package)],
        states={
            CHOOSE_PACKAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_package)],
            CHOOSE_ADDONS: [CallbackQueryHandler(choose_addons)],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_details)],
            CONFIRM: [CallbackQueryHandler(confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    print("✅ Pixel Design Bot is running...")
    app.run_polling(
