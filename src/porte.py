import datetime
import sys
import os
from Conf import Conf
from API42 import API42
from Kafka import Kafka


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Where conf file? Use me like this!\n\tpython3 porte.py config.yaml")
        exit(1)

    if "--help" in sys.argv:
        print("Usage: python3 src/porte.py config.yaml")
        print("\tYou can also add --log-in-file in the end to output log in file")
        exit(0)

    if sys.argv[1] and os.path.exists(sys.argv[1]):
        conf = Conf(sys.argv[1])

        log_file = None

        if '--log-in-file' in sys.argv:
            os.makedirs(conf.pathLogs, exist_ok=True)

            date_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            log_path = f"{conf.pathLogs}/{date_str}_hallvoice.log"

            log_file = open(log_path, "a", buffering=1, encoding="utf-8")

            sys.stdout = Tee(sys.stdout, log_file)
            sys.stderr = Tee(sys.stderr, log_file)

        try:
            api = API42(conf)
            consumer = Kafka(conf, api)
            consumer.consume_messages()
        finally:
            if log_file:
                log_file.close()
    else:
        print("Config path not exists, check your args...")
        print("Path for config file should be the first arg")
        print("Usage: python3 porte.py config.yaml")
        print("\tYou can also add --log-in-file in the end to output log in file")
        exit(1)