import time
import requests


class RatatouilleClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str | None = None,
        password: str | None = None,
        auth_base_url: str = "https://auth.42paris.fr",
        api_base_url: str = "https://ratatouille.42paris.fr/api/v1",
        realm: str = "master",
        scope: str = "openid",
    ):
        self.auth_base_url = auth_base_url
        self.api_base_url = api_base_url

        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.realm = realm
        self.scope = scope

        self.access_token: str | None = None
        self.expires_at = 0

    @property
    def token_url(self) -> str:
        return (
            f"{self.auth_base_url}/realms/{self.realm}"
            "/protocol/openid-connect/token"
        )

    def get_token(self) -> str:
        if self.access_token and time.time() < self.expires_at - 30:
            return self.access_token

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
        }

        if self.username and self.password:
            data.update({
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            })
        else:
            data.update({
                "grant_type": "client_credentials",
            })

        response = requests.post(self.token_url, data=data, timeout=15)
        response.raise_for_status()

        payload = response.json()
        self.access_token = payload["access_token"]
        self.expires_at = time.time() + payload.get("expires_in", 300)

        return self.access_token

    def request(self, method: str, path: str, **kwargs):
        token = self.get_token()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        headers.setdefault("Accept", "application/json")

        url = f"{self.api_base_url}{path}"

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            timeout=15,
            **kwargs,
        )

        response.raise_for_status()

        if response.content:
            return response.json()

        return None

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, json=None, **kwargs):
        return self.request("POST", path, json=json, **kwargs)
    
    def getUserByIDOrUsername(self, id_or_username: str, hint: str | None = None):
        try:
            url = f"/users/{id_or_username}"
            if hint:
                url += f"?hint={hint}"
            return self.get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise