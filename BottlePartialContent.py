#-*-coding:utf-8;-*-

from __future__ import print_function

import bottle

import os, mimetypes, socket

HOST = "0.0.0.0" # "localhost" # 
PORT = 8080 # random.randint(3001, 9999) # 
MAX_PARTIAL_SIZE = 4 * 1024 * 1024 ## 4 MB
home_path = "C:/Users/User/Videos" # "/sdcard"

if home_path.startswith("/"):
    home_path = home_path[1:]
home_path = "/drive/" + home_path
"""
Simple HTTP Server with Partial Content Support
New version with template
"""

"""
def get_internal_wifi_ip():
    
    ## Get internal Wi-Fi IPv4 IP by calling ipconfig
    ## Only tested on Windows
    ## This solution without SOCKet SUCKs!
    
    ipconfig = subprocess.check_output(["ipconfig"]).decode("cp950")
    wifi = ipconfig.find("無線區域網路介面卡 Wi-Fi:")
    ipv4 = ipconfig.find("IPv4 位址", wifi)
    return ipconfig[ipv4: ipconfig.find("\r", ipv4)].rsplit(" ",1)[-1]
"""

def get_internal_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    res = s.getsockname()[0]
    s.close()
    return res


app = bottle.Bottle()

@app.hook('after_request')
def hide_server():
    bottle.response.headers["Server"] = "Super Server v1.2.3" ## hide default bottle header
    bottle.response.headers["X-Powered-By"] = "Your parents v9.8.7" ## Just 4 fun

@app.get("/hello")
@app.get("/hello/<name>")
def hello_name(name="World"):
    print()
    print("Hello %s!" % name)
    return bottle.template('<b>Hello {{name}}</b>!', name=name)

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
        ## https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/206
        ## https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range
        range_str = range_str.strip()
        if any(map(lambda x: range_str.count(x[0])!=x[1], [("=",1),("-",1),(",",0)])):
            return None, None
        eq_pos = range_str.find("=")
        if range_str[:eq_pos].strip() != "bytes":
            return None, None
        rstart, rend = range_str[eq_pos+1:].split("-")
        try:               rstart = int(rstart.strip())
        except ValueError: rstart = None
        try:               rend = int(rend.strip())
        except ValueError: rend = None
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
        vids = (f for f in files if isvid(os.path.join(full_path,f)))
        others = (f for f in files if not isvid(os.path.join(full_path,f)))
        links = []
        cur = "/drive"
        link_start = os.sep if full_path.startswith(os.sep) else "" ## not SAO :)
        for d in full_path.split(os.sep):
            if d == "": continue
            cur += "/" + d
            links.append('<a href="%s">%s</a>' % (cur, d))
        res = '<h2>%s</h2>' % (link_start + "/".join(links))
        res += '<h3>'
        res += '<a href="javascript:window.open(\'/ccast\', \'_blank\')">Chromecast</a>'
        res += ' | '
        res += '<a href="./%s">Refresh (F5)</a>' % (curdir)
        res += ' | '
        res += '<a href="../%s">Go up (..)</a>' % (os.path.split(updir)[1])
        res += '</h3>'
        for type_name, files in [("Videos", vids), ("Folders", dirs), ("Others", others)]:
            res += "<h3>%s:</h3>" % (type_name)
            for f in files:
                if type_name == "Videos":
                    res += '<a href="./%s/%s">%s</a>' % (curdir, f, f)
                    res += '<button type="button" onclick="play_media(\'%s\')" >Play</button><br>' % \
                        ("http://%s:%s/drive/" % (get_internal_ip(),PORT) + drive_path + "/" + f)
                else:
                    res += '<a href="./%s/%s">%s</a><br>' % (curdir, f, f)
        return bottle.template("BottlePartialContentDirView", body_string=res)
    elif os.path.isfile(full_path):
        print("Is a file.")
        file_size = os.path.getsize(full_path)
        if file_size < MAX_PARTIAL_SIZE:
            path_root, path_name = os.path.split(full_path)
            return bottle.static_file(path_name, root = path_root)
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
        bottle.response.headers["Content-Range"] = "bytes %s-%s/%s" % (rstart, rend, file_size)
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
    bottle.redirect(home_path) #return "Home page."

# @app.route("/404")
# def return_404():
#     print()
#     print("404 for fun.")
#     bottle.response.status = "404 Your brain not found!"
#     return "<h1>404 Your brain not found!</h1><h1>Did you miss it somewhere?</h1>"

# @app.route("/418")
# def return_418():
#     print()
#     print("418 I'm a teapot for fun.")
#     bottle.abort(418, "I'm a teapot!\nDon't attempt to brew coffee with me!")

@app.route("<full_path:path>")
def not_found(full_path):
    print()
    print("Not found route.")
    bottle.abort(404, "Your brain not found. :)\nWrong URL: '%s'" % full_path)

if __name__ == "__main__":
    try:              input = raw_input
    except NameError: pass

    server_url = "http://%s:%s" % (HOST,PORT)
    print()
    print("Max content length:", MAX_PARTIAL_SIZE)
    print("Home path:", home_path)
    print("Server will run at %s" % server_url)

    if HOST == "0.0.0.0":
        open_url = "http://localhost:%s" % (PORT)
    else:
        open_url = server_url

    if input("Press Enter to open %s in browser..." % (open_url)) == "":
        try:
            from androidhelper import sl4a
        except ImportError:
            print("Trying webbrowser...")
            import webbrowser
            if webbrowser.open(open_url):
                print("Opened.")
            else:
                print("Guess something went wrong, maybe not opened.")
        else:
            print("Trying sl4a...")
            import time
            while True:
                try:
                    droid=sl4a.Android()
                    break
                except:
                    print("Failed to init sl4a, will try again later.")
                    time.sleep(0.5)
            uri2open = open_url
            intent2start = droid.makeIntent("android.intent.action.VIEW", uri2open, "text/html", None, [u"android.intent.category.BROWSABLE"], None, None, None)
            droid.startActivityForResultIntent(intent2start.result)
            print("Opened.")
    print()
    bottle.run(app, host=HOST, port=PORT)
