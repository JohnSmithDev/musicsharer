#!/usr/bin/env python
"""
Tests for HTTPRangeServer.py

Example usage:
  python -m musicsharer.tests.test_HttpRangeServer
"""

__author__ = "John Smith, 2013 <code@john-smith.me>"

import pdb
import os
import logging
import sys

import unittest

import threading
import SocketServer # renamed as socketserver in Python 3
import signal
import urllib
import urllib2

from ..HTTPRangeServer import HTTPRangeRequestHandler, parse_range_header

SERVER_NAME = "127.0.0.1"
TEST_PORT = 12345


class TestRangeParsing(unittest.TestCase):
    def test_no_range(self):
        ret = parse_range_header("", 999)
        self.assertIsNone(ret[0])
        self.assertIsNone(ret[1])

        ret = parse_range_header(None, 999)
        self.assertIsNone(ret[0])
        self.assertIsNone(ret[1])

    def test_simple_range(self):
        ret = parse_range_header("bytes=10-20", 999)
        self.assertEquals(ret[0], 10)
        self.assertEquals(ret[1], 20)

    def test_from_midpoint_to_end(self):
        ret = parse_range_header("bytes=10-", 999)
        self.assertEquals(ret[0], 10)
        self.assertEquals(ret[1], 998)

    def test_bytes_from_end(self):
        ret = parse_range_header("bytes=-20", 999)
        self.assertEquals(ret[0], 979)
        self.assertEquals(ret[1], 998)



class MyTCPServer(SocketServer.TCPServer):
    """
    From http://stackoverflow.com/questions/10613977/ - response from
    Nick Craig-Wood
    """
    allow_reuse_address = True

def clean_shutdown_closure(daemon):
    def clean_shutdown_handler(*args): # signnum, frame
        _ = len(args) # just to stop pychecker whinging
        logging.error("Shutdown signal handler called")
        daemon.server_close()
        logging.error("Exiting")
        sys.exit(1)
    return clean_shutdown_handler


class TestsWithActualServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.dirname(__file__)
        cls.test_filename = "testfile.txt"
        with open(os.path.join(cls.test_dir, cls.test_filename), "r") as f:
            cls.test_content = f.read()

        # Q: Is there a better way to specify the serving directory to
        # SimpleHTTPServer?
        os.chdir(cls.test_dir)

        cls.httpd = MyTCPServer(("", TEST_PORT),
                                HTTPRangeRequestHandler)

        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.server_thread.daemon = True
        print("About to start serving thread..")
        cls.server_thread.start()
        print("Server thread running..")
        cls.url = "http://%s:%d/%s" % (SERVER_NAME, TEST_PORT,
                                        cls.test_filename)

    @classmethod
    def tearDownClass(cls):
        # print("Sleeping...")
        # import time
        # time.sleep(60)
        # print("About to close..")
        cls.httpd.server_close()
        cls.httpd.shutdown()
        # print("Closed..")

    def test_vanilla_download(self):
        """Just a bog-standard HTTP request to sanity check basics are OK"""

        response = urllib.urlopen(self.url)

        self.assertEquals(response.code, 200)
        self.assertEquals(response.headers["content-length"],
                          str(len(self.test_content)))
        self.assertEquals("".join(response.readlines()), self.test_content)

    def test_simple_range(self):
        from_offset = 10 # these are inclusive, so a range of 10-19
        to_offset = 19   # is 10 characters
        assert from_offset < len(self.test_content)
        assert to_offset < (len(self.test_content) + 1)
        req = urllib2.Request(self.url,
                              headers={"Range": "bytes=%d-%d" %
                                       (from_offset, to_offset)})
        response = urllib2.urlopen(req)

        self.assertEquals(response.code, 206)
        self.assertEquals(response.headers["content-length"],
                          str(to_offset - from_offset + 1))
        self.assertEquals("".join(response.readlines()),
                          self.test_content[from_offset:to_offset+1])
        self.assertEquals(response.headers["content-range"],
                          "bytes %d-%d/%d" % (from_offset, to_offset,
                                              len(self.test_content)))

    def test_range_final_n_bytes(self):
        trailing_range = 10
        assert trailing_range < len(self.test_content)
        req = urllib2.Request(self.url,
                              headers={"Range": "bytes=-%d" %
                                       (trailing_range)})
        response = urllib2.urlopen(req)
        self.assertEquals(response.code, 206)
        self.assertEquals(response.headers["content-length"],
                          str(trailing_range))
        self.assertEquals("".join(response.readlines()),
                          self.test_content[-trailing_range:])
        self.assertEquals(response.headers["content-range"],
                          "bytes %d-%d/%d" %
                          (len(self.test_content) - trailing_range,
                           len(self.test_content) - 1,
                           len(self.test_content)))


    def test_range_end_undefined(self):
        from_offset = 10
        assert from_offset < len(self.test_content)
        req = urllib2.Request(self.url,
                              headers={"Range": "bytes=%d-" %
                                       (from_offset)})
        response = urllib2.urlopen(req)

        self.assertEquals(response.code, 206)
        self.assertEquals(response.headers["content-length"],
                          str(len(self.test_content) - from_offset))
        self.assertEquals("".join(response.readlines()),
                          self.test_content[from_offset:])
        self.assertEquals(response.headers["content-range"],
                          "bytes %d-%d/%d" % (from_offset,
                                              len(self.test_content)-1,
                                              len(self.test_content)))


    def test_range_end_bigger_than_file(self):
        # TODO - need to find out what expected behaviour should be
        pass


if __name__ == '__main__':
    unittest.main()


