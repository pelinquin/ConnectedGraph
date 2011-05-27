#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,re,dbhash,base64,hashlib,datetime
import xml.sax.saxutils, urllib
from subprocess import Popen, PIPE
sys.path.append('/home/laurent/formose/ConnectedGraph')
import svgapp

__version__='0.2.1'
__TITLE__='Connected Graph'
__BASE__='/tmp/wd'

_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml"'
_SVGNS    = 'xmlns="http://www.w3.org/2000/svg"'
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink"'

def log_add(line):
    log = open('%s/cg.log'%__BASE__,'a')
    d = '%s'%datetime.datetime.now()
    log.write('[%s] %s\n'%(d[:19],line))
    log.close()

def parse_multipart(content_type,args):
    hargs = {}
    m = re.match(r'^multipart\/form\-data; boundary=\-+(\d+)',content_type)
    if m:
        h,key,txt,first = {},'','',True
        for l in args.split('\r\n'):
            m1,m2 = re.match(r'Content-Disposition: form\-data; name=\"(\w+)\"',l), re.search(m.group(1),l)
            if m1:
                key = m1.group(1)
            elif m2:
                if key:
                    hargs[key] = txt[:-1]
                    txt,first = '',True
            else:
                if not first:
                    txt += '%s\n'%l
                first = False
    return hargs

def my_app(environ,start_response):
    """ app """
    start_response('200 OK',[])
    return []

class collab:
    """ """
    def __init__(self,app):
        self.app = app

    def __call__(self,environ, start_response):
        """ app """
        edit_mode,view_mode = environ['PATH_INFO'] == '/edit', environ['PATH_INFO'] == ''
        if not os.path.isdir(__BASE__):
            os.mkdir(__BASE__)
        user = environ['svgapp.user']
        m = re.search('id\s*=\s*(\S{10})\s*($|\&)',urllib.unquote(environ['QUERY_STRING']))
        did = m.group(1) if m else ''
        if environ['PATH_INFO'] == "/new_doc":
            start_response('200 OK',[])
            return [new_doc(user)]
        elif environ['PATH_INFO'] == "/save_doc":
            title,lout,content = '','{}','' 
            if re.match(r'^multipart',environ['CONTENT_TYPE']):
                args = environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH',0)))
                h = parse_multipart(environ['CONTENT_TYPE'],args)
                title,lout,content = h['title'],h['lout'],h['content']
            start_response('200 OK',[])
            return [save_doc(user,did,title,lout,content)]
        elif environ['PATH_INFO'] == "/save_patch":
            sid,patch = '',''
            if re.match(r'^multipart',environ['CONTENT_TYPE']):
                args = environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH',0)))
                h = parse_multipart(environ['CONTENT_TYPE'],args)
                sid,patch = h['sid'],h['patch']
            start_response('200 OK',[])
            return [save_patch(user,did,sid,patch)]
        elif environ['PATH_INFO'] == "/load_patch":
            sid,clear_timeout = '',''
            m2 = re.search(r'sid=(\S{20})\&clear_timeout=(\d+)$',urllib.unquote(environ['QUERY_STRING']))
            if m2: 
                sid,clear_timeout = m2.group(1),m2.group(2)
            start_response('200 OK',[])
            return [load_patch(user,did,sid,clear_timeout)]
        elif environ['PATH_INFO'] == "/reset":
            mp = re.search(r'pw=(\w+)$',urllib.unquote(environ['QUERY_STRING']))
            start_response('200 OK',[])
            return [reset(mp.group(1) if mp else '')]
        ####
        titledoc,lout,value = load_doc(did)
        o = '<title id=".title">%s</title>'%__TITLE__
        o += '<link %s rel="shortcut icon" href="img/logo16.png"/>\n'%_XHTMLNS
        if edit_mode:
            sid = create_window_id()
            o += '<script %s type="text/ecmascript" xlink:href="js/collab.js"/>\n'%_XLINKNS 
            o += '<script %s type="text/ecmascript" xlink:href="js/diff_match_patch.js"/>\n'%_XLINKNS
            o += '<script %s type="text/ecmascript" xlink:href="ace/ace.js"></script><script %s type="text/ecmascript" xlink:href="ace/theme-twilight.js"></script><script %s type="text/ecmascript" xlink:href="ace/mode-python.js"></script>\n'%(_XLINKNS,_XLINKNS,_XLINKNS)
            disp = 'inline'
            o += '<foreignObject display="%s" width="100%%" height="100%%">'%disp
            # Change here to select textarea or ace!
            o += '<div %s id=".editor" class="editor" sid="%s">%s</div>'%(_XHTMLNS,sid,xml.sax.saxutils.escape(value))
            #o += '<textarea %s id=".editor" class="editor" sid="%s" spellcheck="false" rows="20">%s</textarea>'%(_XHTMLNS,sid,xml.sax.saxutils.escape(value))
            o += '</foreignObject>\n'
            if user:
                if did:
                    action,ttl = 'change_name(true)','Change document name'
                    o += '<text id=".save" fill="white" onclick="save_doc();" text-anchor="end" x="81%" y="12" class="button">Saved</text>\n'
                else:
                    action,ttl = 'new_doc(this)','Create a new document'
                    titledoc = 'New document'
                o += '<text id=".name" fill="white" onclick="%s;" x="50%%" y="12" class="button">%s<title>%s</title></text><foreignObject display="none" x="50%%" width="120" height="30"><div %s><input onchange="change_name(false);" size="10" value=""/></div></foreignObject>\n'%(action,titledoc,ttl,_XHTMLNS)
        
        start_response('200 OK',[])
        def custom_start_response(status, header):
            return start_response(status, header)
        response_iter = self.app(environ, custom_start_response)
        response_string = ''.join(response_iter) + o
        return [response_string]

def save_doc(user,did,title,lout,content):
    """ Save the layout and the content of a diagram """
    base = __BASE__
    stack = dbhash.open('%s/stack.db'%base,'c')
    stack['_%s'%did] = title + '\n' + lout + '\n' + content
    k = '@%s'%did
    if stack.has_key(k):
        del stack[k]
    stack.close()
    return 'Saved'

def create_window_id():
    """ Create a new window id"""
    base = __BASE__
    rev = dbhash.open('%s/rev.db'%base,'c')
    rev['@'] = '%d'%(long(rev['@'])+1) if rev.has_key('@') else '0'
    sid = hashlib.sha1(rev['@']).hexdigest()[:-20]
    rev.close()    
    return sid

def new_doc(user):
    """ utiliser user """
    gid = ''
    if user:
        base = __BASE__
        rev = dbhash.open('%s/rev.db'%base,'c')
        gid = create_id(rev)
        if rev.has_key(user):
            rev[user] += ':%s'%gid
        else:
            rev[user] = gid
        rev.close()    
    return gid

def create_id(rev):
    """ Create a new diagram id"""
    rev['_'] = '%d'%(long(rev['_'])+1) if rev.has_key('_') else '0'
    return base64.urlsafe_b64encode(hashlib.sha1(rev['_']).digest())[:-18]

def save_patch(user,did,sid,patch):
    """  editor onchange """
    base = __BASE__
    stack = dbhash.open('%s/stack.db'%base,'c')
    patch = re.sub('\r','',patch)
    if stack.has_key(did):
        for other in stack[did].split(':'):
            if (other != sid):
                if stack.has_key(other):
                    stack[other] += patch
                else :
                    stack[other] = patch
    k = '@%s'%did
    if stack.has_key(k):
        stack[k] += patch
    else:
        stack[k] = patch
    stack.close()
    return 'ok'

def get_shared(req,user,did,sid):
    """ """
    base = __BASE__
    o,sep = '',''
    req.content_type = 'text/plain'
    stack = dbhash.open('%s/stack.db'%base)
    if stack.has_key(did):
        for other in stack[did].split(':'):
            if other != sid:
                if stack.has_key('_%s'%other):
                    user = stack['_%s'%other][11:]
                    if user == '':
                        user = 'anonymous'
                    o += sep + user
                    sep = ','
    stack.close()
    return o 
    
def load_patch(user,did,sid,clear_timeout):
    """ Periodic patch stack read"""
    import time
    base = __BASE__
    stack = dbhash.open('%s/stack.db'%base,'c')
    t = datetime.datetime.now()
    d = '%s'%time.mktime(t.timetuple())
    stack['_%s'%sid] = '%s:%s'%(d[:10],user)
    if stack.has_key(did):
        if not re.search(sid,stack[did]):
            stack[did] += ':%s'%sid
    else:
        stack[did] = sid
    for other in stack[did].split(':'):
        if (other != sid):
            if stack.has_key('_%s'%other):
                if int(d[:10]) - int(stack['_%s'%other][:10]) > int(clear_timeout):
                    if stack.has_key(did):
                        stack[did] = re.sub(':$','',re.sub('%s:?'%other,'',stack[did]))
                    del stack['_%s'%other]
                    if stack.has_key(other):
                        del stack[other]
    o = ''
    if stack.has_key(sid):
        o = stack[sid]
        del stack[sid]
    stack.close()
    return o

def reset(pw):
    """ clear GIT database....
    you must provide the right password for reseting the database !
    """
    if hashlib.sha1(pw).hexdigest() == 'd2cd4178312fa9485b750280bc863d8b1ac9e9bf':
        Popen(('rm -rf %s/cg;'%__BASE__), shell=True).communicate()
        return 'reset done'
    return 'reset no allowed !'

def load_doc(did):
    """ Load layout and content of a diagram """
    base = __BASE__
    content,lout,title = '',{},'Untitled'
    if did and os.path.isfile('%s/stack.db'%base):
        stack,key = dbhash.open('%s/stack.db'%base),'_%s'%did
        if stack.has_key(key):
            lines =  stack[key].split('\n')
            if len(lines) > 2:
                title,lout,content = lines[0],eval(lines[1]),'\n'.join(lines[2:])
        k = '@%s'%did
        if stack.has_key(k):
            import diff_match_patch
            dmp = diff_match_patch.diff_match_patch()
            patches = dmp.patch_fromText(stack[k])
            result = dmp.patch_apply(patches, content)
            content = result[0].encode('utf-8')
            #log_add(result[0])
        stack.close()
    return title,lout,content



