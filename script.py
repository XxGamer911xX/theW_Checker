import os
import re
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Get the bot token from Render environment variables
TOKEN = os.getenv("TOKEN")

# Function to check if a WhatsApp invite link is valid
def is_valid_whatsapp_link(link):
    pattern = r"https:\/\/chat\.whatsapp\.com\/[a-zA-Z0-9]{22}"
    return bool(re.fullmatch(pattern, link))

# Function to process links, find duplicates, and categorize them
def process_links(text):
    lines = text.strip().split("\n")
    links_dict = {}
    duplicates = defaultdict(list)
    valid_links, invalid_links = 0, 0
    response = ""

    for i in range(1, len(lines), 2):
        number = lines[i - 1].strip()
        link = lines[i].strip()

        if is_valid_whatsapp_link(link):
            valid_links += 1
            if link in links_dict.values():
                existing_number = [key for key, val in links_dict.items() if val == link][0]
                duplicates[link].extend([existing_number, number])
            else:
                links_dict[number] = link
        else:
            invalid_links += 1
            response += f"❌ Invalid Link at {number}: {link}\n"

    response += f"\n🔍 Scan Summary:\n"
    response += f"✅ Valid Links: {valid_links}\n"
    response += f"❌ Invalid Links: {invalid_links}\n"

    if duplicates:
        response += f"⚠️ Duplicate Links: {len(duplicates)}\n\n📌 Duplicates Found:\n"
        for link, numbers in duplicates.items():
            unique_numbers = sorted(set(numbers))
            response += f" - Link {', '.join(unique_numbers)} are the same → {link}\n"
    else:
        response += "\n✅ No Duplicate Links Found."

    return response, valid_links, invalid_links, len(duplicates)

# Start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! Send me a list of WhatsApp invite links or upload a file.")

# Handle text messages
async def handle_text(update: Update, context: CallbackContext):
    user = update.message.from_user
    text = update.message.text
    response, valid_count, invalid_count, duplicate_count = process_links(text)
    await update.message.reply_text(response)

    print(f"📌 User: {user.first_name} (@{user.username}) scanned {valid_count} valid, {invalid_count} invalid, {duplicate_count} duplicate link(s)")

# Handle file uploads
async def handle_file(update: Update, context: CallbackContext):
    user = update.message.from_user
    file = await update.message.document.get_file()
    file_path = "links.txt"

    await file.download_to_drive(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    response, valid_count, invalid_count, duplicate_count = process_links(text)
    await update.message.reply_text(response)
    os.remove(file_path)

    print(f"📌 User: {user.first_name} (@{user.username}) scanned {valid_count} valid, {invalid_count} invalid, {duplicate_count} duplicate link(s) via file")

# Main function to start the bot
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
