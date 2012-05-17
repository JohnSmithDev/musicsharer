# musicsharer

A very simplistic Python script to serve music files via HTTP to
browser clients that support HTML5 audio.  The client-side code will
automatically play all the tracks in a directory in sequence.

This is intended for single-user use on a LAN - if you want something
to share files over a wider network and/or to multiple users, you'd be
much better off using a "proper" server such as Apache or nginx.

## Basic usage

The most basic usage is to open up a terminal window, and

    cd <directory-containing-audio-files>
    musicsharer.py

Then open up your browser and enter the URL

    http://{address-of-server}:12345

The first track should play automatically on most browsers, otherwise you'll
have to click/press the play 'button' on the audio controls (looking at you,
Mobile Safari).

The default port that the server serves from is 12345; if you prefer to
use a different port, then pass it as an argument to the script.  e.g.

    musicsharer.py 80

Obviously you need to have the user privileges to serve on that port, to
not have an existing process serving on that port, to not have firewall
rules getting in the way, etc.

## Motivation and use cases

Most of my music collection is on my Linux machine(s), so using iTunes
(which I despise in general anyway) to transfer music to my iOS devices
is a no-no.  In any case, my collection is far bigger than would fit on my
Mac or my iOS devices, so I wanted an alternative solution.  Using Mobile
Safari's HTML audio support seemed a reasonable option.

As music files are spread out over a number of machines, with varying
operating systems, I also wanted something fair

However, this raises a couple of gotchas that may not be immediately
obvious:

* Mobile Safari doesn't like playing media elements without some form
  of user interaction.  This makes things a bit awkward if you want to
  play multiple tracks (e.g. the tracks of an album).  JavaScript hackery
  can address most, but not all, of these problems.
* For certain MP3 files, Mobile Safari can only handle downloading them
  in pieces, using the Range header in HTTP requests.  Unfortunately
  SimpleHTTPServer in Python's stdlib doesn't support this header, instead
  serving the entire file, which causes Mobile Safari to fail with a fairly
  unhelpful error message.

## Bugs and ToDo

Write some tests, primarily to prove the Range header processing.  (This
will need me to read and understand the HTTP spec properly, the support at
present is purely based on empirical observations of what browsers send, and
I see from the spec there are other variations that my code doesn't support:
http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.35 )

Make the client UI nicer - there hasn't been any effort expended in this area,
as you'll quickly discover ;-)

Allow directory navigation from the client.

Optionally allow some external programs (e.g. mencoder, ffmpeg?) to transcode
files into a format a client browser supports (e.g. MP3 to OGG for Firefox,
Opera; OGG to MP3 for Safari), similar to how a DNLA server works AFAIK.

Automatic advancing to the next track doesn't work in the iOS 4 version of
Mobile Safari.  Given how cantankerous Mobile Safari is with audio/video
elements, I'm not inclined to waste time trying to fix this - I'll only be
supporting the current version.

