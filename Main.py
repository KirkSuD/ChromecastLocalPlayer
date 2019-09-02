#-*-coding:utf-8;-*-

from __future__ import print_function

import bottle, pychromecast
from bottle import request as req

import json, mimetypes #os, random

HOST = "0.0.0.0" # "localhost" # 
PORT = 8080 # random.randint(3001, 9999) # 

"""
Chromecast controller with Bottle Server UI
Requirements: bottle, pychromecast
"""

if __name__ == "__main__":
    try:              input = raw_input
    except NameError: pass

    print()
    print("Chromecast control app & local server by pychromecast & bottle.")

    from BottlePartialContent import app as local_server_app
    from ChromeCastControl import app as ccast_control_app

    server_url = "http://%s:%s" % (HOST,PORT)
    print()
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
                print("Trying Redirect.html + termux-share")
                with open("./Redirect.html", "w") as wf:
                    html="""<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="0; url=%s" />
</head>
<body>
</body>
</html>
""" % open_url
                    wf.write(html)
                import subprocess
                if subprocess.call(["termux-share","./Redirect.html"]):
                    print("Opened.")
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
    ccast_control_app.merge(local_server_app)
    bottle.run(ccast_control_app, host=HOST, port=PORT)
