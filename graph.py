#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,re,dbhash,base64,hashlib,datetime,random
import xml.sax.saxutils, urllib
import Cookie
from subprocess import Popen, PIPE
import svgapp

__version__='0.2.1'
__TITLE__='Connected Graph'

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
def gui_elements():
    """ current node + progress bar + node area """
    o = '<g id=".current" class="current" display="none" stroke="red" stroke-width="2" fill="none"><rect/></g>\n'
    o += '<g id=".currentline" class="current" display="none" stroke="red" stroke-width="2" fill="none"><rect/></g>\n'
    #o += '<g display="none" transform="translate(1,10)"><rect text-anchor="end" width="100" height="14" rx="6" ry="6" stroke-width="1px" stroke="#CCC" fill="none"/><rect id=".bar" class="bar" width="0" height="14" rx="6" ry="6"/><text id=".prg" x="44" y="11">0%</text></g>\n'
    o += '<g display="none"><foreignObject id=".area"><textarea %s></textarea></foreignObject></g>\n'%_XHTMLNS
    return o

def menu():
    """ node menu prebuild """
    o = '<g id=".menu"><rect class="theme" rx="4"/>'
    for i in __REG_TYPES__:
        o += '<text class="item">%s</text><g></g>'%__REG_TYPES__[i]
    #o += '</g>\n'
    #o += '<g id=".menu_node"><rect class="theme" rx="4"/>'
    #o += '<text y="30" class="item">Delete node</text>'
    #o += '<text y="30" class="item">Change node to...</text>'
    #o += '</g>\n'
    #o += '<g id=".menu_connector"><rect class="theme" rx="4"/>'
    #o += '<text y="30" class="item">Delete Connector</text>'
    #o += '<text y="30" class="item">Flip connector way</text>'
    return o + '</g>\n'

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

def my_app(environ,start_response):
    """ app """
    start_response('200 OK',[])
    return []

class graph:
    """ """
    def __init__(self,app):
        self.app = app

    def __call__(self,environ, start_response):
        """ app """
        edit_mode,view_mode = environ['PATH_INFO'] == '/edit', environ['PATH_INFO'] == ''
        if not edit_mode and not view_mode:
            return self.app(environ, start_response)
        o = '<script %s type="text/ecmascript" xlink:href="/js/graph.js"/>\n'%_XLINKNS 
        a = ''
        if edit_mode:
            a += svgapp.logo(False) 
            #a += '<rect width="1" height="1"/>' #bug WEBkit
        value = 'A->B'
        value = re.sub('\$','#',re.sub('\\\\n','\n',urllib.unquote(environ['QUERY_STRING'])))
        value = re.sub('mode=[^&]*&?','',value)
        value = re.sub('id=[^&]*&?','',value)
        #m = re.search('id\s*=\s*(\S{10})\s*($|\&)',urllib.unquote(environ['QUERY_STRING']))
        lout = {}
        mygraph = cg(value)
        mygraph.set_pos(lout)
        a += mygraph.draw()    
        if edit_mode:
            a += menu() + gui_elements()
        def custom_start_response(status, header):
            return start_response(status, header)
        response_iter = self.app(environ, custom_start_response)
        response_string = o + ''.join(response_iter) + a 
        return [response_string]

if __name__ == '__main__':
    print 'test'


