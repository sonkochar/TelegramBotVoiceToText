import os
import telebot
import tempfile
from pydub import AudioSegment
from speech_recognition import Recognizer, AudioFile
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqldb import add_user_to_db
import logging

logging.basicConfig(level=logging.ERROR, filename="bot_errors.log")

bot = telebot.TeleBot('*******')

recognizer = Recognizer()
user_languages = {}

user_language_selected = {}


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""
    chat_id = message.chat.id
    username = message.from_user.username or ""

    add_user_to_db(user_id, first_name, last_name, chat_id, username)

    bot.send_message(
        message.chat.id,
        '''<b>Voice→Text Converter Bot</b>\n
 Send your voice messages and get text instantly!\n
 <em>💡Make life easier with me</em>\n
 Choose your preferred language with /language\n
 <b>Note:</b><i>By default language is set to <b>English</b></i>\n
 What will you convert today?👀''',
        parse_mode="html"
    )


@bot.message_handler(commands=['language'])
def set_language(message):
    if message.chat.id in user_language_selected and user_language_selected[message.chat.id]:
        del user_languages[message.chat.id]
        del user_language_selected[message.chat.id]

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        InlineKeyboardButton("Russian 🇷🇺", callback_data="lang_ru"),
        InlineKeyboardButton("Armenian 🇦🇲", callback_data="lang_hy")
    )
    bot.send_message(message.chat.id, "Please choose your language:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def callback_language(call):
    if call.data == "lang_selected":
        bot.answer_callback_query(call.id, "Language has already been selected.")
        return

    language_map = {
        "lang_en": ("English", "en-US"),
        "lang_ru": ("Russian", "ru-RU"),
        "lang_hy": ("Armenian", "hy-AM")
    }

    language_name, language_code = language_map[call.data]

    user_languages[call.message.chat.id] = language_code
    user_language_selected[call.message.chat.id] = True

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(f"✔️ {language_name} selected", callback_data="lang_selected")
    )
    bot.edit_message_text(
        text=f"Language set to {language_name}!",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)



@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        if message.voice.file_size > 10_000_000:
            bot.reply_to(message, "Sorry, the voice message is too large to process.")
            return

        processing_message = bot.send_message(message.chat.id, "Processing your voice...")

        language = user_languages.get(message.chat.id, 'en-US')

        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            temp_file.write(downloaded_file)
            voice_file_path = temp_file.name


        audio = AudioSegment.from_ogg(voice_file_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wa8v") as temp_wav_file:
            audio.export(temp_wav_file, format="wav")
            wav_file_path = temp_wav_file.name

        with AudioFile(wav_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=language)


        bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)

        bot.reply_to(message, f"Transcribed Text: {text}")

        os.remove(voice_file_path)
        os.remove(wav_file_path)


    except Exception as e:
        logging.error(f"Error processing voice message: {e}")
        bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
        bot.reply_to(message,
                     "Sorry, something went wrong while processing your voice message. Please try again later.")



@bot.message_handler(content_types=['text'])
def handle_non_voice(message):
    bot.send_message(
        message.chat.id,
        '''Sorry, please try voice messages or select(change) /language😊'''
    )


bot.polling(non_stop=True)



