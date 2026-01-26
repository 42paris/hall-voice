import datetime
import asyncio
import redis
import time
from IntraAPIClient import IntraAPIClient


class API42(object):
    def __init__(self, conf) -> None:
        self.redis = redis.Redis(host=conf.getRedisHost(), port=conf.getRedisPort(), db=0)
        self.redis_ttl: int = conf.getRedisTTL()
        apiKey: list[str] = conf.getAPIkeys()
        self.api = IntraAPIClient(conf)

    async def refreshCache(self, login) -> str | None:
        url = f"users/{login}"
        try:
            print(f"[{datetime.datetime.now()}] API refreshing cache for {login}")
            intra = self.api.get(url)
            if intra is not None and intra.status_code == 200:
                # Get the usual name
                firstname = intra.json()["usual_first_name"]
                # If there is no usual name, take the first_name
                if firstname is None:
                    firstname = intra.json()["first_name"]
                # Putting in redis cache
                self.redis.set(f"login: {login}", firstname, ex=self.redis_ttl)  # Cache the firstname for 6 month
                return firstname
        except Exception as e:
            print(f"[{datetime.datetime.now()}] API exception excepted while refreshing cache, {e}")
            return None

    def getUsualName(self, login) -> str | None:
        cached_data = self.redis.get(f"login: {login}")
        if cached_data:
            print(f"[{datetime.datetime.now()}] API cache data found for {login}")
            asyncio.create_task(self.refreshCache(login))  # Refresh cache in background
            # Return firstname if it is in redis cache
            return str(cached_data.decode('utf-8'))
        else:
            # Else get it from API
            return asyncio.run(self.refreshCache(login))