import configparser


class Conf(object):
    def __init__(self, path: str) -> None:
        try:
            with open(path, "r"):
                config = configparser.ConfigParser()
                config.read(path)

                # Accessing values from the configuration file
                self.kafka_servers: str = config.get("kafka", "kafka_servers")
                self.topic: list[str] = []
                self.topic.append(config.get("kafka", "topic"))
                self.group_id: str = config.get("kafka", "group_id")
                self.username: str = config.get("kafka", "username")
                self.password: str = config.get("kafka", "password")
                self.pathCustom: str = config.get("path", "custom")
                self.pathMP3: str = config.get("path", "mp3")
                self.pathLogs: str = config.get("path", "logs")
                self.building: str = config.get("building", "name")
                self.purgeToken: str = config.get("purgeapi", "token")
                self.redis_host: str = config.get("redis", "host")
                self.redis_port: int = int(config.get("redis", "port"))
                self.redis_ttl: int = int(config.get("redis", "ttl"))
                self.apiUID: str = config.get("42api", "uid")
                self.apiSEC: str = config.get("42api", "secret")
                self.welcome: list[tuple[str, str]] = []
                self.goodbye: list[tuple[str, str]] = []
                for welcomeMsg in config.items("welcome"):
                    self.welcome.append(welcomeMsg)
                for goodbyeMsg in config.items("goodbye"):
                    self.goodbye.append(goodbyeMsg)
        except FileNotFoundError as e:
            print(f"Cannot open {path}:\n{e}")
        except configparser.NoSectionError as e:
            print(f"Cannot read config at {path}:\n{e}")
            exit(1)


    def getKafkaServer(self) -> str:
        return self.kafka_servers

    def getTopic(self) -> list[str]:
        return self.topic

    def getGroupID(self) -> str:
        return self.group_id

    def getUsername(self) -> str:
        return self.username

    def getPassword(self) -> str:
        return self.password

    def getCustomPath(self) -> str:
        return self.pathCustom

    def getMP3Path(self) -> str:
        return self.pathMP3

    def getLogPath(self) -> str:
        return self.pathLogs

    def getBuilding(self) -> str:
        return self.building

    def getPurgeToken(self) -> str:
        return self.purgeToken

    def getAPIkeys(self) -> list[str]:
        return [self.apiUID, self.apiSEC]

    def getWelcome(self) -> list[tuple[str, str]]:
        return self.welcome

    def getGoodbye(self) -> list[tuple[str, str]]:
        return self.goodbye

    def getRedisHost(self) -> str:
        return self.redis_host

    def getRedisPort(self) -> int:
        return self.redis_port

    def getRedisTTL(self) -> int:
        return self.redis_ttl
