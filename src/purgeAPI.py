import sys
import redis
import urllib.parse
import ipaddress
from http.server import HTTPServer, BaseHTTPRequestHandler
from Conf import Conf

if sys.argv[1] is not None:
    conf = Conf(sys.argv[1])
    r = redis.Redis(host=conf.getRedisHost(), port=conf.getRedisPort(), db=0)
else:
    print(f"Usage: python3 purgeAPI.py <path-to-conf-file>")
    exit(1)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def reponse(self, value: int, message):
        self.send_response(value)
        # If login not found in cache
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        print(message)
        self.wfile.write(message.encode())

    def do_GET(self):
        client_address = ipaddress.ip_address(self.client_address[0])
        if conf.getPurgeToken():
            print("WIP, Please code me")
        # Check if client is from range of networks
        if (client_address in ipaddress.ip_network("10.42.0.0/16")
                or (client_address in ipaddress.ip_network("10.43.0.0/16"))
                or (client_address in ipaddress.ip_network("10.41.0.0/16"))
                or (client_address in ipaddress.ip_network("10.50.0.0/16"))
                or (client_address in ipaddress.ip_network("10.51.0.0/16"))
                or (client_address in ipaddress.ip_network("127.0.0.1/32"))):
            # Parse query parameters
            query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if 'purge' in query_components:
                purge_value = query_components.get('purge', None)
                print(f"Purge request received with value: {purge_value[0]}")
                # Get firstname from cache
                cache = r.get(f"login: {purge_value[0]}")
                # If firname is cached
                if cache:
                    # Delete firstname from redis cache
                    r.delete(f"login: {purge_value[0]}")
                    self.reponse(200, f"Login {purge_value[0]} purged from cache. Value was {cache.decode()}")
                # Else login not found in cache
                else:
                    self.reponse(404, f"Cannot purge `{purge_value[0]}`, not found in cache")
            elif 'get' in query_components:
                get_value = query_components.get('get', None)
                print(f"Get request received with value: {get_value[0]}")
                # Get firstname from cache
                cache = r.get(f"login: {get_value[0]}")
                # If firname is cached
                if cache:
                    # Print value in console and response
                    self.reponse(200, f"Value for `{get_value[0]}` is `{cache.decode()}` from cache.")
                else:
                    self.reponse(404, f"Cannot get `{get_value[0]}`, not found in cache")
            else:
                # If no parameter, send man
                self.reponse(400, "Please provide a 'purge' or `get` query parameter.")


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print(f"Starting httpd server on port {server_address[1]}")
    httpd.serve_forever()


if __name__ == '__main__':
    run()
