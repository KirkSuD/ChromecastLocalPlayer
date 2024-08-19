from __future__ import annotations

import json
import uuid
import dataclasses
from pathlib import Path
from datetime import datetime

import bottle
import requests
import pychromecast

# import pychromecast.controllers
import pychromecast.controllers.media
import pychromecast.controllers.receiver

app = bottle.Bottle()
casts: dict[str, pychromecast.Chromecast] = {}
browser: pychromecast.discovery.CastBrowser | None = None
cast: pychromecast.Chromecast | None = None
media: pychromecast.controllers.media.MediaController | None = None


@app.get("/cast/search")
def search_chromecast():
    global casts, browser
    print("GET /cast/search", bottle.request.query_string)
    if "force" in bottle.request.query and browser:
        pychromecast.discovery.stop_discovery(browser)
        casts, browser = None, None
    if not casts:
        chromecasts, browser = pychromecast.get_chromecasts()
        casts = {c.cast_info.friendly_name: c for c in chromecasts}
    return {"names": sorted(casts.keys())}


@app.get("/cast/connect")
def connect_chromecast():
    global cast, media
    print("GET /cast/connect", bottle.request.query_string)
    name = bottle.request.query.name
    if name not in casts:
        return {"error": "UnknownName"}
    if cast and cast.cast_info.friendly_name != name:
        cast.disconnect()
        cast, media = None, None
    if not media:
        cast = casts[name]
        cast.wait()
        media = cast.media_controller
    return {}


@app.get("/cast/disconnect")
def disconnect_chromecast():
    global cast, media
    print("GET /cast/disconnect")
    if cast:
        cast.disconnect()
        cast, media = None, None
    return {}


@app.get("/cast/status")
def get_status():
    def to_json_serializable(obj, raise_error=False):
        basic_types = {str, int, float, bool, type(None)}
        if isinstance(obj, list):
            if len(obj) == 0:
                return obj
            res = []
            for i in obj:
                if type(i) not in basic_types:
                    i = to_json_serializable(i)
                res.append(i)
            if res:
                return res
        elif isinstance(obj, dict):
            if len(obj) == 0:
                return obj
            res = {}
            for k, i in obj.items():
                if type(i) not in basic_types:
                    i = to_json_serializable(i)
                res[k] = i
            if res:
                return res
        elif isinstance(obj, set):
            return to_json_serializable(list(obj))
        elif dataclasses.is_dataclass(obj):
            return to_json_serializable(dataclasses.asdict(obj))
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif raise_error:
            raise TypeError(f"Can't make this type json serializable: {type(obj)}")
        else:
            return f"<<non-serializable: {type(obj).__qualname__}>>"

    print("GET /cast/status")
    if not cast or not media:
        return {"error": "NotConnected"}
    try:
        media.update_status()
    except Exception:
        pass
    cast_info: pychromecast.models.CastInfo | None = cast.cast_info
    cast_status: pychromecast.controllers.receiver.CastStatus | None = cast.status
    media_status: pychromecast.controllers.media.MediaStatus = media.status

    media_info = {  # from MediaStatus.__repr__() info
        "metadata_type": media_status.metadata_type,
        "title": media_status.title,
        "series_title": media_status.series_title,
        "season": media_status.season,
        "episode": media_status.episode,
        "artist": media_status.artist,
        "album_name": media_status.album_name,
        "album_artist": media_status.album_artist,
        "track": media_status.track,
        "subtitle_tracks": media_status.subtitle_tracks,
        "images": media_status.images,
        "supports_pause": media_status.supports_pause,
        "supports_seek": media_status.supports_seek,
        "supports_stream_volume": media_status.supports_stream_volume,
        "supports_stream_mute": media_status.supports_stream_mute,
        "supports_skip_forward": media_status.supports_skip_forward,
        "supports_skip_backward": media_status.supports_skip_backward,
    }
    media_info.update(media_status.__dict__)

    res = {"info": cast_info, "cast": cast_status, "media": media_info}
    res = to_json_serializable(res)
    return res


def play_toggle():
    media_status = get_status()["media"]
    if media_status["player_state"] == "PAUSED":
        media.play()
    elif media_status["player_state"] == "PLAYING":
        media.pause()


def seek_relative(delta: float):
    media_status = get_status()["media"]
    position = media_status["current_time"] + delta
    position = min(max(0, position), media_status["duration"])
    media.seek(position)


def reset_playback_rate():
    media.set_playback_rate(1)


@app.get("/cast/<function_name>")
def run_function(function_name):
    print(f"GET /cast/{function_name}", bottle.request.query_string)
    if not cast:
        return {"error": "NotConnected"}

    functions = [
        [cast.set_volume, dict(volume=float), float],
        [cast.set_volume_muted, dict(muted=bool), None],
        [cast.volume_up, dict(delta=float), float],
        [cast.volume_down, dict(delta=float), float],
        [media.play, {}, None],
        [media.pause, {}, None],
        [play_toggle, {}, None],
        [media.stop, {}, None],
        [media.rewind, {}, None],
        [media.skip, {}, None],
        [media.seek, dict(position=float), None],
        [seek_relative, dict(delta=float), None],
        [media.set_playback_rate, dict(playback_rate=float), None],
        [reset_playback_rate, {}, None],
        [media.queue_next, {}, None],
        [media.queue_prev, {}, None],
        [media.enable_subtitle, dict(track_id=int), None],
        [media.disable_subtitle, {}, None],
        [media.block_until_active, {}, None],
        [
            media.play_media,
            dict(
                url=str,
                content_type=str,
                title=str,
                thumb=str,
                current_time=float,
                autoplay=bool,
                stream_type=str,
                metadata=dict,
                subtitles=str,
                subtitles_lang=str,
                subtitles_mime=str,
                subtitle_id=int,
                enqueue=bool,
                media_info=dict,
            ),
            None,
        ],
    ]
    functions = {f.__name__: [f, params, ret] for f, params, ret in functions}
    if function_name not in functions:
        return {"error": "UnknownFunction"}

    func, params, _ = functions[function_name]
    query = dict(bottle.request.query.decode())
    args = {}
    for p, t in params.items():
        if p not in query:
            if function_name != "play_media" or p == "url":
                raise ValueError(f"Function {function_name} missing param: {p}")
            continue
        q = query[p]
        if t is bool:
            # 0/!0 true/false True/False empty/non-empty
            if q.lower() in ["true", "false"]:
                a = q.lower() == "true"
            else:
                try:
                    a = int(q) != 0
                except ValueError:
                    a = len(q) > 0
        elif t is int:
            a = int(q)
        elif t is float:
            a = float(q)
        elif t is str:
            a = q
        elif t is dict:
            a = json.loads(q)
        else:
            raise TypeError(f"Unknown param type: {t}")
        args[p] = a

    if function_name == "play_media" and "content_type" not in args:
        head_response = requests.head(args["url"])
        args["content_type"] = head_response.headers.get("Content-Type", "")

    res = func(**args)
    if res is None:
        return {}
    return {"result": res}


@app.get("/cast")
def get_app():
    print("GET /cast")
    return bottle.static_file("chromecast_control.html", root=Path(__file__).parent)


if __name__ == "__main__":
    import argparse
    import bottle_app_runner
    import streaming_server

    @app.get("/")
    def get_home_page():
        print("GET /")
        return bottle.redirect("/cast")

    parser = argparse.ArgumentParser(
        description="An HTTP server to control Chromecast & cast local media",
    )
    bottle_app_runner.add_arguments(parser)
    streaming_server.add_arguments(parser)
    parser.add_argument(
        "--disable", action="store_true", help="disable streaming server (default: no)"
    )
    args = parser.parse_args()
    if not args.disable:
        streaming_server.get_config(args)
        app.merge(streaming_server.app)

    bottle_app_runner.run_app(app, args)
