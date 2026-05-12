import datetime
import threading
from RatatouilleClient import RatatouilleClient
import redis

class API42:
    def __init__(self, conf) -> None:
        self.redis = redis.Redis(host=conf.getRedisHost(), port=conf.getRedisPort(), db=0)
        self.redis_ttl: int = conf.getRedisTTL()
        self.client = RatatouilleClient(
            client_id=conf.getRatatouilleClientId(),
            client_secret=conf.getRatatouilleClientSecret(),
            realm=conf.getRatatouilleRealm(),
        )

    def _cache_key(self, login: str) -> str:
        return f"login: {login}"

    def refresh_cache(self, login: str) -> str | None:
        try:
            print(f"[{datetime.datetime.now()}] API refreshing cache for {login}")
            user = self.client.getUserByIDOrUsername(login)
            if user is None or user.status_code != 200:
                return None
            data = user.json()
            firstname = data.get("first_name")
            if not firstname:
                return None
            self.redis.set(self._cache_key(login), firstname, ex=self.redis_ttl)
            return firstname
        except Exception as e:
            print(f"[{datetime.datetime.now()}] API exception while refreshing cache: {e}")
            return None

    def getName(self, login: str) -> str | None:
        key = self._cache_key(login)
        cached_data = self.redis.get(key)
        if cached_data:
            print(f"[{datetime.datetime.now()}] API cache data found for {login}")
            # Refresh en arrière-plan
            threading.Thread(
                target=self.refresh_cache,
                args=(login,),
                daemon=True
            ).start()
            return cached_data.decode("utf-8")
        return self.refresh_cache(login)
