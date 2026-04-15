import datetime
import os
import json
import subprocess
import tempfile
import redis
import threading
import queue
from io import BytesIO
from random import choice, randint
from gtts import gTTS, gTTSError


class Messages(object):
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

        self._play_queue = queue.Queue()
        self._play_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self._play_thread.start()

    def processMessage(self, msg: str) -> None:
        data = json.loads(msg)
        if data["firstname"] == "chantier":
            return
        if self.buildingName != data["building"]:
            return

        print(f"[{datetime.datetime.now()}][HV] NEW MESSAGE: {msg}")
        kind: str = data["kind"]
        login: str = data["login"]
        company: str = data["company"]

        firstname: str = "" if "promo" in company or "piscine" in company else data["firstname"]
        if login and firstname == "":
            firstname = self.api.getUsualName(login)
        if not firstname:
            firstname = "toi"

        jsonFile: str = self.customPath + login + ".json"
        if os.path.isfile(jsonFile):
            print(f"[{datetime.datetime.now()}][HV] Custom HallVoice for {login}: {jsonFile}")
            self.playCustomSound(kind, jsonFile, firstname)
        else:
            self.genericMessage(firstname, kind)

    def playCustomSound(self, kind: str, jsonFile: str, firstname: str) -> None:
        kind = "welcome" if kind == "in" else "goodbye"
        try:
            with open(jsonFile, "r") as custom_file:
                j = json.loads(custom_file.read())
                if kind not in j:
                    self.playError(f"Invalid JSON file {jsonFile}, please check your PR")
                    print(f"[{datetime.datetime.now()}][HV] Invalid JSON file {jsonFile}, kind in/out not found")
                    return

                if "mp3" in j[kind]:
                    try:
                        base = self.mp3Path + j[kind]["mp3"]
                        if os.path.isdir(base):
                            customMP3 = base + "/" + choice(os.listdir(base))
                            print(f"[{datetime.datetime.now()}][HV] Queueing {customMP3}")
                            self.enqueue_file(customMP3)
                        elif os.path.isfile(base):
                            customMP3 = base
                            print(f"[{datetime.datetime.now()}][HV] Queueing {customMP3}")
                            self.enqueue_file(customMP3)
                        else:
                            self.playError("Error while loading a random mp3 file, please contact staff member")
                            print(f"[{datetime.datetime.now()}][HV] Error for custom hallvoice {jsonFile}, invalid path")
                    except Exception as e:
                        print(f"[{datetime.datetime.now()}][HV] Error while queueing a custom song:\n{e}")
                        self.playError("Error while playing a custom song, please contact staff member")

                elif "txt" in j[kind]:
                    lang: str = j[kind]["lang"] if "lang" in j[kind] else "fr"
                    if isinstance(j[kind]["txt"], list):
                        self.say(j[kind]["txt"][randint(0, len(j[kind]["txt"]) - 1)], lang)
                    elif isinstance(j[kind]["txt"], str):
                        self.say(j[kind]["txt"], lang)

        except FileNotFoundError as e:
            self.playError("Error while loading your custom JSON, please contact staff member")
            print(f"[{datetime.datetime.now()}][HV] Custom HallVoice for {firstname} not found:\n{e}")
        except Exception as e:
            self.playError("A serious error happened, please contact staff member")
            print(f"[{datetime.datetime.now()}][HV] Random Exception at playCustomSound():\n{e}")

    def genericMessage(self, firstname: str, kind: str) -> None:
        tts = ""
        if kind in ("welcome", "in"):
            tts = self.welcomeMsg[randint(0, len(self.welcomeMsg) - 1)][1].replace("<name>", firstname)
        elif kind in ("goodbye", "out"):
            tts = self.goodbyeMsg[randint(0, len(self.goodbyeMsg) - 1)][1].replace("<name>", firstname)
        self.say(tts, "fr")

    def say(self, txt: str, lang: str) -> None:
        if not txt:
            self.playError("Error while generating TTS message, please contact staff member")
            print(f"[{datetime.datetime.now()}][HV] TTS messages generation error for txt: {txt}")
            return

        print(f"[{datetime.datetime.now()}][HV] Preparing TTS: {txt}")
        cache_key = f"tts:{lang}:{txt}"
        cache = self.redis.get(cache_key)

        if cache:
            print(f"[{datetime.datetime.now()}][HV] TTS cache hit")
            self.enqueue_mp3(cache)
            return

        print(f"[{datetime.datetime.now()}][HV] TTS cache not found, generating")
        try:
            mp3_fp = BytesIO()
            tts = gTTS(text=txt, lang=lang)
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            data = mp3_fp.read()
            self.redis.set(cache_key, data, ex=self.redis_ttl)
            self.enqueue_mp3(data)
        except gTTSError as e:
            print(f"[{datetime.datetime.now()}][HV] HallvoiceERROR TTS error:\n{e}")

    def playError(self, message: str) -> None:
        cache_key = f"HallvoiceERROR:{message}"
        cache = self.redis.get(cache_key)

        if cache:
            print(f"[{datetime.datetime.now()}][HV] HallvoiceERROR TTS cached")
            self.enqueue_mp3(cache)
            return

        print(f"[{datetime.datetime.now()}][HV] HallvoiceERROR TTS not cached, generating")
        try:
            mp3_fp = BytesIO()
            tts = gTTS(text=message, lang="en")
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            data = mp3_fp.read()
            self.redis.set(cache_key, data, ex=self.redis_ttl)
            self.enqueue_mp3(data)
        except gTTSError as e:
            print(f"[{datetime.datetime.now()}][HV] HallvoiceERROR TTS error:\n{e}")

    def enqueue_mp3(self, data: bytes, volume: float = 0.7) -> None:
        self._play_queue.put({
            "type": "mp3",
            "data": data,
            "volume": volume,
            "queued_at": datetime.datetime.now().timestamp(),
        })

    def enqueue_file(self, path: str) -> None:
        self._play_queue.put({
            "type": "file",
            "path": path,
            "queued_at": datetime.datetime.now().timestamp(),
        })

    def _playback_worker(self) -> None:
        while True:
            job = self._play_queue.get()
            try:
                age = datetime.datetime.now().timestamp() - job["queued_at"]
                if age > self._play_timeout_sec:
                    print(f"[{datetime.datetime.now()}][HV] Playback dropped: queue wait > {self._play_timeout_sec}s")
                    continue

                if job["type"] == "mp3":
                    self._play_mp3_now(job["data"], job["volume"])
                elif job["type"] == "file":
                    self._play_file_now(job["path"])

            except Exception as e:
                print(f"[{datetime.datetime.now()}][HV] Playback worker error:\n{e}")
            finally:
                self._play_queue.task_done()

    @staticmethod
    def _play_mp3_now(mp3: bytes, volume: float = 0.7) -> None:
        if not mp3:
            return

        tmp_in = None
        tmp_out = None

        try:
            tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")

            tmp_in.write(mp3)
            tmp_in.close()
            tmp_out.close()

            subprocess.run(
                ["sox", tmp_in.name, tmp_out.name, "vol", str(volume)],
                check=True,
            )
            subprocess.run(["pw-play", tmp_out.name], check=True)

        except subprocess.CalledProcessError as e:
            print(f"[{datetime.datetime.now()}][HV] Error during sox or pw-play:\n{e}")
        finally:
            for f in (tmp_in, tmp_out):
                if f is not None:
                    try:
                        os.remove(f.name)
                    except OSError:
                        pass

    @staticmethod
    def _play_file_now(path: str) -> None:
        try:
            subprocess.run(["pw-play", path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.datetime.now()}][HV] Error while playing file {path} with pw-play:\n{e}")