#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO: add static pages (img,css,js,...)

import wsgiref.simple_server as server
import ui
port = 8080
httpd = server.make_server('', port, ui.application)
print "Serving HTTP on port %i..." % port
httpd.serve_forever()
