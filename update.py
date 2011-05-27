#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,re,dbhash,base64,hashlib,datetime,time
import xml.sax.saxutils, urllib
from subprocess import Popen, PIPE

__version__='0.2.1'
__TITLE__='Connected Graph'

_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml"'
_SVGNS    = 'xmlns="http://www.w3.org/2000/svg"'
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink"'

def get_id_pkg(r):
    """ pkg commit sha1 """
    r.add_common_vars()
    env = r.subprocess_env.copy()
    e = os.environ.copy()
    e['GIT_DIR'] = '%s/.git'%os.path.dirname(env['SCRIPT_FILENAME'])
    out,err = Popen(('git', 'log','--pretty=oneline','-1'), env=e,stdout=PIPE).communicate()
    dat = os.path.getmtime('%s/.git'%os.path.dirname(env['SCRIPT_FILENAME']))
    dat_str = '%s'%datetime.datetime.fromtimestamp(dat)
    if err:
        return 'error','error'
    else:
        return out[:7],dat_str[:19]

def my_app(environ,start_response):
    """ app """
    start_response('200 OK',[])
    return []

def update_tool1():
    """ update the tool from github """
    (pwd, name,ip) = get_env()
    t = datetime.datetime.now()
    d = time.mktime(t.timetuple())
    rev = dbhash.open('%s/cg/rev.db'%ui.__BASE__,'w')
    allow,delta = False,0
    if rev.has_key('_update_'):
        delta = d - float(rev['_update_'])
        if delta > 120:
            rev['_update_'],allow = '%s'%d,True
    if not rev.has_key('_update_'):
        rev['_update_'] = '%s'%d
    rev.close()
    if not allow:
        return 'Error: Time since last update is %d secondes; should be greater than 2 minutes!'%int(delta)
    cmd = 'cd %s/..; rm -rf ConnectedGraph; git clone git://github.com/pelinquin/ConnectedGraph.git; cd ConnectedGraph; git submodule update --init'%pwd
    out,err = Popen((cmd), shell=True,stdout=PIPE, stderr=PIPE).communicate()
    o = 'Application Updating from %s commit...\n'%(ui.sha1_pkg())
    if err:
        o += 'Error:%s\n'%err
    else:
        o += 'Message:%s\nUpdate OK\n'%out
    return o 

class update:
    """ """
    def __init__(self,app,url=''):
        self.app = app
        self.url = url

    def update_tool(self,environ):
        """ update the tool from github """
        d = time.mktime(datetime.datetime.now().timetuple())
        out,err = '',''
        #dname = os.path.dirname(env['SCRIPT_FILENAME'])
        #bname = os.path.basename(env['SCRIPT_FILENAME'])
        o = 'Application Updating from commit...\n'
        o += 'Message:%s\nUpdate OK %s %s\n'%(d,self.url, environ['SCRIPT_FILENAME'])
        return o 

    def __call__(self,environ, start_response):
        """ app """
        if environ['PATH_INFO'] == "/update_tool":
            start_response('200 OK',[])
            return [self.update_tool(environ)]
        elif (environ['PATH_INFO'] != '/edit') and (environ['PATH_INFO'] != '/'):
            return self.app(environ, start_response)
        o = '<script %s type="text/ecmascript" xlink:href="/js/update.js"/>\n'%_XLINKNS 
        a = '<text class="button" onclick="update_tool();" fill="white" text-anchor="end" x="98%" y="12">U<title>Update tool from Github</title></text>'     
        start_response('200 OK',[])
        def custom_start_response(status, header):
            return start_response(status, header)
        response_iter = self.app(environ, custom_start_response)
        response_string = o + ''.join(response_iter) + a 
        return [response_string]

def reset(pw):
    """ update
    """
    if hashlib.sha1(pw).hexdigest() == 'd2cd4178312fa9485b750280bc863d8b1ac9e9bf':
        Popen(('rm -rf %s/cg;'%__BASE__), shell=True).communicate()
        return 'reset done'
    return 'reset no allowed !'




