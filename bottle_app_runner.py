import os
import socket
import argparse
import webbrowser

import bottle


def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--server", help="server to use (default: waitress)")
    parser.add_argument("--host", help="address to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", help="port to bind to (default: 8080)")
    parser.add_argument(
        "--open", action="store_true", help="open browser (default: no)"
    )


def get_config(args: argparse.Namespace) -> tuple[str, str, int, bool]:
    server = args.server or os.environ.get("SERVER", "waitress")
    host = args.host or os.environ.get("IP", "0.0.0.0")
    port = args.port or os.environ.get("PORT", 8080)
    return server, host, port, args.open


def get_internal_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def run_app(app: bottle.Bottle, args: argparse.Namespace):
    server, host, port, open = get_config(args)

    original_url = f"http://{host}:{port}"
    local_url = f"http://localhost:{port}"
    try:
        internal_ip = get_internal_ip()
        internal_url = f"http://{internal_ip}:{port}"
    except Exception:
        internal_url = None
    print("Listen on:", original_url)

    open_url = original_url
    if host in ["localhost", "127.0.0.1", "0.0.0.0"]:
        open_url = local_url
        print("Local URL:", local_url)
    if host == "0.0.0.0" and internal_url is not None:
        open_url = internal_url
        print("Internal IP URL:", internal_url)
    if open:
        print("Browser open:", open_url)
        webbrowser.open(open_url)
    print()

    bottle.run(app, server=server, host=host, port=port)


if __name__ == "__main__":
    app = bottle.Bottle()

    @app.get("/<name>")
    def get_hello(name):
        return f"Hello, {name}!"

    @app.get("<path:path>")
    def get_any(path):
        return bottle.redirect("/world")

    parser = argparse.ArgumentParser(
        description="Simple hello world http server",
    )
    add_arguments(parser)
    args = parser.parse_args()

    run_app(app, args)
