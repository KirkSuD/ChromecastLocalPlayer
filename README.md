# Chromecast Local Player

A simple Python server with web UI to control Chromecast,
    play local media files via Chromecast.

## Archived

Archived because I basically don't use Chromecast anymore.

If you somehow find this useful, you can fork the repo.  
Or use the code as long as it's non-commercial.

## Requirements

`pip install -r requirements.txt`:
- `bottle`: fast and simple micro-framework for python
- `pychromecast`: version 14.0.1 needs **Python 3.11+**
- `requests`: used to get media content-type from url
- `waitress`: default server, optional, you can use another server

## How to use

1. Run `chromecast_control.py`:
```
usage: chromecast_control.py [-h]
    [--server SERVER] [--host HOST] [--port PORT] [--open]
    [--under UNDER] [--home HOME] [--static STATIC] [--partial PARTIAL] [--disable]

An HTTP server to control Chromecast & cast local media

options:
  -h, --help         show this help message and exit
  --server SERVER    server to use (default: waitress)
  --host HOST        address to bind to (default: 0.0.0.0)
  --port PORT        port to bind to (default: 8080)
  --open             open browser (default: no)
  --under UNDER      limit access under path (default: no limit)
  --home HOME        home path (default: user's home dir)
  --static STATIC    max static file size (default: 16MiB)
  --partial PARTIAL  default range length (default: 4MiB)
  --disable          disable streaming server (default: no)
```

2. It would print something like this, visit the "internal IP URL":
```
Listen on: http://0.0.0.0:8080
Local URL: http://localhost:8080
Internal IP URL: http://192.168.XXX.XXX:8080
```

3. Wait until the search is done, then select a chromecast to connect to.
4. Click the "Cast" button.
5. Paste media URL to cast; or click the "File" button to browse local files.
6. In the file explorer, you can navigate and filter. Click a file to cast.

## Hot keys

- Left / Space / Right: seek -10s / pause,play / seek +10s
- P / S / N: previous / stop / next
- M / Down / Up: mute / volume down / volume up

## Docker

I wrote `Dockerfile`.  
I guess it would work, but it's never tested.

## Screenshots

- Main UI

<img src="https://i.imgur.com/i2s2MMK.png" alt="Chromecast control main UI">

- Cast UI

<img src="https://i.imgur.com/Je8KPeZ.png" alt="Chromecast control cast UI" width="400">

- File Explorer

<img src="https://i.imgur.com/NlIuQQh.png" alt="File explorer UI" width="400">

## How it works

`streaming_server.py` and `file_explorer.tpl` form a simple HTTP server  
    which supports streaming (HTTP range requests, 206 Partial Content).  
You can run it on your computer, and access files on another device within same LAN.

`chromecast_control.py` and `chromecast_control.html` form a Chromecast controller.  
`chromecast_control.html` gets chromecast status every 500ms, and updates the UI.

## To do

- better front-end
    - icons?
    - avoid changing input values when user interacting
    - remember status & check some preconditions?
    - better theme?
    - better layout?
- more testing
