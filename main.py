import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


# Path to the storage file
STORAGE_FILE = "storage/data.json"

# Ensure the storage directory exists
os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)
if not os.path.exists(STORAGE_FILE):
    with open(STORAGE_FILE, "w") as f:
        json.dump({}, f)

env = Environment(loader=FileSystemLoader("."))


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message.html":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            self.render_read_page()

        elif pr_url.path.startswith("/") and os.path.exists(pr_url.path[1:]):
            self.send_static_file(pr_url.path[1:])
        else:
            self.send_html_file("error.html", 404)

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            parsed_data = parse_qs(post_data.decode("utf-8"))
            username = parsed_data.get("username", [""])[0]
            message = parsed_data.get("message", [""])[0]

            if username and message:
                self.save_message(username, message)
                self.send_response(302)
                self.send_header("Location", "/read")
                self.end_headers()
            else:
                self.send_html_file("error.html", 400)

    def save_message(self, username, message):
        """Save the message to the JSON file with a timestamp."""
        timestamp = datetime.now().isoformat()
        try:
            with open(STORAGE_FILE, "r+") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}

                data[timestamp] = {"username": username, "message": message}

                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except FileNotFoundError:
            with open(STORAGE_FILE, "w") as f:
                json.dump(
                    {timestamp: {"username": username, "message": message}}, f, indent=4
                )

    def render_read_page(self):
        """Render the /read page with messages from data.json."""
        try:
            with open(STORAGE_FILE, "r") as f:
                try:
                    messages = json.load(f)
                except json.JSONDecodeError:
                    messages = {}
        except FileNotFoundError:
            messages = {}

        template = env.get_template("read.html")
        rendered_page = template.render(messages=messages)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(rendered_page.encode("utf-8"))

    def send_html_file(self, filename, status=200):
        """Send HTML file to the client."""
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static_file(self, filename):
        """Send static file like CSS, JS, or images."""
        if os.path.exists(filename):
            if filename.endswith(".css"):
                content_type = "text/css"
            elif filename.endswith(".png"):
                content_type = "image/png"
            elif filename.endswith(".js"):
                content_type = "application/javascript"
            else:
                content_type = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.end_headers()
            with open(filename, "rb") as fd:
                self.wfile.write(fd.read())
        else:
            self.send_html_file("error.html", 404)


def run(server_class=HTTPServer, handler_class=HttpHandler):

    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        print("Server running on http://localhost:3000")
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
