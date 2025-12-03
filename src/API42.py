import datetime
import redis
import time
from IntraAPIClient import IntraAPIClient


class API42(object):
    def __init__(self, conf) -> None:
        self.redis = redis.Redis(host=conf.getRedisHost(), port=conf.getRedisPort(), db=0)
        self.redis_ttl: int = conf.getRedisTTL()
        apiKey: list[str] = conf.getAPIkeys()
        self.api = IntraAPIClient(conf)

    def getUsualName(self, login) -> str | None:
        url = f"users/{login}"
        cached_data = self.redis.get(f"login: {login}")
        if cached_data:
            print(f"[{datetime.datetime.now()}] API cache data found for {login}")
            # Return firstname if it is in redis cache
            return str(cached_data.decode('utf-8'))
        else:
            print(f"[{datetime.datetime.now()}] API cache data not found for {login}, putting in cache")
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
            else:
                return "toi"
