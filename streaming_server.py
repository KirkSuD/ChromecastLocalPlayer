import os
import mimetypes
import urllib.parse
from pathlib import Path
from datetime import datetime

import bottle

app = bottle.Bottle()
config = {
    "limit_dir": None,  # all path can be accessed
    "home_path": str(Path.home()),  # home page redirect to
    "static_size": 16 * 1024 * 1024,  # <= 16MiB: return static file
    "partial_size": 4 * 1024 * 1024,  # else: default partial length 4MiB
}


def parse_range(range_str, size):
    if "," in range_str:
        # multipart ranges are not supported
        return -1, -1
    bytes_str, range_str = range_str.split("=", maxsplit=1)
    if bytes_str.strip() != "bytes":
        # unknown unit
        return -1, -1
    start, end = range_str.split("-", maxsplit=1)
    start, end = start.strip(), end.strip()
    if start == "":
        # Range: bytes=-100 => last 100 bytes
        start, end = size - int(end), size - 1
    elif end == "":
        # Range: bytes=100- => bytes since 100
        start, end = int(start), size - 1
    else:
        start, end = int(start), int(end)
    return start, end


def parse_size(s):
    if type(s) is not str:
        return s
    si = "BKMGTPEZY"
    s = s.upper().rstrip("B")
    kilo = 1000
    if s and s[-1] == "I":
        kilo = 1024
        s = s[:-1]
    n = 1
    if s and s[-1] in si:
        n = kilo ** si.index(s[-1])
        s = s[:-1]
    if not s:
        return 0
    try:
        return int(s) * n
    except ValueError:
        return float(s) * n


def format_size(n, ib=False):
    kilo = 1024 if ib else 1000
    si = "BKMGTPEZY"
    i = 0
    while n >= kilo:
        n //= kilo
        i += 1
    res = str(n) + " "
    if i > 0:
        res += si[i]
    res += "iB" if ib else "B"
    return res


def canonical_path(path):
    return Path(os.path.expandvars(str(path))).expanduser().resolve().absolute()


# https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests
@app.route("/file", method="HEAD")
def head_file():
    path = canonical_path(bottle.request.query.path)
    print("HEAD /file", path)
    if config["limit_dir"] and not path.is_relative_to(config["limit_dir"]):
        return bottle.abort(403, "Forbidden")
    if not path.is_file():
        return bottle.abort(404, "Not Found")
    size = path.stat().st_size
    bottle.response.headers["Accept-Ranges"] = "bytes"

    content_type, _ = mimetypes.guess_type(path)
    if content_type:
        bottle.response.headers["Content-Type"] = content_type
    bottle.response.headers["Content-Length"] = size


@app.get("/file")
def get_file():
    path = canonical_path(bottle.request.query.path)
    print("GET /file", path)
    if config["limit_dir"] and not path.is_relative_to(config["limit_dir"]):
        return bottle.abort(403, "Forbidden")
    if not path.is_file():
        return bottle.abort(404, "Not Found")
    size = path.stat().st_size
    bottle.response.headers["Accept-Ranges"] = "bytes"

    if "Range" not in bottle.request.headers and size <= config["static_size"]:
        return bottle.static_file(path.name, path.parent)

    content_type, _ = mimetypes.guess_type(path)
    if content_type:
        bottle.response.headers["Content-Type"] = content_type

    if "Range" in bottle.request.headers:
        start, end = parse_range(bottle.request.headers["Range"], size)
    else:
        start, end = 0, config["partial_size"] - 1
    if not (0 <= start <= end <= size - 1):
        return bottle.abort(416, "Range Not Satisfiable")

    length = end - start + 1
    bottle.response.status = 206
    bottle.response.headers["Content-Length"] = length
    bottle.response.headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    with open(path, "rb") as f:
        f.seek(start)
        return f.read(length)


@app.get("/explorer")
def get_explorer():
    def get_mime_types(path):
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type:
            main_type, sub_type = mime_type.split("/", maxsplit=1)
        else:
            main_type, sub_type = None, None
        return mime_type, main_type, sub_type

    def is_wanted(path):
        # using nonlocal filter_type, filter_name, case_sensitive
        mime_type, main_type, _ = get_mime_types(path)
        if filter_type is None:
            type_ok = True
        else:
            type_ok = mime_type in filter_type or main_type in filter_type
        if filter_name is None:
            name_ok = True
        elif case_sensitive:
            name_ok = filter_name in str(path.name)
        else:
            name_ok = filter_name.casefold() in str(path.name).casefold()
        return type_ok and name_ok

    def include_wanted(path):
        for _, _, f in path.walk():
            for i in f:
                if is_wanted(path / i):
                    return True
        return False

    def navigate_url(update, url="", prefix_url=None):
        q = query.copy()
        q.update(update)
        res = url + "?" + urllib.parse.urlencode(q)
        if prefix_url is None:
            return res
        return prefix_url + urllib.parse.quote(res)

    query = dict(bottle.request.query.decode())
    print("GET /explorer", query)
    if "path" not in query:
        return bottle.redirect(navigate_url({"path": config["home_path"]}, "/explorer"))
    path = canonical_path(query["path"])
    if config["limit_dir"] and not path.is_relative_to(config["limit_dir"]):
        return bottle.abort(403, "Forbidden")
    if not path.is_dir():
        return bottle.abort(404, "Not Found")

    file_url = query.get("file_url")
    show_hidden = "show_hidden" in query
    filter_name = query.get("filter_name")
    case_sensitive = "case_sensitive" in query
    filter_type = None
    if "filter_type" in query:
        filter_type = query["filter_type"].split(",")
        filter_type = [i.strip() for i in filter_type]
    recursive_filter = "recursive_filter" in query  # slow when dir huge

    folders, files = [], []
    for p in path.iterdir():
        if p.name.startswith(".") and not show_hidden:
            continue
        stat = p.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y/%m/%d %H:%M:%S")
        if p.is_dir():
            if not recursive_filter or include_wanted(p):
                url = navigate_url({"path": p})
                folders.append({"name": p.name, "mtime": mtime, "url": url})
            continue
        if is_wanted(p):
            mime_type, main_type, _ = get_mime_types(p)
            url = navigate_url({"path": p}, "/file", file_url)
            files.append(
                {
                    "url": url,
                    "name": p.name,
                    "mtime": mtime,
                    "mime_type": mime_type,
                    "main_type": main_type,
                    "size": "{:>6}".format(format_size(stat.st_size)),
                }
            )
    folders.sort(key=lambda folder: folder["name"])
    files.sort(key=lambda file: file["name"])
    path_parts = []
    for i, part in enumerate(path.parts):
        path_parts.append([navigate_url({"path": Path(*path.parts[: i + 1])}), part])
    return bottle.template(
        "file_explorer",
        path_parts=path_parts,
        path_sep=os.sep,
        file_url=file_url,
        show_hidden=show_hidden,
        filter_name=filter_name,
        case_sensitive=case_sensitive,
        filter_type=filter_type,
        recursive_filter=recursive_filter,
        folders=folders,
        files=files,
    )


def add_arguments(parser):
    parser.add_argument("--dir", help="limit access in dir (default: no limit)")
    parser.add_argument("--home", help="home path (default: user's home dir)")
    parser.add_argument("--static", help="max static file size (default: 16MiB)")
    parser.add_argument("--partial", help="default range length (default: 4MiB)")


def get_config(args, print_config=True):
    config["limit_dir"] = args.dir or config["limit_dir"]
    config["home_path"] = args.home or config["home_path"]
    config["static_size"] = args.static or config["static_size"]
    config["partial_size"] = args.partial or config["partial_size"]
    if config["limit_dir"]:
        config["limit_dir"] = str(canonical_path(config["limit_dir"]))
    if config["home_path"]:
        config["home_path"] = str(canonical_path(config["home_path"]))
    if config["static_size"]:
        config["static_size"] = parse_size(config["static_size"])
    if config["partial_size"]:
        config["partial_size"] = parse_size(config["partial_size"])
    if config["limit_dir"]:
        if not Path(config["home_path"]).is_relative_to(config["limit_dir"]):
            config["home_path"] = config["limit_dir"]
    if print_config:
        print("Streaming server config:", config)
        print()
    return config


if __name__ == "__main__":
    import argparse
    import bottle_app_runner

    @app.get("/")
    def get_home_page():
        print("GET /", bottle.request.query_string)
        return bottle.redirect("/explorer?" + bottle.request.query_string)

    parser = argparse.ArgumentParser(
        description="An HTTP server supporting range requests, with file explorer",
    )
    bottle_app_runner.add_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()
    get_config(args)

    bottle_app_runner.run_app(app, args)
