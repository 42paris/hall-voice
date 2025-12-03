import os
import time
import requests

requests.packages.urllib3.disable_warnings()


class IntraAPIClient(object):
    verify_requests = False

    def __init__(self, conf, progress_bar=False):
        base_dir = os.path.dirname(os.path.realpath(__file__))
        self.client_id = conf.getAPIkeys()[0]
        self.client_secret = conf.getAPIkeys()[1]
        self.token_url = "https://api.intra.42.fr/v2/oauth/token"
        self.api_url = "https://api.intra.42.fr/v2"
        self.scopes = "public"
        self.progress_bar = progress_bar
        self.token = None

    def request_token(self):
        request_token_payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": self.scopes,
        }
        print("Attempting to get a token from intranet")
        self.token = "token_dummy"
        res = self.request(requests.post, self.token_url, params=request_token_payload)
        rj = res.json()
        self.token = rj["access_token"]
        print(f"Got new acces token from intranet {self.token}")

    def _make_authed_header(self, header={}):
        ret = {"Authorization": f"Bearer {self.token}"}
        ret.update(header)
        return ret

    def request(self, method, url, headers={}, **kwargs):
        if not self.token:
            self.request_token()
        tries = 0
        if not url.startswith("http"):
            url = f"{self.api_url}/{url}"

        while True:
            print(f"Attempting a request to {url}")

            res = method(
                url,
                headers=self._make_authed_header(headers),
                verify=self.verify_requests,
                **kwargs
            )

            rc = res.status_code
            if rc == 500:
                print(f"Server error {str(rc)}\n{str(res.content)}")
                time.sleep(1)
                continue
            if rc == 401:
                if 'www-authenticate' in res.headers:
                    _, desc = res.headers['www-authenticate'].split('error_description="')
                    desc, _ = desc.split('"')
                    if desc == "The access token expired" or desc == "The access token is invalid":
                        if self.token != "token_dummy":
                            print(f"Server said our token {self.token} {desc.split(' ')[-1]}")
                        if tries < 5:
                            print("Renewing token")
                            tries += 1
                            self.request_token()
                            time.sleep(1)
                            continue
                        else:
                            print("Tried to renew token too many times, something's wrong")

            if rc == 429:
                print(f"Rate limit exceeded - Waiting {res.headers['Retry-After']}s before requesting again")
                time.sleep(float(res.headers['Retry-After']))
                continue

            if rc >= 400:
                req_data = "{}{}".format(url, "\n" + str(kwargs['params']) if 'params' in kwargs.keys() else "")
                if rc < 500:
                    raise ValueError(f"\n{res.headers}\n\nClientError. Error {str(rc)}\n{str(res.content)}\n{req_data}")
                else:
                    raise ValueError(f"\n{res.headers}\n\nServerError. Error {str(rc)}\n{str(res.content)}\n{req_data}")

            print(f"Request to {url} returned with code {rc}")
            return res

    def get(self, url, headers={}, **kwargs):
        return self.request(requests.get, url, headers, **kwargs)

    def post(self, url, headers={}, **kwargs):
        return self.request(requests.post, url, headers, **kwargs)

    def patch(self, url, headers={}, **kwargs):
        return self.request(requests.patch, url, headers, **kwargs)

    def put(self, url, headers={}, **kwargs):
        return self.request(requests.put, url, headers, **kwargs)

    def delete(self, url, headers={}, **kwargs):
        return self.request(requests.delete, url, headers, **kwargs)
