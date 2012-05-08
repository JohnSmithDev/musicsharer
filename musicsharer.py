#!/usr/bin/env python
"""
A simplistic web server application to serve music files via HTTP
to browsers that support HTML5 audio.

Usage:
  cd <directory-containing-music-files>
  musicsharer.py [port] [comma-separated-file-suffixes]
Both arguments are optional, defaulting to 12345 and STANDARD_AUDIO_FORMATS
respectively.

See README.md or the GitHub page for more information.
"""

__author__ = "John Smith <code@john-smith.me>"

import logging
import sys
import os
import cgi
import urllib
import signal
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from CGIHTTPServer import CGIHTTPRequestHandler
import BaseHTTPServer
try:
    import HTTPRangeServer
    inherited_server = HTTPRangeServer.HTTPRangeRequestHandler
except ImportError:
    logging.warning("Unable to import HTTPRangeServer, using stdlib's " +
                    "SimpleHTTPServer")
    import SimpleHTTPServer
    inherited_server = SimpleHTTPServer.SimpleHTTPRequestHandler
import SocketServer

STANDARD_AUDIO_FORMATS = ["mp3", "ogg", "wav", "flac", "aac", "wma"]

# Whether to show log messages in the browser (useful for debugging Mobile
# Safari's many foibles)
CLIENT_DEBUG_MSGS = False

def is_matching_filename(filename, suffix_list):
    """
    Return True/False if filename's suffix is in suffix list.
    (Returns False if the file doesn't seem to have a suffix)
    Assumption: members of suffix_list are lower case
    """
    try:
        _, suffix = filename.rsplit(".", 1)
    except ValueError:
        logging.warning("Unable to obtain suffix for '%s'" % (filename))
        return False
    return suffix.lower() in suffix_list

def filter_audio_files_only(file_list, audio_formats=None):
    """
    Return filtered list of filenames only including audio files (based
    on filename suffix).  Optional argument 'audio_formats'
    allows specific formats to be defined, otherwise defaults
    will be used.
    """
    if audio_formats is None:
        audio_formats = STANDARD_AUDIO_FORMATS
    return [z for z in file_list if is_matching_filename(z, audio_formats)]

def file_list_to_html(file_list, dir_name=None):
    """
    Ideally this would be done with a proper templating system, but I'm
    trying to keep to Python stdlib
    """
    audio_files = filter_audio_files_only(file_list)

    bits = []
    if dir_name:
        title = "Directory: %s (%d music files)" % (dir_name, len(audio_files))
    else:
        title = "%d music files" % (len(audio_files))
    title = cgi.escape(urllib.unquote(title))
    bits.append("<!DOCTYPE html><head><title>%s</title>" % (title))
    bits.append("<link rel='stylesheet' type='text/css' href='_static_/player.css' />")
    bits.append("</head>")
    bits.append("<body><h1>%s</h1>" % (title))
    bits.append("<audio controls preload='auto'></audio>")
    bits.append("<button id='prev'>&lt;&lt;</button>")
    bits.append("<button id='next'>&gt;&gt;</button>")
    bits.append("<div id='debug' class='hidden'>Debug text appears here</div>");
    bits.append("<ol>")
    for i, af in enumerate(audio_files):
        bits.append("<li id='track-%d'>%s</li>" % 
                    (i, cgi.escape(urllib.unquote(af))))
    bits.append("</ol>")
    bits.append("<script>")
    bits.append("var trackNames = [%s];" % ",".join(['"%s"' % z 
                                                    for z in audio_files]))
    bits.append("var clientDebugging = %s;" % 
                ("true" if CLIENT_DEBUG_MSGS else "false"))
    bits.append("</script>")
    bits.append("<script src='_static_/player_control.js'></script>")
    bits.append("</body></html>\n")
    return "\n".join(bits)




class EnhancedRequestHandler(inherited_server):
    def list_directory(self, path):
        """
        Return a nice directory listing for a directory of MP3 files
        Derived from the code in SimpleHTTPServer.py
        """

        try:
            file_list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        file_list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write(file_list_to_html(file_list, path))
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    @staticmethod
    def get_script_dir():
        """
        Via  http://code.activestate.com/recipes/474083-get-the-path-of-the-currently-executing-python-scr/
        """
        return os.path.dirname(os.path.realpath(__file__))

    def translate_path(self, path):
        """
        Override to enable serving of the server's own static files
        """
        default_path = \
            inherited_server.translate_path(self, path)
        if not os.path.exists(default_path) and "_static_" in default_path:
            return os.path.join(EnhancedRequestHandler.get_script_dir(), 
                                "resource", 
                                os.path.basename(default_path))
        else:
            return default_path

def clean_shutdown_closure(daemon):
    def clean_shutdown_handler(*args): # signnum, frame
        _ = len(args) # just to stop pychecker whinging
        logging.error("Shutdown signal handler called")
        daemon.server_close()
        logging.error("Exiting")
        sys.exit(1)
    return clean_shutdown_handler

def main(port=12345):
    Handler = EnhancedRequestHandler
    httpd = SocketServer.TCPServer(("", port), Handler)
    shutdown_func = clean_shutdown_closure(httpd)
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, shutdown_func)
    logging.info("Running on port %d, pid %d" % (port, os.getpid()))
    try:
        httpd.serve_forever(1)
    except:
        # Use .server_close(), *not* .shutdown() - see:
        # http://www.gossamer-threads.com/lists/python/bugs/748420
        httpd.server_close()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s %(message)s')
    logging.getLogger().setLevel(logging.DEBUG)

    if len(sys.argv) > 2:
        STANDARD_AUDIO_FORMATS = sys.argv[2].split(",")

    if len(sys.argv) > 1:
        main(int(sys.argv[1]))
    else:
        main()


