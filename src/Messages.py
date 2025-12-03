import datetime
import os
import json
import subprocess
import tempfile
import redis
import threading
from io import BytesIO
from random import choice, randint
from gtts import gTTS, gTTSError

class Messages(object):
    _play_lock = threading.Lock()
    _play_timeout_sec = 10

    def __init__(self, conf, api) -> None:
        self.redis = redis.Redis(host=conf.getRedisHost(), port=conf.getRedisPort(), db=0)
        self.welcomeMsg: list[tuple[str, str]] = conf.getWelcome()
        self.goodbyeMsg: list[tuple[str, str]] = conf.getGoodbye()
        self.buildingName: str = conf.getBuilding()
        self.redis_ttl: int = conf.getRedisTTL()
        self.mp3Path: str = conf.getMP3Path()
        self.customPath: str = conf.getCustomPath()
        self.api = api
        # pygame removed; no mixer init

    def processMessage(self, msg: str) -> None:
        data = json.loads(msg)
        if data["firstname"] == "chantier":
            return
        if self.buildingName != data["building"]:
            return
        print(f"[{datetime.datetime.now()}][HV] NEW MESSAGE: {msg}")
        kind: str = data['kind']
        login: str = data['login']
        firstname: str = ""
        if login is not None and login != "":
            firstname: str = self.api.getUsualName(login)
        if firstname is None or firstname == "":
            firstname: str = data["firstname"]
        jsonFile: str = (self.customPath + login + ".json")
        if os.path.isfile(jsonFile):
            print(f"[{datetime.datetime.now()}][HV] Custom HallVoice for " + login + ": " + jsonFile)
            self.playCustomSound(kind, jsonFile, firstname)
            return
        else:
            self.genericMessage(firstname, kind)

    def playCustomSound(self, kind: str, jsonFile: str, firstname: str) -> None:
        kind: str = "welcome" if kind == "in" else "goodbye"
        try:
            with open(jsonFile, 'r') as custom_file:
                j = json.loads(custom_file.read())
                if kind in j:
                    if "mp3" in j[kind]:
                        try:
                            if os.path.isdir(self.mp3Path + j[kind]["mp3"]) is True:
                                customMP3 = (
                                    self.mp3Path
                                    + j[kind]["mp3"]
                                    + "/"
                                    + choice(os.listdir(self.mp3Path + j[kind]["mp3"]))
                                )
                                print(f"[{datetime.datetime.now()}][HV] Playing {customMP3}")
                                self.playFile(customMP3)
                            elif os.path.isfile(self.mp3Path + j[kind]["mp3"]) is True:
                                customMP3 = self.mp3Path + j[kind]["mp3"]
                                print(f"[{datetime.datetime.now()}][HV] Playing {customMP3}")
                                self.playFile(customMP3)
                            else:
                                self.playError("Error while loading a random mp3 file, please contact staff member")
                                print(f"[{datetime.datetime.now()}][HV] Error for custom hallvoice {jsonFile}"
                                      f", invalid path")
                                return
                        except Exception as e:
                            print(f"[{datetime.datetime.now()}][HV] Error while playing a custom song with pw-play:\n{e}")
                            self.playError("Error while playing a custom song, please contact staff member")
                    elif "txt" in j[kind]:
                        lang: str = j[kind]["lang"] if "lang" in j[kind] else "fr"
                        if isinstance(j[kind]["txt"], list):
                            self.say(j[kind]["txt"][randint(0, len(j[kind]["txt"]) - 1)], lang)
                        elif isinstance(j[kind]["txt"], str):
                            self.say(j[kind]["txt"], lang)
                else:
                    self.playError(f"Invalide JSON file {jsonFile}, please check your PR")
                    print(f"[{datetime.datetime.now()}][HV] Invalide JSON file {jsonFile}, kind in/out not found")
        except FileNotFoundError as e:
            self.playError("Error while loading your custom JSON, please contact staff member")
            print(f"[{datetime.datetime.now()}][HV] Custom HallVoice for {firstname} not found:\n{e}")
        except Exception as e:
            self.playError("A Serious error happend, please contact staff member")
            print(f"[{datetime.datetime.now()}][HV] Random Exception at playCustomSound():\n{e}")

    def genericMessage(self, firstname: str, kind: str) -> None:
        tts: str = ""
        if kind == "welcome" or kind == "in":
            tts: str = self.welcomeMsg[randint(0, len(self.welcomeMsg) - 1)][1].replace("<name>", firstname)
        elif kind == "goodbye" or kind == "out":
            tts: str = self.goodbyeMsg[randint(0, len(self.goodbyeMsg) - 1)][1].replace("<name>", firstname)
        self.say(tts, "fr")

    def say(self, txt: str, lang: str) -> None:
        mp3_fp = BytesIO()
        if txt is not None and txt != "":
            print(f"[{datetime.datetime.now()}][HV] Playing TTS: {txt}")
            cache = self.redis.get(txt + lang)  # Get the TTS from cache
            if cache:  # If TTS is cached, play it
                print(f"[{datetime.datetime.now()}][HV] TTS cache getted!")
                mp3_fp.write(cache)
                self.playMP3(mp3_fp)
            else:  # If TTS is NOT cached, cache it AND play it...
                print(f"[{datetime.datetime.now()}][HV] TTS cache not found, putting in cache")
                try:
                    # Generate speech using gTTS and save to a BytesIO object
                    tts = gTTS(text=txt, lang=lang)
                    # Create and write the TTS to a BytesIO
                    mp3_fp = BytesIO()
                    tts.write_to_fp(mp3_fp)
                    # Cache MP3 bytes
                    mp3_fp.seek(0)
                    data = mp3_fp.read()
                    self.redis.set(txt + lang, data, ex=self.redis_ttl)
                    mp3_fp = BytesIO(data)
                    self.playMP3(mp3_fp)
                except gTTSError as e:  # If we break gTTS API with rate-limit
                    print(f"[{datetime.datetime.now()}][HV] HallvoiceERROR TTS error:\n{e}")
                    # Only try to play if we actually have data
                    if mp3_fp.getbuffer().nbytes > 0:
                        self.playMP3(mp3_fp)
        else:
            self.playError("Error while generating TTS message, please contact staff member")
            print(f"[{datetime.datetime.now()}][HV] TTS messages generation error for txt: {txt}")

    @staticmethod
    def playMP3(mp3: BytesIO | bytes, volume: float = 0.5) -> None:
        """
        Play MP3 data using pw-play, reducing volume with sox.
        Ensures:
          - no simultaneous playback (class-level lock)
          - if we wait > 10s for the lock, we cancel.
        """
        if isinstance(mp3, BytesIO):
            data = mp3.getvalue()
        else:
            data = mp3

        if not data:
            return

        # Try to acquire the playback lock with a 10s timeout
        acquired = Messages._play_lock.acquire(timeout=Messages._play_timeout_sec)
        if not acquired:
            print(f"[{datetime.datetime.now()}][HV] Playback dropped: queue wait > {Messages._play_timeout_sec}s")
            return

        tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")

        try:
            # write original mp3
            tmp_in.write(data)
            tmp_in.close()
            tmp_out.close()

            # apply sox volume reduction
            subprocess.run(
                ["sox", tmp_in.name, tmp_out.name, "vol", str(volume)],
                check=True
            )

            # play reduced mp3
            subprocess.run(["pw-play", tmp_out.name], check=True)

        except subprocess.CalledProcessError as e:
            print(f"[{datetime.datetime.now()}][HV] Error during sox or pw-play:\n{e}")

        finally:
            # cleanup temp files
            for f in (tmp_in.name, tmp_out.name):
                try:
                    os.remove(f)
                except OSError:
                    pass
            # always release the lock if acquired
            Messages._play_lock.release()


    @staticmethod
    def playFile(path: str) -> None:
        """
        Play an existing MP3 file using pw-play.
        """
        # Try to acquire the playback lock with a 10s timeout
        acquired = Messages._play_lock.acquire(timeout=Messages._play_timeout_sec)
        if not acquired:
            print(f"[{datetime.datetime.now()}][HV] Playback dropped: queue wait > {Messages._play_timeout_sec}s")
            return
        try:
            subprocess.run(["pw-play", path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.datetime.now()}][HV] Error while playing file {path} with pw-play:\n{e}")
        finally:
            Messages._play_lock.release()

    def playError(self, message: str) -> None:
        mp3_fp = BytesIO()
        cache = self.redis.get(f"HallvoiceERROR+{message}")
        if cache:
            print(f"[{datetime.datetime.now()}][HV] HallvoiceERROR TTS cached")
            mp3_fp.write(cache)
            self.playMP3(mp3_fp)
        else:
            print(f"[{datetime.datetime.now()}][HV] HallvoiceERROR TTS not cached, caching him")
            try:
                tts = gTTS(text=message, lang="en")
                tts.write_to_fp(mp3_fp)
                mp3_fp.seek(0)
                data = mp3_fp.read()
                self.redis.set(f"HallvoiceERROR+{message}", data, ex=self.redis_ttl)
                self.playMP3(data)
            except gTTSError as e:
                print(f"[{datetime.datetime.now()}][HV] HallvoiceERROR TTS error:\n{e}")
