import re
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from collections import defaultdict

TOKEN = "8118348751:AAFnDTPuty8kL8Fe_d3uJX2-PDFYXkjXaio"  # Replace with your actual bot token

def is_valid_whatsapp_link(link):
    """Check if the given link follows the correct WhatsApp invite format."""
    pattern = r"https:\/\/chat\.whatsapp\.com\/[a-zA-Z0-9]{22}"
    return bool(re.fullmatch(pattern, link))

def process_links(text):
    """Reads, validates, and finds duplicates in WhatsApp links."""
    lines = text.strip().split("\n")
    links_dict = {}  # Stores {number: link}
    duplicates = defaultdict(list)  # Stores duplicate links {link: [numbers]}
    valid_links = 0
    invalid_links = 0
    response = ""

    for i in range(1, len(lines), 2):  # Assuming format: number → link
        number = lines[i - 1].strip()
        link = lines[i].strip()

        if is_valid_whatsapp_link(link):
            valid_links += 1
            if link in links_dict.values():
                existing_number = [key for key, val in links_dict.items() if val == link][0]
                duplicates[link].extend([existing_number, number])  # Track duplicate positions
            else:
                links_dict[number] = link
        else:
            invalid_links += 1
            response += f"❌ Invalid Link at {number}: {link}\n"

    # Prepare response
    response += f"\n🔍 Scan Summary:\n"
    response += f"✅ Valid Links: {valid_links}\n"
    response += f"❌ Invalid Links: {invalid_links}\n"
    
    if duplicates:
        response += f"⚠️ Duplicate Links: {len(duplicates)}\n\n"
        response += "📌 Duplicates Found:\n"
        for link, numbers in duplicates.items():
            unique_numbers = sorted(set(numbers))
            response += f" - Link {', '.join(unique_numbers)} are the same → {link}\n"
    else:
        response += "\n✅ No Duplicate Links Found."

    return response, valid_links, invalid_links, len(duplicates)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello! Send me a list of WhatsApp invite links or upload a file.")

async def handle_text(update: Update, context: CallbackContext):
    user = update.message.from_user
    text = update.message.text
    if text:
        response, valid_count, invalid_count, duplicate_count = process_links(text)
        await update.message.reply_text(response)
        
        # Print in console
        print(f"📌 User: {user.first_name} (@{user.username}) scanned {valid_count} valid, {invalid_count} invalid, {duplicate_count} duplicate link(s)")

async def handle_file(update: Update, context: CallbackContext):
    """Handles file uploads, reads content, and validates links."""
    user = update.message.from_user
    file = await update.message.document.get_file()
    file_path = "links.txt"

    await file.download_to_drive(file_path)  # Save the file
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    response, valid_count, invalid_count, duplicate_count = process_links(text)
    await update.message.reply_text(response)
    os.remove(file_path)  # Clean up

    # Print in console
    print(f"📌 User: {user.first_name} (@{user.username}) scanned {valid_count} valid, {invalid_count} invalid, {duplicate_count} duplicate link(s) via file")

def main():
    """Runs the Telegram bot using Application instead of Updater."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
