"""
An extension of the Python stdlib SimpleHTTPServer module, to
support the "Range" header in HTTP requests, as needed by iOS Safari
to support (some) MP3s.

Some methods are modifications to the original SimpleHTTPServer that is
part of the Python stdlib.  This uses the versions that ship with Python
2.7 on Fedora 15.

Licensed under BSD 2-Clause License

"""
__version__ = "0.1"

__author__ = "John Smith <code@john-smith.me>"

import os
import BaseHTTPServer
import SimpleHTTPServer

# Additions for handling Range: header
import logging
import re

class HTTPRangeRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    """
    Extension of SimpleHTTPServer.SimpleHTTPRequestHandler to support
    the Range header in HTTP requests.  (As needed for serving certain
    MP3 files to Mobile Safari.
    """

    server_version = "HTTPRangeServer/" + __version__

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            if self.range_from is not None and self.range_to is not None:
                self.copy_chunk(f, self.wfile)
            else:
                self.copyfile(f, self.wfile)
            f.close()

    def copy_chunk(self, in_file, out_file):
        """
        Copy a chunk of in_file as dictated by self.range_[from|to]
        to out_file.
        NB: range values are inclusive so 0-99 => 100 bytes
        Neither of the file objects are closed when the
        function returns.  Assumes that in_file is open
        for reading, out_file is open for writing.
        If range_tuple specifies something bigger/outside
        than the size of in_file, out_file will contain as
        much content as matches.  e.g. with a 1000 byte input,
        (500, 2000) will create a 500 byte long file
        (2000, 3000) will create a zero length output file
        """

        in_file.seek(self.range_from)
        # Add 1 because the range is inclusive
        left_to_copy = 1 + self.range_to - self.range_from

        bytes_copied = 0
        while bytes_copied < left_to_copy:
            read_buf = in_file.read(left_to_copy)
            if len(read_buf) == 0:
                break
            out_file.write(read_buf)
            bytes_copied += len(read_buf)
        return bytes_copied

    def parse_range_header(self):
        """
        Return a 2-element tuple containing the requested Range offsets
        in bytes.  If no Range explicitly requested, or is "0-", or fails
        to parse, returns (None, None)
        """
        range_header = self.headers.getheader("Range")
        if range_header is None:
            return (None, None)
        if not range_header.startswith("bytes="):
            logging.warning("Don't know how to parse Range: %s [1]" % 
                            (range_header))
            return (None, None)
        regex = re.compile(r"^bytes=(\d+)\-(\d+)?")
        rangething = regex.search(range_header)
        if rangething:
            logging.debug("Requested range is [%s]-[%s]" % 
                          (rangething.group(1), rangething.group(2)))
            from_val = int(rangething.group(1))
            if rangething.group(2) is not None:
                return (from_val, int(rangething.group(2)))
            else:
                if from_val == 0:
                    return (None, None)
                else:
                    return (from_val, None)
        else:
            logging.warning("Don't know how to parse Range: %s [2]" % 
                            (range_header))
            return (None, None)

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        self.range_from, self.range_to = self.parse_range_header()
	path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        if self.range_from is not None and self.range_to is not None:
		self.send_response(206)
	else:
		self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        if self.range_from is not None and self.range_to is not None:
            # TODO: Should also check that range is within the file size
            self.send_header("Content-Range",
                             "bytes %d-%d/%d" % (self.range_from,
                                                 self.range_to,
                                                 fs[6]))
            # Add 1 because ranges are inclusive
            self.send_header("Content-Length", 
                             (1 + self.range_to - self.range_from))
        else:
            self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

def test(HandlerClass = HTTPRangeRequestHandler,
         ServerClass = BaseHTTPServer.HTTPServer):
    BaseHTTPServer.test(HandlerClass, ServerClass)

if __name__ == '__main__':
    test()
