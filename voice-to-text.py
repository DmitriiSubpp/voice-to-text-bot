import requests
import speech_recognition as sr
import pickle
import subprocess
import os
import ffmpeg
import sys

instructions_ru = "Привет!\n\nЯ могу перевести голосовое сообщение в текст.\n\n" \
                  "Перешли мне голосовое сообщение и я покажу его содержание.\n" \
                  "Также ты можешь переслать несколько голосовых и я переведу их по очереди\n\n" \
                  "Чем дольше длится голосовое, тем дольше оно будет обрабатываться" \
                  "Если произошла ошибка, то необходимо отправить два сообщения подряд, первое нужно для калибровки бота после ошибки"

token = "TOKEN"
url = "https://api.telegram.org/bot{}".format(token)

offset = 0
commands = ['/author']
message_ids = []
chat_id = 0


def send_message(chat_id, reply_to, text):
    message_data = {'chat_id': chat_id, 'text': text, 'reply_to_message_id': reply_to}
    requests.get(url + '/sendMessage', data=message_data)


while True:
    # ==================================================================
    data = {'offset': offset, 'limit': 0, 'timeout': 0}
    updates = requests.get("https://api.telegram.org/bot{}/getUpdates".format(token), data=data)
    last_update = updates.json()['result']
    # ==================================================================
    for update in last_update:
        offset = update['update_id'] + 1
        print(update)

        if 'text' in update['message']:
            message = update['message']['text']
            message_id = update['message']['message_id']
            chat_id = update['message']['chat']['id']
            lang = update['message']['from']['language_code']

            if message == '/author':
                send_message(chat_id, message_id, 'Author: @Dmitry_subb')

            elif message == '/start' or message == '/help':
                send_message(chat_id, message_id, instructions_ru)

        if 'voice' in update['message']:

            try:
                chat_id = update['message']['chat']['id']
                message_id = update['message']['message_id']

                file_id = update['message']['voice']['file_id']
                voice_data = {'file_id': file_id}
                file = requests.post(url + '/getFile', data=voice_data).json()

                file_path = file['result']['file_path']
                voice = requests.get('https://api.telegram.org/file/bot{}/{}'.format(token, file_path))

                if update['message']['chat']['type'] == 'group':
                    opus = update['message']['from']['username'] + '.opus'
                    wav = update['message']['from']['username'] + '.wav'
                else:
                    opus = str(chat_id) + '.opus'
                    wav = str(chat_id) + '.wav'

                with open(opus, "wb") as file:
                    file.write(voice.content)

                process = subprocess.run(['ffmpeg', '-i', opus, wav])

                if not process.returncode:
                    r = sr.Recognizer()
                    voice = sr.AudioFile(wav)

                    with voice as source:
                        audio = r.record(source)
                        send_message(chat_id, message_id, r.recognize_google(audio, language='ru'))

                os.remove(wav)
                os.remove(opus)

            except Exception:
                chat_id = update['message']['chat']['id']
                message_id = update['message']['message_id']
                send_message(chat_id, message_id, "Что-то пошло не так ):")
                print("Error occurred in voice block: \n{}".format(sys.exc_info()[1]))
