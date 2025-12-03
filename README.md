# Porte42 - Hall Voice
Bonjour la porte

# Requirements
## Studs
- Buy Hall Voice Change on [intra shop](https://shop.intra.42.fr/)
- Make a [Pull Request](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork) to add your files
  - Include your login in the PR name
  - Add a .json file with your configuration (Also see `custom/_Example.json`)
  - No sound during more than 10 seconds
  - No more than 20 sounds
  - No sound over 1 Mo
  - No troll, insults, too loud sound, etc

PR might be refused if one of those requirements are missing

You can find an example PR [here](https://github.com/42Paris/hall-voice/pull/3/files)

## Staff
- Buy one RPI
- In Raspbian, clone this repository
- Goto the repository and type
  - `pip3 install -r requirements.txt`
- Install a Redis server
  - `sudo apt-get install redis`
- How to run?
  - You can use systemctl
    - `sudo cp hallvoice.service /etc/systemd/system`
    - `sudo systemctl enable --now hallvoice.service`
  - You can use Docker (WIP DO NOT USE ME, OR THE RPI WILL BURN)
    - `docker compose build --no-cache`
    - `docker compose up -d`
    - To look at logs: `docker compose logs -f`
- Copy and fill-up the config file in
  - `cp config/config.ini.example config/config.ini`
- Kafka:
  - The RPI must be in bocal's network so it can access Redpanda
  - You messages MUST be JSONised like so
    - `{"building":"<where>","firstname":"<name>","kind":"<in/out>","login":"<login>"}`
- You can pre-fill the redis cache with
  - `goinfre-firstname-redis.py`
    - to get all firstname from list of logins in `login.list`
  - `goinfre-tts-redis.py`
    - to cache all gTTS from a list of firstname in `firstname.list`
      - This can take a very long time, generate one tts per second to avoid Google rate-limit
- All data stored in redis have a TTL of 6 months

# QnA
## Studs
- Q: Will the hallvoice use Usualname if I have one?
  - A: Yes! Hallvoice use 42API to get your Usualname from your login, if there is no Usualname find, legal firstname will be used and cached
- Q: I juste set a Usualname but the old legal firstname is still in use, how to "force" the hallvoice to use the my Usualname?
  - A: Firstname is cached in Redis, you need to ask the bocal in [Slack](https://42born2code.slack.com/archives/C7P0Z4F3L) #42paris_staff_it or [Discord](https://discord.com/channels/774300457157918772/839426887171440671) #staff_it to purge it.
- Q: I bought hallvoice, how to use it?
  - A: As written in `Requirements`: You can find an example [PR](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork) [here](https://github.com/42Paris/hall-voice/pull/3/files), also see `custom/_Example.json`
- Q: I want to change a song, do I have to buy hallvoice again?
  - A: No
- Q: What's the TTL (Time to live) for the cache?
  - A: TTL for redis cache is 6 month, the staff can change it in the config file, or purge by login if asked
- Q: Code is garbage, can I improve it?
  - I guess... Yes you can? You can try to do a [PR](https://help.github.com/en/articles/creating-a-pull-request-from-a-fork)

## Staff
- Q: I am the bocal, how to purge cache from a login?
  - A: From bocal's network, make GET call at `http://<rpi-IP>:8000/?purge=<login>`
- Q: How can I query cache ?
  - A: From bocal's network, make GET call at `http://<rpi-IP>:8000/?get=<login>`
- Q: Something's f*cky, need to debug!
  - A: Logs can be found in folder `logs/<date>-hallvoice.log`
- Q: How to update?
  - A: Hmmm, Are you pisciner? A simple `git pull` should do the trick :)

# Fun fact
- When redis cache is fully pre-filled:
  - it consume ~300M of disk space
  - 39888 TTS cached (2493 firstname * 16 welcome and goodbye message)
  - ~5300 login is used to cache firstnames
- The RPI has no soundcard whatsoever, we use Dante to play the mp3 across the network. Yes, the speaker works via PoE and is connected to the network.

# Change logs
- Hallvoice V2
  - Now works with kafka
- Hallvoice V3
  - Still in python but now code is object oriented
  - Redis cache to store the firstname from 42API
  - Redis cache to store
  - Norm and sanitize JSON files
- Hallvoice V3.1
  - Dockerized!
- Hallvoice V3.2
  - Improvement in dockerization!
  - Added `get` param in PurgeAPI
  - PurgeAPI code Improvement
- Hallvoice V3.2.1
  - WIP, Token authentification for PurgeAPI
- Hallvoice V3.3
  - Removed unused files
  - Moved CI scripts to dedicated folder
  - Moved conf file to folder
  - Updated some path in conf files
- Hallvoice V3.3.1
  - Updated volumes for redis container
- Hallvoice V3.3.2
  - Added the very most important folders in hallvoice container
  - Custom path if run in docker mode
- Hallvoice V3.3.3
  - Path for custom MP3 and JSON is now in config file
  - Custom MP3 played is now logged
  - Added print() and TTS for helping debugging
  - Added one Welcome and Goodbye message
  - docker-compose.yaml
    - added depends_on for hallvoice and purgeapi containers
    - Explicit read-only on folder: config, mp3, custom 
    - Forcing TZ
    - Ports for purgeAPI
  - More print() and TTS for debugging
- Hallvoice V3.3.4
  - Moved and modified print()
- Hallvoice V3.4
  - Changed the way mp3 are played, from pygame to pw-play
  - When `--log-in-file` is used to log the output to file, it now also print logs to `stdout`
  - Changed the way intra API is handled

###### Made with love by 42Paris team SI

###### Soon™, Hallvoice V4 in Golang!
