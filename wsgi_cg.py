#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,re,dbhash,base64,hashlib,datetime
import xml.sax.saxutils, urllib
sys.path.append('/home/laurent/formose/ConnectedGraph')
import svgapp, collab, update, graph

__version__='0.2'

_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml"'
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink"'

def log_add(line):
    log = open('%s/cg.log'%__BASE__,'a')
    d = '%s'%datetime.datetime.now()
    log.write('[%s] %s\n'%(d[:19],line))
    log.close()

def my_app(environ,start_response):
    """ app """
    start_response('200 OK',[])
    return []

class middleware:
    """ """
    def __init__(self,app):
        self.app = app

    def __call__(self,environ, start_response):
        environ['mid.data'] = 'data'
        def custom_start_response(status, header):
            return start_response(status, header)
        response_iter = self.app(environ, custom_start_response)
        o = ''
        a = ''
        response_string = o + ''.join(response_iter) + a 
        return [response_string]

prj = 'ConnectedGraph'
application = svgapp.svg_app(update.update(graph.graph(collab.collab(middleware(my_app))),prj))

if __name__ == '__main__':
    import hmac
    print hmac.new('AA','BLABLA',hashlib.sha1).hexdigest()
    print hashlib.sha1('BLABLA').hexdigest()

