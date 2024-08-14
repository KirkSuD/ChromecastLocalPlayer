# -*-coding:utf-8;-*-

from __future__ import print_function

import json
import time
import mimetypes
# import random

import bottle
import pychromecast  # type: ignore
from bottle import request as req

HOST = "0.0.0.0"  # "localhost" #
PORT = 8080  # random.randint(3001, 9999) #
DEVICE_FRIENDLY_NAME = "Your device name here"
VERBOSE_ON = False

"""
Chromecast controller with Bottle Server UI
Requirements: bottle, pychromecast

/ccast/hello
/ccast/hello/<name>
Simple test

/
Redirect to /ccast

/ccast
Return a UI HTML
<friendly name>
<volume_mute_toggle_button> <volume_down_button> <volume_slider> <volume_up_button>
<rewind_button> <stop_button> <play/pause_button>
<-10sec_button> <time_slider> <+10sec_button>

/ccast/status
Return Chromecast status JSON with these keys:
friendly_name, volume_level, volume_muted, status_text, title, current_time, duration, player_state

/ccast/volume_mute_toggle
/ccast/volume_mute_true
/ccast/volume_mute_false

/ccast/volume_up
/ccast/volume_down
/ccast/volume_set/<volume>

/ccast/play_media?url=<>&content_type=<>&title=<>&thumb=<>&current_time=<>
/ccast/play
/ccast/rewind
/ccast/pause
/ccast/stop
/ccast/seek/<time>
"""
print()
print("Chromecast control app initializing...")
print()
print("Searching Chromecasts...")
while True:
    ccasts = pychromecast.get_chromecasts()
    if len(ccasts) > 0:
        break
    print("No Chromecasts found, will try again in 1 sec.")
    time.sleep(1)
ccasts_right_name = [
    cc for cc in ccasts if cc.device.friendly_name == DEVICE_FRIENDLY_NAME
]
if len(ccasts_right_name) == 1:
    ccast = ccasts_right_name[0]
else:
    for i, j in enumerate(ccasts):
        print(i, j)
    while True:
        try:
            ccast = ccasts[int(input("Please select a chromecast by number: ").strip())]
            break
        except ValueError:
            print("Please enter a number.")
        except IndexError:
            print("Please enter a correct number.")
        except KeyboardInterrupt:
            raise SystemExit
        except Exception:
            print("Unknown error occurred, please try again.")
print()
print("Chromecast:", ccast)
print()
print("Wait until device ready...")
ccast.wait()
medcon = ccast.media_controller
print("Device is ready.")


def get_status():
    ccast_status = ccast.status
    try:
        medcon.update_status()
    except pychromecast.error.UnsupportedNamespace as err:
        print("pychromecast.error.UnsupportedNamespace")
        print(err)
    medcon_status = medcon.status
    return {
        "friendly_name": ccast.device.friendly_name,
        "volume_level": ccast_status.volume_level,
        "volume_muted": ccast_status.volume_muted,
        "status_text": ccast_status.status_text,
        "title": medcon_status.title,
        "current_time": medcon_status.current_time,
        "duration": medcon_status.duration,
        "player_state": medcon_status.player_state,
    }


app = bottle.Bottle()


@app.hook("after_request")
def hide_server():
    bottle.response.headers["Server"] = (
        "Super Server v1.2.3"  # hide default bottle header
    )
    bottle.response.headers["X-Powered-By"] = "Taiwan NO.1 v9.4.8.7"  # Just 4 fun

    if VERBOSE_ON:
        print()
        print("======== after_request verbose info start ========")
        print("ccast:", ccast)
        print("ccast.status:", ccast.status)
        print("medcon:", medcon)
        print("medcon.status:", medcon.status)
        print("simplified status:", get_status())
        print("======== after_request verbose info finish ========")
        print()


@app.get("/ccast/hello")
@app.get("/ccast/hello/<name>")
def hello_name(name="World"):
    print()
    print("Hello %s!" % name)
    return bottle.template("<b>Hello {{name}}</b>!", name=name)


@app.get("/")
def home_page():
    print()
    print("Root route redirect.")
    bottle.redirect("/ccast")  # return "Home page."


@app.get("/ccast")
def ccast_app():
    return bottle.static_file("ChromeCastControl.html", root="./")


@app.get("/ccast/icon/<icon_path:path>")
def ccast_icon(icon_path):
    return bottle.static_file(icon_path, root="./icon")


@app.get("/ccast/status")
def get_ccast_status():
    res = get_status()
    res["success"] = True
    return json.dumps(res)


@app.post("/ccast/reboot")
def ccast_reboot():
    ccast.reboot()
    return json.dumps({"success": True})


@app.post("/ccast/volume_mute_toggle")
def volume_mute_toggle():
    ccast.set_volume_muted(not get_status()["volume_muted"])
    return json.dumps({"success": True})


@app.post("/ccast/volume_mute_true")
def volume_mute_true():
    ccast.set_volume_muted(True)
    return json.dumps({"success": True})


@app.post("/ccast/volume_mute_false")
def volume_mute_false():
    ccast.set_volume_muted(False)
    return json.dumps({"success": True})


@app.post("/ccast/volume_up")
def volume_up():
    new_volume = ccast.volume_up()
    return json.dumps({"success": True, "volume": new_volume})


@app.post("/ccast/volume_down")
def volume_down():
    new_volume = ccast.volume_down()
    return json.dumps({"success": True, "volume": new_volume})


@app.post("/ccast/volume_set/<volume:float>")
def volume_set(volume):
    new_volume = ccast.set_volume(volume)
    return json.dumps({"success": True, "volume": new_volume})


@app.post("/ccast/play_media")
def play_media():
    # https://stackoverflow.com/questions/13039411/how-to-retrieve-get-vars-in-python-bottle-app
    # http://bottlepy.org/docs/dev/tutorial.html#query-variables
    q = req.forms
    # play_media(url, content_type, title=None, thumb=None, current_time=0 ... )
    url = q.url
    content_type = q.content_type
    if not content_type:
        if url.endswith(".m3u"):
            content_type = "video/mpegurl"
        elif url.endswith(".m3u8"):
            content_type = "video/x-mpegurl"  # application/vnd.apple.mpegurl
        else:
            content_type, _content_encoding = mimetypes.guess_type(url)
            if content_type is None:
                content_type = "video/mp4"
    title = q.title if q.title else url.rsplit("/", 1)[-1]
    medcon.play_media(
        url=url,
        content_type=content_type,
        title=title,
        thumb=q.thumb,
        current_time=(q.current_time if q.current_time else 0),
    )
    # print("url:", q.url)
    # print("content type:", content_type)
    # print("title:", title)
    # print("thumb:", q.thumb)
    # print("current_time:", q.current_time)
    # medcon.play()
    return json.dumps({"success": True})


@app.post("/ccast/play")
def player_play():
    medcon.play()
    return json.dumps({"success": True})


@app.post("/ccast/rewind")
def player_rewind():
    medcon.rewind()
    return json.dumps({"success": True})


@app.post("/ccast/pause")
def player_pause():
    medcon.pause()
    return json.dumps({"success": True})


@app.post("/ccast/player_toggle")
def player_toggle():
    if get_status()["player_state"] == "PAUSED":
        action = "play"
        medcon.play()
    else:
        action = "pause"
        medcon.pause()
    return json.dumps({"success": True, "action": action})


@app.post("/ccast/stop")
def player_stop():
    medcon.stop()
    return json.dumps({"success": True})


@app.post("/ccast/seek/<time:float>")
def player_seek(time):
    medcon.seek(time)
    return json.dumps({"success": True})


@app.post("/ccast/seek_relative/<time:float>")
def player_seek_rel(time):
    stat = get_status()
    new_time = stat["current_time"] + time
    new_time = min(max(0, new_time), stat["duration"])
    medcon.seek(new_time)
    return json.dumps({"success": True, "new_time": new_time})


# @app.route("<full_path:path>")
# def not_found(full_path):
#     print()
#     print("Not found route.")
#     bottle.abort(404, "Your brain not found. :)\nWrong URL: '%s'" % full_path)

if __name__ == "__main__":
    server_url = "http://%s:%s" % (HOST, PORT)
    print()
    print("Server will run at %s" % server_url)

    if HOST == "0.0.0.0":
        open_url = "http://localhost:%s" % (PORT)
    else:
        open_url = server_url

    if input("Press Enter to open %s in browser..." % (open_url)) == "":
        try:
            from androidhelper import sl4a  # type: ignore
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
                    droid = sl4a.Android()
                    break
                except Exception:
                    print("Failed to init sl4a, will try again later.")
                    time.sleep(0.5)
            uri2open = open_url
            intent2start = droid.makeIntent(
                "android.intent.action.VIEW",
                uri2open,
                "text/html",
                None,
                ["android.intent.category.BROWSABLE"],
                None,
                None,
                None,
            )
            droid.startActivityForResultIntent(intent2start.result)
            print("Opened.")
    print()
    bottle.run(app, host=HOST, port=PORT)
