# Chromecast Local Player

A simple Python server with web UI to control Chromecast,
    play local media files via Chromecast.

(Note: this is legacy code, which probably requires an older `pychromecast`.  
Back then `pychromecast` only needs py 3.4+, now it needs py 3.11+.  
A new version is under construction, and will be pushed if finished.)

## Requirements

* bottle & pychromecast (`pip install -r requirements.txt`)
* (Optional) Search and download some icons, see below.

## How to use

First, some one-time configuration is needed:

1. Configure the `home_path` variable in `BottlePartialContent.py` as it is used to redirect from the root of the server. (Or you'll have to type the path you want manually each time you run this)
2. Configure the `DEVICE_FRIENDLY_NAME` variable in `ChromeCastControl.py`. Just type your Chromecast's name. (It depends on your Chromecast's settings. It may be something like "living room" or "客廳".) This is used to search your Chromecast.
3. Configure the `PORT` variable in `Main.py`. (Or just use the default 8080) This is the port you'll connect.

Then, everytime you run you just:

1. Make sure your computer and Chromecast are in the same network. (Same Wi-fi, basically.)
2. Run `Main.py`. It'll search your Chromecast, then press enter to open the browser.
3. Enjoy the powerful Chromecast controller and player.

## How it works

`BottlePartialContent.py` and `BottlePartialContentDirView.tpl` form a simple HTTP server which
 supports streaming(partial content, the `206` HTTP status code).  
You can run it on your computer, and watch the video in it on your cellphone!

`ChromeCastControl.py` and `ChromeCastControl.html` form a Chromecast controller,
 a simple web interface to control Chromecast.

`Main.py` combines these two independent scripts, forms an app which lets you
 play the videos in your computer. The former hosts the file, and the latter tells Chromecast where
 to play the video.

## Questions that may be asked

**On which platforms can I run this?**

Basically every platforms with Python 3.4+.  
Though I only tested on Windows, Android Qpython3 and Termux.  
There are browser opening features for PC / sl4a / Termux in `Main.py`.

**Why the `icon` folder is empty?**

I don't own any icons. I'm afraid that there would be copyright issues if I upload them.  
The icons' filenames used in `ChromeCastControl.html` are:

    10sec_backward-512.png
    10sec_forward-512.png
    minus.png
    pause.png
    play.png
    plus.png
    rewind.png
    stop.png
    volOFF.png
    volON.png

## TODO

* The code is messy; clean it!
* It prints some exceptions; fix it! (But I haven't encountered any bugs / unexpected exiting. The program runs smoothly.)
