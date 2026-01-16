import datetime
import time
from io import BytesIO
import redis
from gtts import gTTS
from Conf import Conf


def api_call(name: str, Messages):
    for m in Messages:
        hallvoice = m[1].replace("<name>", name)
        tts_cache = r.get(hallvoice + "fr")
        if tts_cache:
            print(f"[{datetime.datetime.now()}] TTS already in cache for: {hallvoice}")
        else:
            time.sleep(1)
            # Generate speech using gTTS and save to a BytesIO object
            tts = gTTS(text=hallvoice, lang="fr")
            # Create and write the TTS to a BytesIO
            mp3_fp = BytesIO()
            tts.write_to_fp(mp3_fp)
            # Convert the MP3 BytesIO object to WAV format in memory
            mp3_fp.seek(0)  # Reset the file pointer to the beginning
            print(f"[{datetime.datetime.now()}] TTS cached for: {hallvoice}")
            r.set(hallvoice + "fr", mp3_fp.read())


if __name__ == "__main__":
    conf = Conf("config.ini")
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    messagesTTSconf = conf.getWelcome() + conf.getGoodbye()
    with open("firstname.list", "r") as f:
        for line in f.readlines():
            # Func to get firstname and append to list
            api_call(line.strip(), messagesTTSconf)
