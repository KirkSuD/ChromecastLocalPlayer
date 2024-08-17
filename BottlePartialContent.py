import os
import socket
import mimetypes

import bottle

HOST = "0.0.0.0"  # "localhost" #
PORT = 8080  # random.randint(3001, 9999) #
MAX_PARTIAL_SIZE = 4 * 1024 * 1024  # 4 MB
home_path = "C:/Users/User/Videos"  # "/sdcard"

if home_path.startswith("/"):
    home_path = home_path[1:]
home_path = "/drive/" + home_path
"""
Simple HTTP Server with Partial Content Support
New version with template
"""


def get_internal_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    res = s.getsockname()[0]
    s.close()
    return res


app = bottle.Bottle()


@app.get("/hello")
@app.get("/hello/<name>")
def hello_name(name="World"):
    print()
    print("Hello %s!" % name)
    return bottle.template("<b>Hello {{name}}</b>!", name=name)


@app.get("/drive/<drive_path:path>")
def drive_app(drive_path):
    def preprocess_path(full_path):
        if os.name == "nt":
            full_path = full_path.replace("/", "\\")
        elif not full_path.startswith("/"):
            full_path = "/" + full_path
        return full_path

    def walk_once(walk_path):
        for _, dirs, files in os.walk(walk_path):
            return sorted(dirs), sorted(files)

    def isvid(fpath):
        ftype, _ = mimetypes.guess_type(fpath)
        if ftype is not None and ftype.split("/")[0] == "video":
            return True
        return False

    def parse_range(range_str):
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/206
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range
        range_str = range_str.strip()
        if any(
            map(lambda x: range_str.count(x[0]) != x[1], [("=", 1), ("-", 1), (",", 0)])
        ):
            return None, None
        eq_pos = range_str.find("=")
        if range_str[:eq_pos].strip() != "bytes":
            return None, None
        rstart, rend = range_str[eq_pos + 1 :].split("-")
        try:
            rstart = int(rstart.strip())
        except ValueError:
            rstart = None
        try:
            rend = int(rend.strip())
        except ValueError:
            rend = None
        return rstart, rend

    print()
    print("Drive path:", drive_path)
    full_path = preprocess_path(drive_path)
    print("Processed path:", full_path)
    if not os.path.exists(full_path):
        bottle.abort(404, "Drive path not found: " + full_path)
    if os.path.isdir(full_path):
        print("Is a dir.")
        updir, curdir = os.path.split(full_path)
        dirs, files = walk_once(full_path)
        vids = (f for f in files if isvid(os.path.join(full_path, f)))
        others = (f for f in files if not isvid(os.path.join(full_path, f)))
        links = []
        cur = "/drive"
        link_start = os.sep if full_path.startswith(os.sep) else ""
        for d in full_path.split(os.sep):
            if d == "":
                continue
            cur += "/" + d
            links.append('<a href="%s">%s</a>' % (cur, d))
        res = "<h2>%s</h2>" % (link_start + "/".join(links))
        res += "<h3>"
        res += "<a href=\"javascript:window.open('/ccast', '_blank')\">Chromecast</a>"
        res += " | "
        res += '<a href="./%s">Refresh (F5)</a>' % (curdir)
        res += " | "
        res += '<a href="../%s">Go up (..)</a>' % (os.path.split(updir)[1])
        res += "</h3>"
        for type_name, files in [
            ("Videos", vids),
            ("Folders", dirs),
            ("Others", others),
        ]:
            res += "<h3>%s:</h3>" % (type_name)
            for f in files:
                if type_name == "Videos":
                    res += '<a href="./%s/%s">%s</a>' % (curdir, f, f)
                    res += (
                        '<button type="button" onclick="play_media(\'%s\')" >Play</button><br>'
                        % (
                            "http://%s:%s/drive/" % (get_internal_ip(), PORT)
                            + drive_path
                            + "/"
                            + f
                        )
                    )
                else:
                    res += '<a href="./%s/%s">%s</a><br>' % (curdir, f, f)
        return bottle.template("BottlePartialContentDirView", body_string=res)
    elif os.path.isfile(full_path):
        print("Is a file.")
        file_size = os.path.getsize(full_path)
        if not isvid(full_path) or file_size < MAX_PARTIAL_SIZE:
            path_root, path_name = os.path.split(full_path)
            return bottle.static_file(path_name, root=path_root)
        if "Range" in bottle.request.headers:
            rstart, rend = parse_range(bottle.request.headers["Range"])
            if rstart is None and rend is None:
                return bottle.abort(416, "Range Not Satisfiable")
            elif rstart is None:
                if file_size < rend:
                    return bottle.abort(416, "Range Not Satisfiable")
                rlen = rend
                rstart = file_size - rend
            elif rend is None:
                if file_size <= rstart:
                    return bottle.abort(416, "Range Not Satisfiable")
                rlen = min(file_size - rstart, MAX_PARTIAL_SIZE)
                rend = rstart + rlen - 1
            else:
                rlen = min(rend - rstart + 1, MAX_PARTIAL_SIZE)
        else:
            rstart = 0
            rlen = MAX_PARTIAL_SIZE
            rend = rstart + rlen - 1
        bottle.response.headers["Content-Range"] = "bytes %s-%s/%s" % (
            rstart,
            rend,
            file_size,
        )
        bottle.response.status = 206
        content_type, content_encoding = mimetypes.guess_type(full_path)
        if content_type is None:
            content_type = "application/octet-stream"
        bottle.response.headers["Content-Type"] = content_type
        if content_encoding is not None:
            bottle.response.headers["Content-Encoding"] = content_encoding
        with open(full_path, "rb") as rf:
            rf.seek(rstart)
            return rf.read(rlen)
    else:
        print("Path exists, but not a dir or a file. Skipped.")
        return "Path exists, but not a file or a folder."


@app.get("/")
def home_page():
    print()
    print("Root route redirect.")
    bottle.redirect(home_path)  # return "Home page."


@app.route("<full_path:path>")
def not_found(full_path):
    print()
    print("Not found route.")
    bottle.abort(404)


if __name__ == "__main__":
    server_url = "http://%s:%s" % (HOST, PORT)
    print()
    print("Max content length:", MAX_PARTIAL_SIZE)
    print("Home path:", home_path)
    print("Server will run at %s" % server_url)

    if HOST == "0.0.0.0":
        open_url = "http://localhost:%s" % (PORT)
    else:
        open_url = server_url

    print()
    bottle.run(app, host=HOST, port=PORT)
