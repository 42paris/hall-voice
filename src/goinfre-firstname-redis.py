import configparser
import datetime
import random
import time
import redis
import requests
import threading


def api_call(start_l, end_l, access_token):
    with open("login.list", "r") as f:
        for i, line in enumerate(f):
            if i < start_l:
                continue
            elif i >= end_l:
                break
            else:
                cache = r.get(f"login: {line.strip()}")
                if cache is None:
                    # Wait a random time for rate limit
                    time.sleep(random.randint(0, 3))
                    user = requests.get(f"https://api.intra.42.fr/v2/users/{line.strip()}?access_token={access_token}")
                    if user.status_code == 404:
                        print(f"[{datetime.datetime.now()}] API Error 404, returning None.")
                        return None
                    elif user.status_code == 429:
                        print(f"[{datetime.datetime.now()}] API42 rate limited, reduce number of threads to avoid rate"
                              f"limiting")
                        return
                    if user is not None and user.status_code == 200:
                        # Get the usual name
                        firstname = user.json()["usual_first_name"]
                        # If there is no usual name, take the first_name
                        if firstname is None:
                            firstname = user.json()["first_name"]
                        print(f"caching login {line.strip()} with first name {firstname}")
                        r.set(f"login: {line.strip()}", firstname, ex=15778800)
                    else:
                        print(f"Failed to add login {line.strip()} in cache because error {user}")


config = configparser.ConfigParser()
config.read("config/config.ini")
apiUID = config.get("42api", "uid")
apiSEC = config.get("42api", "secret")
urltoken = requests.post("https://api.intra.42.fr/oauth/token?grant_type=client_credentials&client_id=" + apiUID + "&client_secret=" + apiSEC)
token = urltoken.json()['access_token']

if urltoken.status_code == 200:
    print("Successfully getted a token")
    nb_threads = 12
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    with open("login.list", "r") as f:
        file = f.readlines()
        chunk_size = len(file) // nb_threads
        threads = []
        for i in range(nb_threads):
            start_line = i * chunk_size
            # Make sure to handle the last chunk properly if it has fewer lines
            end_line = start_line + chunk_size if i < nb_threads - 1 else len(file)
            thread = threading.Thread(target=api_call, args=(start_line, end_line, token))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
else:
    print("Error while getting token")
