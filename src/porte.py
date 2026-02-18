import datetime
import sys
import os
from Conf import Conf
from API42 import API42
from Kafka import Kafka

class Tee:
    def __init__(self, *steams):
        self.steams = steams

    def write(self, logs):
        for s in self.steams:
            s.write(logs)

    def flush(self):
        for s in self.steams:
            s.flush()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Where conf file? Use me like this!\n\tpython3 porte.py config.yaml")
        exit(1)
    elif "--help" in sys.argv:
        print("Usage: python3 src/porte.py config.yaml")
        print("\tYou can also add --log-in-file in the end to output log in file")
        exit(0)
    elif sys.argv[1] is not None and os.path.exists(sys.argv[1]):
        conf = Conf(sys.argv[1])
        date = datetime.datetime.now()
        date_str = date.strftime("%Y%m%d-%H%M%S")
        if '--log-in-file' in sys.argv:
            f = open(f"{conf.pathLogs}/{date_str}_hallvoice.log", "w", buffering=1)
            sys.stdout = Tee(sys.stdout, f)
            sys.stderr = Tee(sys.stderr, f)
        api = API42(conf)
        consumer = Kafka(conf, api)
        consumer.consume_messages()
    else:
        print("Config path not exists, check your args...")
        print("Path for config file should be the first arg")
        print("Usage: python3 porte.py config.yaml")
        print("\tYou can also add --log-in-file in the end to output log in file")
        exit(1)
