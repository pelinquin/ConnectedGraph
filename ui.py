#!/usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
#  © Copyright 2011 Rockwell Collins, Inc 
#    This file is part of Formose.
#
#    Formose is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Formose is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Formose.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------

"""
 This script is called from Apache in 'mod_python' publisher mode
 As 'mod_python' is longer be supported by Apache...move to 'mod_wsgi'
"""

import os,re
import xml.sax.saxutils
import random
import urllib
import dbhash
import datetime
import hashlib,base64
from subprocess import Popen, PIPE

__version__='0.2e'
__TITLE__='Connected Graph'

__BASE__='/tmp'
__JS__='ui.js'
__CSS__='ui.css'

_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml"'
_SVGNS    = 'xmlns="http://www.w3.org/2000/svg"'
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink"'

##### COMMON REGULAR EXPRESSIONS #####
__REG_NODES__ = r""" # RegEx for capturing nodes
    # 1:name 2:label 3:type 4:child
    (?:                     # do not count group(name,label)
     (\w+) |                # g1:name
     (                      # g2:label
      \[(?:\\.|[^\]])+\]  | # [] delimiter
      \((?:\\.|[^\)])+\)  | # () delimiter
      \<(?:\\.|[^\->])+\> | # <> delimiter
      \"(?:\\.|[^\"])+\"    # \" delimiter
     )                      # end label
    )+                      # at least one name or label
    (:\w+)?                 # g3:type
    (@\S{10})?              # g4:child
    \s*                     # leading spaces
    (?:\#[^\n]*(?:\n|$))?   # comments
    """

__REG_EDGES__ = __REG_NODES__ + """ # RegEx for capturing connector
    \s*                         # ignored spaces
    (->|<-|-!-|[\d\.]*-[\d\.]*) # g5 connector
    \s*                         # ignored spaces
    """ + __REG_NODES__


__REG_TYPES__ = {'(\[.*|r|req|requirement)':'Requirement',
                 '(\(.*|g|goal)':'Goal',
                 '(<.*|a|agent|people)':'Agent',
                 '(b|obs|obstacle)':'Obstacle',
                 '(s|asso|association)':'Association',
                 '(t|ent|entity)':'Entity',
                 '(e|exp|expectation)':'Expectation',
                 '(o|op|operation)':'Operation',
                 '(p|pr|prop|property)':'Property',
                 '(v|ev|event)':'Event',
                 '(c|cl|class)':'Class'}

def get_ip(r):
    """ get client ip address """
    r.add_common_vars()
    env = r.subprocess_env.copy()
    ip = env['REMOTE_ADDR'] if env.has_key('REMOTE_ADDR') else '0.0.0.0'
    return ip

def documents(req,login='',pw='',pw2=''):
    """ document list """
    return edit(req,'',login,pw,pw2,'',True)

def edit(req,id='',login='',pw='',pw2='',mode='',newdoc=False):
    """ edit mode """
    did = id # 'id' is a reserved Python keyword but it is used as an URL parameter
    base='%s/cg'%__BASE__
    if not os.path.isdir(base):
        os.mkdir(base)
    msg,user,ip,uid = '','',get_ip(req),''
    if login:
        if pw2:
            if register_user(login,pw,pw2,ip):
                user,msg = login,'Hi %s, your account is well created!'%login
                save_session(req,user)
            else:
                msg = 'Error: login already used or more than 10 logins/ip or difference in repeated password or password too much simple!'
        else:
            if check_user(login,pw):
                user,msg = login,'Hi %s!'%login
                save_session(req,user)
            else:
                msg = 'Error: bad login or password!'
    else:
        user,uid = load_session(req)
    return main_call(req,did,'..',uid,True,user,msg,mode,newdoc)

def index(req,id=''):
    """ readonly mode"""
    did = id # 'id' is a reserved Python keyword but it is used as an URL parameter
    return main_call(req,did)

def include_ace(pfx):
    support = '%s/support/ace/build/src'%pfx
    return '<script %s type="text/ecmascript" xlink:href="%s/ace.js"></script><script %s type="text/ecmascript" xlink:href="%s/theme-twilight.js"></script><script %s type="text/ecmascript" xlink:href="%s/mode-python.js"></script>'%(_XLINKNS,support,_XLINKNS,support,_XLINKNS,support)

def main_call(req=None,did='',pfx='.',uid='',edit=False,user='',msg='',mode='',newdoc=False):
    """ common to readonly and edit mode"""
    value = re.sub('\$','#',re.sub('\\\\n','\n',urllib.unquote(req.args))) if req.args else ''
    value = re.sub('mode=[^&]*&?','',value)
    value = re.sub('id=[^&]*&?','',value)
    lout = {}
    #from mod_python import Session
    #s = Session.MemorySession(req)
    #s = Session.DbmSession(req)
    #s.load()
    #sid = s.id()
    #sid = "no sessionID!"
    sid = create_window_id()
    titledoc = 'Untitled'
    if did:
        titledoc,lout,value = load_doc(did)
    #msg = '%s'%lout
    #if value == '':
    #    return doc_list(req,user)
    req.content_type = 'application/xhtml+xml'
    o = '<?xml version="1.0" encoding="UTF-8"?>\n'
    o += '<?xml-stylesheet href="%s/%s" type="text/css"?>\n'%(pfx,__CSS__)
    miniature = ' width="600" height="400" viewBox="0 0 2400 1600"'
    miniature = ''
    o += '<svg %s editable="%s" user="%s" did="%s" tool="%s" sid="%s" uid="%s"%s>\n'%(_SVGNS,'yes' if edit else 'no',user,did,__version__,sid,uid,miniature)
    if miniature:
        o += '<rect width="600" height="400" fill="#EEE"/>\n'
    o += '<title id=".title">%s</title>'%__TITLE__
    o += '<link %s rel="shortcut icon" href="%s/logo16.png"/>\n'%(_XHTMLNS,pfx)
    if edit:
        o += include_ace(pfx)
        o += '<script %s type="text/ecmascript" xlink:href="%s/diff_match_patch.js"></script>\n'%(_XLINKNS,pfx)
    o += '<script %s type="text/ecmascript" xlink:href="%s/%s"></script>\n'%(_XLINKNS,pfx,__JS__)
    o += defs()
    if edit:
        disp = 'inline' if mode == 'both' else 'none'
        o += '<foreignObject display="%s" width="100%%" height="100%%">'%disp
        # Change here to select textarea or ace!
        o += '<div %s id=".editor" class="editor">%s</div>'%(_XHTMLNS,xml.sax.saxutils.escape(value))
        #o += '<textarea %s id=".editor" class="editor" spellcheck="false" rows="20" style="color:white;background-color:#444;margin:20pt;width:800px">%s</textarea>'%(_XHTMLNS,xml.sax.saxutils.escape(value))
        o += '</foreignObject>'
    mygraph = cg(value)
    mygraph.set_pos(lout)
    o += mygraph.draw()    
    if edit:
        o += menu() + gui_elements() + menubar(req,'fork',True,user,msg,newdoc,did,titledoc);
    o += '<text id=".debug" class="small" x="300" y="12"> </text>\n'
    if newdoc:
        o += get_doc_list(user)
    return o + '</svg>'

def doc_list(req,user):
    req.content_type = 'text/plain'
    o = "hello %s"%user
    return o 

def parse_type(t):
    """ parse node type """
    if t:
        for i in __REG_TYPES__:
            if re.match(i+'$',t,re.IGNORECASE):
                return __REG_TYPES__[i].upper()
    return None

class cg:
    """ Connected Graphs class"""

    def __init__(self,raw):
        """ """
        self.lab,self.typ,self.child,self.pos = {},{},{},{}
        r,n = {},0
        for m in re.compile(__REG_NODES__,re.X).finditer(raw):
            nm = m.group(1)
            lb = re.sub(r'\\','',m.group(2)[1:-1]) if m.group(2) else None
            tp = parse_type(m.group(3)[1:] if m.group(3) else m.group(2))
            ch = m.group(4)
            if nm:
                if tp:
                    self.typ[nm] = tp
                if ch:
                    self.child[nm] = ch[1:]
                if self.lab.has_key(nm):
                    if lb:
                        self.lab[nm] = lb
                else:
                    if lb:
                        self.lab[nm] = lb
                    else:
                        self.lab[nm] = nm
            else:
                if not r.has_key(lb):
                    tid = '.n%d'%n
                    self.lab[tid] = lb
                    r[lb] = tid
                    if tp:
                        self.typ[tid] = tp
                    if ch:
                        self.child[tid] = ch[1:]
                    n += 1
        self.connectors = []
        for m in re.compile(__REG_EDGES__,re.X).finditer(raw):
            k1,k2 = '',''
            if (m.group(1) or m.group(2)) and (m.group(6) or m.group(7)):
                n1 = m.group(1)
                if n1:
                    k1 = n1
                else:
                    l1 = re.sub(r'\\','',m.group(2)[1:-1])
                    if r.has_key(l1):
                        k1 = r[l1]
                n2 = m.group(6)
                if n2:
                    k2 = n2
                else:
                    l2 = re.sub(r'\\','',m.group(7)[1:-1])
                    if r.has_key(l2):
                        k2 = r[l2]        
                if k1 != k2:
                    if m.group(5) == '->':
                        self.connectors.append((k2,k1))
                    elif m.group(5) == '<-':
                        self.connectors.append((k1,k2))
                    elif m.group(5) == '-!-':
                        self.connectors.append((k1,k2,'conflict'))
                    elif re.match('^[\d\.]*-[\d\.]*$',m.group(5)):
                        self.connectors.append((k1,k2,m.group(5)))     

    def set_pos(self,lout):
        w,h,m = 600,400,40
        random.seed(3)
        for i in self.lab.keys():
            self.pos[i] = lout[i] if lout.has_key(i) else [random.randint(m,w),random.randint(m,h)]
                
    def cut(self,i):
        first = True;
        o = '<text>'
        for line in self.lab[i].split('\n'):
            if first:
                o += '<tspan>%s</tspan>'%line
                first = False
            else:
                o += '<tspan x="0" dy="1.2em">%s</tspan>'%line
        return o + '</text>'

    def draw(self):
        o = '<g id=".nodes" visibility="visible" class="nodes" stroke="none">'
        for i in self.lab.keys():
            if self.pos.has_key(i):
                t = self.typ[i] if self.typ.has_key(i) else ''
                o += '<g id="%s" type="%s" transform="translate(%s,%s)">%s</g>'%(i,t,self.pos[i][0],self.pos[i][1],self.cut(i))
        o += '</g>\n'
        o += '<g id=".connectors" visibility="visible" class="connectors" stroke-width="1">'
        for c in self.connectors:
            o += '<g n1="#%s" n2="#%s"/>'%(c[1],c[0])
        return o + '</g>\n'

    def get(self,cpt):
        """ for unitary test """
        if cpt == 'node':
            return '%s'%self.lab
        elif cpt == 'type':
            return '%s'%self.typ
        else:
            return '%s'%self.connectors

def build_pdf(req):
    """ provision """
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    drawing = svg2rlg('file.svg')
    renderPDF.drawToFile(drawing, 'file.pdf')

def defs():
    """ """
    o = '<defs>'
    o += '<marker id=".conflict" viewBox="0 0 1000 1000" preserveAspectRatio="none" refX="0" refY="100" markerWidth="30" markerHeight="80" orient="auto"><path d="M100,0 l-20,80 l120,-20 l-100,140 l20,-80 l-120,20 Z" stroke="none" fill="red"/></marker>'
    o += '<marker id=".arrow" viewBox="0 0 500 500" refX="80" refY="50" markerUnits="strokeWidth" orient="auto" markerWidth="40" markerHeight="30"><polyline points="0,0 100,50 0,100 10,50" fill="#555"/></marker><radialGradient id=".grad" cx="0%" cy="0%" r="90%"><stop offset="0%" stop-color="#FFF"/><stop offset="100%" stop-color="#DDD" class="end"/></radialGradient><filter id=".shadow" filterUnits="userSpaceOnUse"><feGaussianBlur in="SourceAlpha" result="blur" stdDeviation="2"/><feOffset dy="3" dx="2" in="blur" result="offsetBlur"/><feMerge><feMergeNode in="offsetBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    o += '<marker id=".simple_start" viewBox="-10 -10 100 100" preserveAspectRatio="xMidYMin meet" refX="-30" refY="-15" markerWidth="160" markerHeight="30" orient="0"><text text-anchor="end" stroke-width="0" fill="gray">0..1</text></marker>'
    o += '<marker id=".simple_end" viewBox="-10 -10 100 100" preserveAspectRatio="xMinYMin meet" refX="30" refY="-15" markerWidth="160" markerHeight="30" orient="0"><text text-anchor="end" stroke-width="0" fill="gray">0..*</text></marker>'
    o += '<marker id=".not" viewBox="-13 -6 10 12" refX="-20" markerWidth="8" markerHeight="16" orient="auto"><path d="M-10,-5 L-10,5" stroke="gray"/></marker>'
    # for logo
    o += '<radialGradient id=".rd1" fx="0" fy="0" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(84.70,0.76,-0.76,84.70,171.57,-156.43)" spreadMethod="pad"><stop style="stop-color:#94d787" offset="0"/><stop style="stop-color:#6bc62e" offset="1"/></radialGradient><radialGradient id=".rd2" fx="0" fy="0" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(84.69,0.76,-0.76,84.69,171.58,-156.42)" spreadMethod="pad"><stop style="stop-color:#94d787" offset="0"/><stop style="stop-color:#6bc62e" offset="1"/></radialGradient><radialGradient id=".rd3" fx="0" fy="0" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(161.13,1.45,-1.45,161.13,99.46,-256.92)" spreadMethod="pad"><stop style="stop-color:#bae381" offset="0"/><stop style="stop-color:#6bc62e" offset="1"/></radialGradient>'
    return o + '</defs>\n'

def menu():
    """ node menu prebuild """
    o = '<g id=".menu"><rect class="theme" rx="4"/>'
    for i in __REG_TYPES__:
        o += '<text class="item">%s</text><g></g>'%__REG_TYPES__[i]
    o += '</g>\n'
    o += '<g id=".menu_node"><rect class="theme" rx="4"/>'
    o += '<text class="item">Delete node</text>'
    o += '<text class="item">Change node to...</text>'
    o += '</g>\n'
    o += '<g id=".menu_connector"><rect class="theme" rx="4"/>'
    o += '<text class="item">Delete Connector</text>'
    o += '<text class="item">Flip connector way</text>'
    return o + '</g>\n'

def menubar(req,action,full=False,user='',msg='',newdoc=False,did='',titledoc=''):
    """ top menu bar """
    o = '<g id=".menubar"><rect class="theme" width="100%" height="18"/>'
    #o += '<path id="oo" d="M100,100L0,0" stroke="red"/><text><textPath %s stroke="black" xlink:href="#oo">Hello world !</textPath></text>'%_XLINKNS
    if full:
        (txt,act) = (user,'logout') if user else ('Sign in','signin')
        o += '<text class="button" onclick="%s();" fill="white" text-anchor="end" x="95%%" y="12">%s<title>%s</title></text>'%(act,txt,act)
    num,dat = get_id_pkg(req)
    o += '<text class="button" fill="white" onclick="help();" text-anchor="end" x="99%%" y="12">?<title>Version %s [%s] Installed on %s</title></text>'%(__version__,num,dat)
    o += '<text class="button" fill="white" onclick="%s();" x="46" y="12">%s<title>Fork me on Github!</title></text>'%(action,__TITLE__)
    if full:
        theid = 'id=".name"'
        if newdoc:
            if user:
                o += '<text %s fill="white" onclick="new_doc(this);" x="50%%" y="12" class="button">New document<title>Create a new document</title></text><g/>\n'%theid
        else:
            o += '<text %s fill="white" onclick="change_name(true);" x="50%%" y="12" class="button">%s<title>Change name</title></text><foreignObject display="none" x="50%%" width="120" height="30"><div %s><input onchange="change_name(false);" size="10" value=""/></div></foreignObject>\n'%(theid,titledoc,_XHTMLNS)
            if did:
                o += '<text id=".save" fill="white" onclick="save_doc();" text-anchor="end" x="85%" y="12" class="button">Save</text>\n'
            color = 'red' if msg[:5] == 'Error' else 'white'
            o += logo(False) + '<text class="msg" id=".msg" fill="%s" x="200" y="12">%s </text>'%(color,msg)
        o += login_page()
    return o + '</g>\n'

def gui_elements():
    """ current node + progress bar + node area """
    o = '<g id=".current" class="current" display="none" stroke="red" stroke-width="2" fill="none"><rect/></g>\n'
    o += '<g id=".currentline" class="current" display="none" stroke="red" stroke-width="2" fill="none"><rect/></g>\n'
    o += '<g display="none" transform="translate(1,10)"><rect text-anchor="end" width="100" height="14" rx="6" ry="6" stroke-width="1px" stroke="#CCC" fill="none"/><rect id=".bar" class="bar" width="0" height="14" rx="6" ry="6"/><text id=".prg" x="44" y="11">0%</text></g>\n'
    o += '<g display="none"><foreignObject id=".area"><textarea %s></textarea></foreignObject></g>\n'%_XHTMLNS
    return o

##### AJAX CALL ####

def update(req,user,value=''):
    #from mod_python import Session
    #session = Session.DbmSession(req)
    #session.save()
    #session.load()
    #sid = session.id()
    req.content_type = 'application/xhtml+xml'
    tex = open('%s/test.tex'%__BASE__,'a')
    tex.write(value.encode('utf-8'))
    tex.close()
    return '<ok/>'

def read(req,user):
    """ utiliser user """
    req.content_type = 'text/plain'
    tex = open('%s/test.tex'%__BASE__).read()
    return tex

def new_doc(req,user):
    """ utiliser user """
    base='%s/cg'%__BASE__
    req.content_type = 'text/plain'
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

def create_window_id():
    """ Create a new window id"""
    base='%s/cg'%__BASE__
    rev = dbhash.open('%s/rev.db'%base,'c')
    rev['@'] = '%d'%(long(rev['@'])+1) if rev.has_key('@') else '0'
    sid = hashlib.sha1(rev['@']).hexdigest()[:-20]
    rev.close()    
    return sid

def get_doc_list(user):
    """ Create a new window id"""
    base='%s/cg'%__BASE__
    o = '<text class="list" onclick="open_doc(evt);" y="20">' 
    if os.path.isfile('%s/stack.db'%base) and os.path.isfile('%s/rev.db'%base):
        rev = dbhash.open('%s/rev.db'%base)
        stack = dbhash.open('%s/stack.db'%base)
        if rev.has_key(user):
            for did in rev[user].split(':'):
                k = '_%s'%did
                name = stack[k].split('\n')[0] if stack.has_key(k) else 'Untitled'
                o += '<tspan x="10" dy="1.2em"><title>%s</title>%s</tspan>'%(did,name)
                o += '<tspan class="small" x="100">1 user</tspan>'
        stack.close()
        rev.close()
    return o + '</text>'

def save_doc(req,user,did,sid,title,lout,content):
    """ Save the layout and the content of a diagram """
    base='%s/cg'%__BASE__
    req.content_type = 'text/plain'
    stack = dbhash.open('%s/stack.db'%base,'c')
    stack['_%s'%did] = title + '\n' + lout + '\n' + content
    k = '@%s'%did
    if stack.has_key(k):
        del stack[k]
    stack.close()
    return 'Saved'

def load_doc(did):
    """ Load layout and content of a diagram """
    import diff_match_patch
    dmp = diff_match_patch.diff_match_patch()
    base='%s/cg'%__BASE__
    key,content,lout,title = '_%s'%did,'',{},'Untitled'
    if os.path.isfile('%s/stack.db'%base):
        stack = dbhash.open('%s/stack.db'%base)
        if stack.has_key(key):
            lines =  stack[key].split('\n')
            if len(lines) > 2:
                title,lout,content = lines[0],eval(lines[1]),'\n'.join(lines[2:])
        k = '@%s'%did
        if stack.has_key(k):
            patches = dmp.patch_fromText(stack[k])
            result = dmp.patch_apply(patches, content)
            content = result[0]
        stack.close()
    return title,lout,content

def log_add(line):
    log = open('%s/cg/cg.log'%__BASE__,'a')
    d = '%s'%datetime.datetime.now()
    log.write('[%s] %s\n'%(d[:19],line))
    log.close()
    
def save_patch(req,user,did,sid,patch):
    """  editor onchange """
    base='%s/cg'%__BASE__
    req.content_type = 'text/plain'
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
    base='%s/cg'%__BASE__
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
    
def load_patch(req,user,did,sid,clear_timeout):
    """ Periodic patch stack read"""
    import time
    base='%s/cg'%__BASE__
    req.content_type = 'text/plain'
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

def reset(req,pw):
    """ clear GIT database....
    you must provide the right password for reseting the database !
    """
    req.content_type = 'text/plain'
    if hashlib.sha1(pw).hexdigest() == 'd2cd4178312fa9485b750280bc863d8b1ac9e9bf':
        Popen(('rm -rf %s/cg;'%__BASE__), shell=True).communicate()
        return 'reset done'
    return 'reset no allowed !'

##### SESSION ####

def load_session(req):
    """ """
    from mod_python import Session
    s = Session.DbmSession(req)    
    s.load()
    uid = s.id()
    user = s['user'] if s.has_key('user') else ''
    #base='%s/cg'%__BASE__
    #user,uid = '','user_id_toto'
    #if os.path.isfile('%s/session.db'%base):
    #    s = dbhash.open('%s/session.db'%base)
    #    user = s['user'] if s.has_key('user') else ''
    #s.close()  
    return user,uid

def save_session(req,user=''):
    """ """
    from mod_python import Session
    s = Session.DbmSession(req) 
    if user:
        s['user'] = user
    s.save()
    #base='%s/cg'%__BASE__
    #s = dbhash.open('%s/session.db'%base,'c')
    #s['_'] = '%d'%(long(rev['_'])+1) if s.has_key('_') else '0'
    #gid = base64.urlsafe_b64encode(hashlib.sha1(s['_']).digest())[:-18]
    #if user:
    #    s[user] = gid
    #s.close()    
    req.content_type = 'text/plain'
    return 'ok'

#### login ####

def register_user(login,pw1,pw2,ip):
    """ Store up to 10 login/pw per ip"""
    result = False
    base='%s/cg/pw.db'%__BASE__
    db = dbhash.open(base,'c')
    if not db.has_key(ip):
        db[ip] = '%d'%0
    if len(pw1) > 4 :
        if login != pw1:
            if not re.match('^anonymous$',login,re.IGNORECASE):
                if (pw1 == pw2) and login:
                    if int(db[ip]) < 10:
                        if not db.has_key(login):
                            db[login] = hashlib.sha1(pw1).hexdigest()
                            db[ip] = '%d'%(int(db[ip]) + 1)
                            result = True
    db.close()    
    return result

def check_user(login,pw):
    """ """
    base='%s/cg/pw.db'%__BASE__
    result = False
    if login and pw:
        if os.path.isfile(base):
            db = dbhash.open(base)
            if db.has_key(login):
                if db[login] == hashlib.sha1(pw).hexdigest():
                    result = True
            db.close()    
    return result

##### SHA1 #####

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

def login_page():
    """ + FORMOSE logo """
    o = '<g id=".loginpage" display="none">'
    o += '<rect x="5%" y="5%" width="90%" height="90%" opacity=".9" fill="#DDD"/>'
    o += '<text x="140" y="220">Login:</text>'
    o += '<text x="140" y="240">Password:</text>'
    o += '<text class="button" onclick="create_account(this);" x="140" y="310">Create a new account</text>'
    o += '<text id="msg" display="none" x="208" y="190" fill="red">New account:</text>'
    o += '<foreignObject display="inline" y="200" x="200" width="120" height="80">' 
    o += '<div %s><form id="myform" method="post">'%_XHTMLNS
    o += '<input id="login" name="login" title="Login" size="10" value=""/>'
    o += '<input id="pw" onchange="submit();" name="pw" type="password" title="Password" size="10" value=""/>'
    o += '<input id="pw2" style="display:none" name="pw2" type="password" title="Password repeat" size="10" value=""/>'
    o += '</form></div>'
    o += '</foreignObject>'
    o += '<rect width="1" height="1"/>' #bug WEBkit
    o += '<g onclick="check();" title="submit login/password" class="button" fill="#444" transform="translate(320,208)"><rect x="1" width="15" height="30" rx="5"/><path transform="translate(0,6)" d="M4,4 4,14 14,9" fill="white"/></g>'
    return o + logo() + '</g>'

def logo(full=True):    
    o = '<!-- Copyright 2010 Stephane Macario -->'
    if full:
        o += '<g onclick="fork();" transform="matrix(0.5,0,0,0.5,120,500)" style="fill:#ffffff;stroke:none">'
    else:
        o += '<g onclick="switch_mode();" transform="matrix(0.2,0,0,0.2,0,166)" style="fill:#ffffff;stroke:none">'
    if full:
        o += '<g style="fill:#231f20;stroke:none"><path d="m 536.70,-701.72 c 0,0 -332.09,0 -332.09,0 0,0 0,-65.40 0,-65.40 0,0 332.09,0 332.09,0 0,0 0,65.40 0,65.40 z"/><path d="m 561.06,-675.65 c 0,0 -330.70,0 -330.70,0 0,0 0,-68.26 0,-68.26 0,0 330.70,0 330.70,0 0,0 0,68.26 0,68.26 z"/></g><path d="m 237.89,-737.15 c 0,0 0,9.74 0,9.74 0,0 15.65,0 15.65,0 0,0 0,6.37 0,6.37 0,0 -15.65,0 -15.65,0 0,0 0,19.25 0,19.25 0,0 -7.88,0 -7.88,0 0,0 0,-41.98 0,-41.98 0,0 29.34,0 29.34,0 0,0 0,6.61 0,6.61 0,0 -21.45,0 -21.45,0 z"/><path d="m 278.83,-723.11 c 0,4.90 0.88,8.69 2.64,11.38 1.76,2.68 4.32,4.03 7.69,4.03 3.95,0 6.96,-1.31 9.04,-3.94 2.07,-2.63 3.11,-6.45 3.11,-11.47 0,-9.82 -3.85,-14.73 -11.55,-14.73 -3.52,0 -6.23,1.33 -8.11,3.99 -1.88,2.66 -2.82,6.24 -2.82,10.74 z m -8.23,0 c 0,-5.96 1.73,-11.02 5.22,-15.15 3.47,-4.13 8.13,-6.19 13.95,-6.19 6.41,0 11.31,1.87 14.70,5.61 3.38,3.73 5.08,8.98 5.08,15.73 0,6.75 -1.77,12.11 -5.31,16.07 -3.54,3.96 -8.56,5.95 -15.08,5.95 -5.98,0 -10.58,-1.96 -13.77,-5.89 -3.19,-3.92 -4.79,-9.30 -4.79,-16.13 z"/><path d="m 331.08,-737.32 c 0,0 0,11.60 0,11.60 1.45,0.11 2.57,0.17 3.34,0.17 3.29,0 5.71,-0.43 7.24,-1.30 1.52,-0.87 2.29,-2.57 2.29,-5.10 0,-2.05 -0.82,-3.48 -2.45,-4.30 -1.63,-0.81 -4.22,-1.22 -7.74,-1.22 -0.85,0 -1.74,0.05 -2.67,0.17 z m 16.93,35.54 c 0,0 -11.91,-17.39 -11.91,-17.39 -1.19,-0.01 -2.86,-0.08 -5.01,-0.19 0,0 0,17.59 0,17.59 0,0 -8.23,0 -8.23,0 0,0 0,-42.01 0,-42.01 0.44,0 2.16,-0.06 5.14,-0.21 2.98,-0.14 5.38,-0.21 7.21,-0.21 11.32,0 16.98,4.12 16.98,12.37 0,2.48 -0.78,4.74 -2.34,6.78 -1.56,2.04 -3.52,3.48 -5.90,4.32 0,0 13.22,18.96 13.22,18.96 0,0 -9.16,0 -9.16,0 z"/><path d="m 408.88,-701.77 c 0,0 -7.65,0 -7.65,0 0,0 -4.69,-22.61 -4.69,-22.61 0,0 -8.98,23.19 -8.98,23.19 0,0 -2.78,0 -2.78,0 0,0 -8.98,-23.19 -8.98,-23.19 0,0 -4.81,22.61 -4.81,22.61 0,0 -7.65,0 -7.65,0 0,0 9.04,-41.98 9.04,-41.98 0,0 4.17,0 4.17,0 0,0 9.62,28.29 9.62,28.29 0,0 9.39,-28.29 9.39,-28.29 0,0 4.17,0 4.17,0 0,0 9.16,41.98 9.16,41.98 z"/><path d="m 426.17,-723.11 c 0,4.90 0.87,8.69 2.64,11.38 1.76,2.68 4.32,4.03 7.69,4.03 3.95,0 6.96,-1.31 9.04,-3.94 2.07,-2.63 3.11,-6.45 3.11,-11.47 0,-9.82 -3.85,-14.73 -11.55,-14.73 -3.52,0 -6.23,1.33 -8.11,3.99 -1.88,2.66 -2.82,6.24 -2.82,10.74 z m -8.23,0 c 0,-5.96 1.73,-11.02 5.22,-15.15 3.48,-4.13 8.13,-6.19 13.95,-6.19 6.41,0 11.31,1.87 14.70,5.61 3.38,3.73 5.08,8.98 5.08,15.73 0,6.75 -1.77,12.11 -5.31,16.07 -3.54,3.96 -8.56,5.95 -15.08,5.95 -5.98,0 -10.57,-1.96 -13.77,-5.89 -3.19,-3.92 -4.79,-9.30 -4.79,-16.13 z"/><path d="m 468.10,-704.12 c 0,0 2.92,-6.69 2.92,-6.69 3.12,2.08 6.20,3.13 9.23,3.13 4.65,0 6.97,-1.52 6.97,-4.57 0,-1.42 -0.54,-2.79 -1.64,-4.08 -1.09,-1.29 -3.35,-2.75 -6.77,-4.35 -3.41,-1.60 -5.71,-2.93 -6.90,-3.97 -1.18,-1.04 -2.10,-2.27 -2.73,-3.71 -0.64,-1.43 -0.95,-3.01 -0.95,-4.75 0,-3.24 1.25,-5.94 3.78,-8.08 2.52,-2.13 5.75,-3.21 9.70,-3.21 5.14,0 8.92,0.91 11.33,2.72 0,0 -2.40,6.43 -2.40,6.43 -2.77,-1.85 -5.70,-2.78 -8.78,-2.78 -1.82,0 -3.23,0.45 -4.24,1.35 -1,0.9 -1.50,2.08 -1.5,3.53 0,2.4 2.83,4.89 8.50,7.48 2.98,1.37 5.14,2.63 6.46,3.79 1.31,1.15 2.32,2.49 3.01,4.03 0.69,1.53 1.03,3.24 1.03,5.13 0,3.39 -1.42,6.18 -4.28,8.37 -2.85,2.19 -6.67,3.28 -11.47,3.28 -4.16,0 -7.92,-1.01 -11.27,-3.04 z"/><path d="m 516.24,-737.15 c 0,0 0,9.74 0,9.74 0,0 14.49,0 14.49,0 0,0 0,6.37 0,6.37 0,0 -14.49,0 -14.49,0 0,0 0,12.64 0,12.64 0,0 20.29,0 20.29,0 0,0 0,6.61 0,6.61 0,0 -28.18,0 -28.18,0 0,0 0,-41.98 0,-41.98 0,0 28.18,0 28.18,0 0,0 0,6.61 0,6.61 0,0 -20.29,0 -20.29,0 z"/>'
    o += '<g transform="translate(-5.8,-492.07)"><path d="m 86.77,-176.29 c 0,0 -1.34,-5.21 -1.34,-5.21 -0.84,0.01 -1.69,0.03 -2.54,0.03 -16.44,-0.14 -32.02,-3.82 -46.07,-10.26 10.86,15.09 26.44,26.58 44.59,32.30 -0.05,-0.18 -0.12,-0.36 -0.17,-0.56 -1.57,-6.07 0.78,-12.28 5.55,-16.29 z" style="fill:url(#.rd1);stroke:none"/></g>'
    o += '<g transform="translate(-5.8,-492.07)"><path d="m 194.97,-241.90 c 0.06,-7.29 -0.78,-14.39 -2.40,-21.18 -12.30,42.46 -48.78,74.56 -93.44,80.57 0,0 0.49,1.90 0.49,1.90 7.36,0.32 13.85,5.02 15.66,12.04 1.18,4.60 0.10,9.27 -2.55,13.00 45.51,-2.58 81.83,-40.09 82.25,-86.34 z" style="fill:url(#.rd2);stroke:none"/></g>'
    o += '<g transform="translate(-5.8,-492.07)"><path d="m 174.53,-298.79 c -1.33,2.19 -3.38,4.04 -6.02,5.16 -5.24,2.22 -11.13,0.93 -14.64,-2.79 0,0 -66.45,27.28 -66.45,27.28 -1.04,4.29 -3.88,8.13 -7.94,10.55 0,0 7.64,29.58 7.64,29.58 0,0 50.14,-4.17 50.14,-4.17 0.72,-3.86 3.44,-7.37 7.59,-9.13 6.47,-2.74 13.96,-0.12 16.70,5.84 2.74,5.97 -0.28,13.04 -6.77,15.78 -5.77,2.44 -12.33,0.62 -15.64,-4.01 0,0 -49.83,4.15 -49.83,4.15 0,0 9.82,38.03 9.82,38.03 -4.48,0.60 -9.05,0.94 -13.69,1.00 0,0 -19.33,-74.79 -19.33,-74.79 -6.12,-1.26 -11.20,-5.59 -12.77,-11.67 -2.25,-8.71 3.54,-17.68 12.95,-20.06 8.58,-2.16 17.20,1.96 20.35,9.33 0,0 64.21,-26.35 64.21,-26.35 0.34,-3.82 2.68,-7.39 6.39,-9.47 -13.86,-9.58 -30.63,-15.26 -48.76,-15.42 -48.21,-0.43 -87.64,38.29 -88.07,86.50 -0.17,19.29 5.94,37.17 16.41,51.72 14.04,6.43 29.62,10.11 46.07,10.26 51.89,0.46 95.91,-34.09 109.68,-81.60 -3.19,-13.35 -9.47,-25.51 -18.03,-35.70 z" style="fill:url(#.rd3);stroke:none"/></g>'
    o += '<path d="m 145.03,-797.14 c 0,0 -64.21,26.35 -64.21,26.35 -3.14,-7.37 -11.76,-11.49 -20.35,-9.33 -9.40,2.37 -15.20,11.35 -12.95,20.06 1.57,6.08 6.65,10.41 12.77,11.67 0,0 19.33,74.79 19.33,74.79 4.63,-0.05 9.20,-0.39 13.69,-1.00 0,0 -9.82,-38.03 -9.82,-38.03 0,0 49.83,-4.15 49.83,-4.15 3.30,4.64 9.86,6.45 15.64,4.01 6.48,-2.74 9.51,-9.81 6.77,-15.78 -2.74,-5.96 -10.22,-8.59 -16.70,-5.84 -4.14,1.75 -6.86,5.26 -7.59,9.13 0,0 -50.14,4.17 -50.14,4.17 0,0 -7.64,-29.58 -7.64,-29.58 4.05,-2.42 6.89,-6.25 7.94,-10.55 0,0 66.45,-27.28 66.45,-27.28 3.51,3.72 9.40,5.01 14.64,2.79 2.64,-1.11 4.68,-2.96 6.02,-5.16 -5.03,-5.99 -10.84,-11.29 -17.30,-15.75 -3.71,2.08 -6.05,5.65 -6.39,9.47 z"/><path d="m 109.47,-660.64 c -1.81,-7.01 -8.29,-11.71 -15.66,-12.04 0,0 -0.49,-1.90 -0.49,-1.90 -4.48,0.60 -9.05,0.94 -13.69,1.00 0,0 1.34,5.21 1.34,5.21 -4.76,4.00 -7.12,10.21 -5.55,16.29 0.04,0.19 0.12,0.37 0.17,0.56 8.05,2.54 16.61,3.95 25.49,4.03 1.95,0.01 3.89,-0.05 5.82,-0.16 2.65,-3.73 3.74,-8.40 2.55,-13.00 z"/>'
    return o +  '</g>\n'

def compute_js_regex_offline():
    """
    This is to make sure that Python and Javascript parsers use the same regex
    However javascript need some transformation since it does not support regex comments
    If one regex change, please report the result in javascript code
    """
    print '// Javascript Code Start REGEX from Python'
    print "var __REG_NODES__ = /%s/g;"%re.sub(r'((?<!\\)\#[^\n]*\n|\s)','',__REG_NODES__)
    print "var __REG_EDGES__ = /%s/g;"%re.sub(r'((?<!\\)\#[^\n]*\n|\s)','',__REG_EDGES__)
    print '// End REGEX'
    """
    // Javascript Code Start REGEX from Python
    var __REG_NODES__ = /(?:(\w+)|(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"))+(:\w+)?(@\S{10})?\s*(?:\#[^\n]*(?:\n|$))?/g;
    var __REG_EDGES__ = /(?:(\w+)|(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"))+(:\w+)?(@\S{10})?\s*(?:\#[^\n]*(?:\n|$))?\s*(->|<-|-!-|[\d\.]*-[\d\.]*)\s*(?:(\w+)|(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"))+(:\w+)?(@\S{10})?\s*(?:\#[^\n]*(?:\n|$))?/g;
    // End REGEX
    """

def diff_patch_test():
    import diff_match_patch
    dmp = diff_match_patch.diff_match_patch()
    start = 'AAAAA\nCCCCC'
    middle = 'AABAA\nCCDCC'
    end = 'AABAA\nECDCE'
    obj1 = dmp.patch_make(start, middle)
    obj2 = dmp.patch_make(middle, end)
    pt = dmp.patch_toText(obj1) + dmp.patch_toText(obj2)
    #print pt
    patches = dmp.patch_fromText(pt)
    result = dmp.patch_apply(patches, start)
    #print result[0]    
    pp = '@@ -1 +1,2 @@\n \n+t\n\n@@ -1 +1,2 @@\n z\n+t\n'
    print pp
    patches = dmp.patch_fromText(pp)
    result = dmp.patch_apply(patches, '')
    print result
    pp = '@@ -1 +1,2 @@\n z\n+t\n\n@@ -1 +1,2 @@\n z\n+t\n'
    print pp
    patches = dmp.patch_fromText(pp)
    result = dmp.patch_apply(patches, '')
    print result

def regex_test():
    #txt = ' - . \# $ AA - \# [B \] B] CC[D D] EE:G [F F]:G YY[U U]:H # Z\nG # L'
    txt = 'A[B]'
    #print txt

    REG1 = r'(?:(\w+)|(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"))+(:\w+)?(@\S{10})?\s*(?:\#[^\n]*(?:\n|$))?';
    #for m in re.compile(REG1,re.X).finditer(txt):
    #    print (m.group(1),m.group(2))

    m = re.match(r'(?:(A+)|(B+))+','AB')
    print (m.group(),m.group(1),m.group(2))
    #('AB', 'A', 'B')
    """
    var m = /(?:(A+)|(B+))+/.exec('AB');
    alert (m[0] + ',' + m[1] + ',' + m[2]);
    //   AB,undefined,B
    """

    #txt = 'A->B [A A]->[B B] # C->C'
    #print txt
    #for m in re.compile(__REG_EDGES__,re.X).finditer(txt):
    #    print (m.group(1),m.group(2),m.group(3),m.group(4),m.group(5),m.group(6),m.group(7),m.group(8),m.group(9))

if __name__ == '__main__':
    """ This is not executed by the web application"""
    #compute_js_regex_offline()
    diff_patch_test()
    #regex_test()
    print 'OK'

    
