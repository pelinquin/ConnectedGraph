#!/usr/bin/python
# -*- coding: latin-1 -*-
#-----------------------------------------------------------------------------
# ©  Copyright 2011 Rockwell Collins, Inc 
#    This file is part of TRAMweb.
#
#    TRAMweb is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    TRAMweb is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with TRAMweb.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------

"""
 This script is called from Apache in 'mod_python' publisher mode
 As 'mod_python' will soon no longer be supported by Apache,
 ...this shall move to 'mod_wsgi'

 Another way to investigate is to use the Pyjama toolkit

SMALL FIXING REMINDER:
- Fix event capture bug for editing (shift click on a node)
- Implement Graphic Connector editing (drag&drop)
- Improve shapes for KAOS nodes types
"""

import os,re
import xml.sax.saxutils
import random
import urllib
import dbhash
import datetime
import hashlib,base64
from subprocess import Popen, PIPE

__version__  = '0.1.11h'
_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml" '
_SVGNS    = 'xmlns="http://www.w3.org/2000/svg" '
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink" '
# Better use a directory not cleaned at server reset
__BASE__ = '/db'
#__BASE__ = '/tmp'
__TITLE__ = 'Connected Graph'

##### COMMON REGULAR EXPRESSIONS #####

__REG_NODES__ = re.compile(r""" # capture nodes
    (\w*) #g1: name
    ( #g2:label
      (?<!\\)\( (?:\\\)|[^\)])+ (?<!\\)\) | #() delimiter
      (?<!\\)\[ (?:\\\]|[^\]])+ (?<!\\)\] | #[] delimiter
      (?<!\\)\" (?:\\\"|[^\"])+ (?<!\\)\" | #\" delimiter
      (?<!\\)<  (?:\\>|[^\->])+ (?<!\\)>  | #<> delimiter
     ) 
    :?(\w*) #g3:typ
    ( @\S{10} | ) #g4:child
    (\s*\#[^\n]*\n|) # g5:comment
    """,re.X)

__REG_EDGES__ = re.compile(r""" # capture OR connected nodes
        (\w*) #g1: name1
        ( #g2:label1
         (?<!\\)\( (?:\\\)|[^\)])+ (?<!\\)\) |
         (?<!\\)\[ (?:\\\]|[^\]])+ (?<!\\)\] |
         (?<!\\)\" (?:\\\"|[^\"])+ (?<!\\)\" |
         (?<!\\)<  (?:\\>|[^\->])+ (?<!\\)>  |
        ) 
        :?(\w*) #g3:typ1
        ( @\S{10} | ) #g4:child1
        \s*
        (->|<-|-!-|[\d\.]*-[\d\.]*) #g5 connector
        \s*
        (\w*) #g6: name2
        ( #g7:label2
         (?<!\\)\( (?:\\\)|[^\)])+ (?<!\\)\) |
         (?<!\\)\[ (?:\\\]|[^\]])+ (?<!\\)\] |
         (?<!\\)\" (?:\\\"|[^\"])+ (?<!\\)\" |
         (?<!\\)<  (?:\\>|[^\->])+ (?<!\\)>  |
        ) 
        :?(\w*) #g8:typ2
        ( @\S{10} | ) #g9:child2
    """,re.X)

__REG_AND__ = re.compile(r""" # capture AND connected nodes
        \{([^\}]+)\} #g1: connected nodes
        \s*>\s* # AND connector
        (\w*) #g2: name
        ( #g3:label
         (?<!\\)\( (?:\\\)|[^\)])+ (?<!\\)\) | # () delimiter
         (?<!\\)\[ (?:\\\]|[^\]])+ (?<!\\)\] | # [] delimiter
         (?<!\\)\" (?:\\\"|[^\"])+ (?<!\\)\" | # \" delimiter
         (?<!\\)<  (?:\\>|[^\->])+ (?<!\\)>  | # <> delimiter
        ) 
        :?(\w*) #g4:typ
        ( @\S{10} | ) #g5:child
    """,re.X)

##########

def cutline(txt,r=2.4):
    """
    Create a <text> object with several lines using <tspan>
    The ratio width/height is function of r...you can adjust it

    """
    reg = re.compile(r'(\s)')
    buf = '<text>'
    line,pos = 1,0
    first=True
    for m in reg.finditer(txt):
        i = m.start()
        if i > pos + r*lrac(len(txt)):
            if first:
                buf += txt[pos:i]
            else:
                buf += '<tspan x="0" dy="1em">%s</tspan>'%txt[pos:i]
            first = False
            pos,line = i+1,line+1
    if first:
        buf += txt[pos:]
    else:
        buf += '<tspan x="0" dy="1em">%s</tspan>'%txt[pos:]
    return emphasis(buf) + '</text>'

def cutline_class(txt):
    """ cut lines on ';' for new line and '|' for class cathegory """
    return '<text><tspan style="font-weight:bold;">' + re.sub(r'\|','</tspan><tspan sep="y" x="0" dy="20">',re.sub(r';','</tspan><tspan x="0" dy="20">',txt + '</tspan></text>'))
    
def emphasis(buf):
    """ 3 levels of emphasis
    italic: 1 quote
    bold: 2 quotes
    italic bold: 3 quotes
    """
    buf = re.sub(r'\'{3}(\w+)\'{3}','<tspan style="font-style:italic;font-weight:bold;">\\1</tspan>',buf)
    buf = re.sub(r'\'\'(\w+)\'\'','<tspan style="font-weight:bold;">\\1</tspan>',buf)
    return re.sub(r'\'(\w+)\'','<tspan style="font-style:italic;">\\1</tspan>',buf)

def cutline_other(txt,r=2.4,x=0,y=10):
    """ Another cutting algo...need to compare perf with cutline"""
    c = int(r * lrac(len(txt)))+1
    buf = '\n<text transform="translate(%d);" y="%d">'%(x,y)
    j,pos = c,0
    first=True
    while j < len(txt):
        m = re.search('\s',txt[j:])
        if m:
            l = m.start()
            i = l+j
            if first:
                buf += txt[pos:i]
            else:
                buf += '<tspan x="0" dy="1em">%s</tspan>\n'%txt[pos:i]
            first = False
            if (i-pos)>c:
                c=i-pos	
            pos = i
            j += l
        j += c
    if first:
        buf += txt[pos+1:]
    else:
        buf + '<tspan x="0" dy="1em">%s</tspan>\n'%txt[pos+1:]
    return buf + '</text>\n'

def defs():
    """ SVG gradients and markers"""
    o = '<defs>'
    o += '<radialGradient id=".grady" cx="0%" cy="0%" r="90%"><stop offset="0%" stop-color="#FFD"/><stop offset="100%" stop-color="#DDA" class="end"/></radialGradient>'
    #o += '<linearGradient x1="0%" y1="0%" x2="100%" y2="100%" id=".grad2"><stop class="begin" offset="0%"/><stop class="end" offset="100%"/></linearGradient>'
    o += '<radialGradient id=".grad" cx="0%" cy="0%" r="90%"><stop offset="0%" stop-color="#FFF"/><stop offset="100%" stop-color="#DDD" class="end"/></radialGradient>'
    o += '<radialGradient id=".gradbackground" cx="5%" cy="5%" r="95%"><stop offset="0%" stop-color="#FFF"/><stop offset="100%" stop-color="#EEE" class="end"/></radialGradient>'
    o += '<pattern id="pattern" patternUnits="userSpaceOnUse" width="60" height="60"><circle fill="black" fill-opacity="0.5" cx="30" cy="30" r="10"/></pattern>'
  
    o += '<marker id=".arrow" viewBox="-13 -6 15 12" refX="0" refY="0" markerWidth="8" markerHeight="10" orient="auto"><path d="M-8,-6 L0,0 -8,6 Z" stroke="gray" fill="gray" stroke-linejoin="round" stroke-linecap="round"/></marker>'
    o += '<marker id=".conflict" viewBox="0 0 1000 1000" preserveAspectRatio="none" refX="0" refY="100" markerWidth="30" markerHeight="80" orient="auto"><path d="M100,0 l-20,80 l120,-20 l-100,140 l20,-80 l-120,20 Z" stroke="none" fill="red"/></marker>'

    o += '<marker id=".simple_start" viewBox="-10 -10 100 100" preserveAspectRatio="xMidYMin meet" refX="-10" refY="-15" markerWidth="160" markerHeight="30" orient="0"><text  stroke-width="0" fill="gray">0..1</text></marker>'
    o += '<marker id=".simple_end" viewBox="-10 -10 100 100" preserveAspectRatio="xMinYMin meet" refX="20" refY="5" markerWidth="160" markerHeight="30" orient="auto"><text  stroke-width="0" fill="gray">0..*</text></marker>'

    o += '<marker id=".not" viewBox="-13 -6 10 12" refX="-20" markerWidth="8" markerHeight="16" orient="auto"><path d="M-10,-5 L-10,5" stroke="gray"/></marker>'
    
    o += '<filter id=".shadow" filterUnits="userSpaceOnUse"><feGaussianBlur in="SourceAlpha" result="blur" id=".feGaussianBlur" stdDeviation="2" /><feOffset dy="3" dx="2" in="blur" id=".feOffset" result="offsetBlur"/><feMerge><feMergeNode in="offsetBlur"/><feMergeNode in="SourceGraphic" /></feMerge></filter>'

    #o += '<filter id = ".shadow2" width = "150%" height = "150%"><feOffset result = "offOut" in = "SourceGraphic" dx = "3" dy = "3"/><feBlend in = "SourceGraphic" in2 = "offOut" mode = "normal"/></filter>'

    o += '<filter id=".shadow1" x="0" y="0"><feGaussianBlur stdDeviation="5"/><feOffset dx="5" dy="5"/></filter>'
    return o + '</defs>\n'

def parse_typ(t):
    """ parse node type """
    if t:
        if t[0] == '(':
            return 'GOAL'
        elif t[0] == '[':
            return 'REQUIREMENT'
        elif t[0] == '<':
            return 'AGENT'
        if re.match('^(r|req|requirement)$',t,re.IGNORECASE):
            return 'REQUIREMENT'
        elif re.match('^(g|goal)$',t,re.IGNORECASE):
            return 'GOAL'
        elif re.match('^(a|agent|people)$',t,re.IGNORECASE):
            return 'AGENT'
        elif re.match('^(o|obs|obstacle)$',t,re.IGNORECASE):
            return 'OBSTACLE'
        elif re.match('^(s|asso|association)$',t,re.IGNORECASE):
            return 'ASSOCIATION'
        elif re.match('^(t|ent|entity)$',t,re.IGNORECASE):
            return 'ENTITY'
        elif re.match('^(e|exp|expectation)$',t,re.IGNORECASE):
            return 'EXPECTATION'
        elif re.match('^(o|op|operation)$',t,re.IGNORECASE):
            return 'OPERATION'
        elif re.match('^(p|pr|prop|property)$',t,re.IGNORECASE):
            return 'PROPERTY'
        elif re.match('^(v|ev|event)$',t,re.IGNORECASE):
            return 'EVENT'
        elif re.match('^(c|cl|class)$',t,re.IGNORECASE):
            return 'CLASS'
    return ''

####
def cg_parent(raw,idc):
    """ """
    lab,typ,ch = {},{},{}
    reverse = {}
    n = 0
    raw = re.sub(r'#[^\n]*\n','',raw)
    for m in __REG_NODES__.finditer(raw):
        if m.group(1) or m.group(2):
            name,label,typp,child = m.group(1),m.group(2)[1:-1],m.group(3),m.group(4)
            if typp:
                typp = parse_typ(typp)
            else:
                typp = parse_typ(m.group(2))
            if name:
                if typp:
                    typ[name] = typp
                if child:
                    ch[child[1:]] = name
                if lab.has_key(name):
                    if label:
                        lab[name] = label
                else:
                    if label:
                        lab[name] = label
                    else:
                        lab[name] = name
            else:
                if not reverse.has_key(label):
                    tid = '.n%d'%n
                    lab[tid] = label
                    reverse[label] = tid
                    if typp:
                        typ[tid] = typp
                    if child:
                        ch[child[1:]] = tid
                    n += 1
    label,role = '',''
    if ch.has_key(idc):
        if lab.has_key(ch[idc]):
            label = lab[ch[idc]]
        if typ.has_key(ch[idc]):
            role = typ[ch[idc]]
    o = '<text x="18" y="50" class="noderole" id=".noderole">%s </text>\n'%role
    o += '<text class="header" x="60" y="50" id=".nodelabel">%s </text>\n'%emphasis(label)
    return o     

class cg:
    """ Connected Graphs class"""
    def __init__(self,raw,lout={},edit=False,rev=''):
        self.lab,self.typ,self.pos,self.child = {},{},{},{}
        self.connectors = []
        self.r = {}
        self.w,self.h,self.m,self.offset = 600,400,40,40
        self.edit = edit
        self.rev = rev
        n = 0
        raw = re.sub(r'#[^\n]*\n','\n',raw)
        for m in __REG_NODES__.finditer(raw):
            if m.group(1) or m.group(2):
                name,label,typ,child = m.group(1),re.sub(r'\\','',m.group(2)[1:-1]),m.group(3),m.group(4)
                if typ:
                    typ = parse_typ(typ)
                else:
                    typ = parse_typ(m.group(2))
                if name:
                    if typ:
                        self.typ[name] = typ
                    if child:
                        self.child[name] = child[1:]
                    if self.lab.has_key(name):
                        if label:
                            self.lab[name] = label
                    else:
                        if label:
                            self.lab[name] = label
                        else:
                            self.lab[name] = name
                else:
                    if not self.r.has_key(label):
                        tid = '.n%d'%n
                        # TO REVIEW if sha1 based id is not better !
                        #tid = base64.urlsafe_b64encode(hashlib.sha1('.n%d'%n).digest())[:-20]
                        self.lab[tid] = label
                        self.r[label] = tid
                        if typ:
                            self.typ[tid] = typ
                        if child:
                            self.child[tid] = child[1:]
                        n += 1
        for i in self.lab.keys():
            if lout.has_key(i):
                self.pos[i] = lout[i]
            else:
                self.pos[i] = [random.randint(self.m,self.w-2*self.m),random.randint(self.m+self.offset,self.h-2*self.m)]
        #####
        for m in __REG_EDGES__.finditer(raw):
            key1,key2 = 'error1','error2'
            if (m.group(1) or m.group(2)) and (m.group(6) or m.group(7)):
                n1 = m.group(1)
                if n1:
                    key1 = n1
                else:
                    l1 = re.sub(r'\\','',m.group(2)[1:-1])
                    if self.r.has_key(l1):
                        key1 = self.r[l1]
                n2 = m.group(6)
                if n2:
                    key2 = n2
                else:
                    l2 = re.sub(r'\\','',m.group(7)[1:-1])
                    if self.r.has_key(l2):
                        key2 = self.r[l2]
                        
            if key1 != key2:
                if m.group(5) == '->':
                    self.connectors.append((key2,key1))
                elif m.group(5) == '<-':
                    self.connectors.append((key1,key2))
                elif m.group(5) == '-!-':
                    self.connectors.append((key1,key2,'conflict'))
                elif re.match('^[\d\.]*-[\d\.]*$',m.group(5)):
                    self.connectors.append((key1,key2,m.group(5)))     
        for m1 in __REG_AND__.finditer(raw):
            key1,key2 = 'error3','error4'
            if m1.group(2) or m1.group(3):
                name = m1.group(2)
                if name:
                    key2 = name
                else:
                    label = m1.group(3)[1:-1]
                    if self.r.has_key(label):
                        key2 = self.r[label]
            tot = ''
            for m in __REG_NODES__.finditer(m1.group(1)):
                if m.group(1) or m.group(2):
                    name = m.group(1)
                    if name:
                        if self.lab.has_key(name):
                            key1 = name
                    else:
                        label = re.sub(r'\\','',m.group(2)[1:-1])
                        if self.r.has_key(label):
                            key1 = self.r[label]
                    if tot:
                        tot += ':'+key1
                    else:
                        tot = key1
            self.connectors.append((key2,tot))
    
    def get_k(self):
        """ return k ratio """
        if self.lab:
            return lrac(self.w*self.h/len(self.lab))*2/3
        else:
            return 0
        
    def layout(self,coef=10,nb=50):
        """ Force directed graph layout (adapted from Fruchterman & Reingold)
        Repulsion [fr(d)=-k²/d]
        Attraction [fa(d)=d²/k] 
        """
        self.k = self.get_k()
        disp = {}
        for i in self.lab.keys():
            disp[i] = [0,0]
        #print 'Begin:%s'%(self.pos)
        for it in range(nb):
            energy = 0
            for i in self.lab.keys(): # Repulsion
                disp[i] = [0,0]
                for j in self.lab.keys():
                    if i != j:
                        dx = self.pos[j][0] - self.pos[i][0]
                        dy = self.pos[j][1] - self.pos[i][1]
                        d = lrac(dx*dx+dy*dy) - 10
                        if d<1:
                            d=1
                        disp[i][0] -= dx*self.k*self.k/d/d/coef
                        disp[i][1] -= dy*self.k*self.k/d/d/coef 
                        #print '\t%s'%disp[i]
            for c in self.connectors: # Attraction 
                l = c[0]
                for n in c[1].split(':'):
                    if n[0] == '!':
                        n = n[1:]
                    dx = self.pos[l][0] - self.pos[n][0]
                    dy = self.pos[l][1] - self.pos[n][1]
                    d = lrac(dx*dx+dy*dy) - 10
                    if d<1:
                        d=1
                    disp[l][0] -= dx*d/self.k/coef/2
                    disp[l][1] -= dy*d/self.k/coef/2
                    disp[n][0] += dx*d/self.k/coef/2
                    disp[n][1] += dy*d/self.k/coef/2
            for i in self.lab.keys():
                d = lrac(disp[i][0]*disp[i][0] + disp[i][1]*disp[i][1])
                if d < 1:
                    d=1    
                t = int(self.w/4/float(it+1))
                #print t
                #t = 10000
                cx = abs(disp[i][0]) if abs(disp[i][0]) < t else t
                cy = abs(disp[i][1]) if abs(disp[i][1]) < t else t
                dx,dy = disp[i][0]*cx/d,disp[i][1]*cy/d
                energy += dx*dx + dy*dy
                self.pos[i][0] += dx
                self.pos[i][1] += dy
            sx,sy = 0,0
            for i in self.pos.keys():
                sx += self.pos[i][0]
                sy += self.pos[i][1]
            sx = sx/len(self.pos) - self.w/2
            sy = sy/len(self.pos) - self.h/2
            for i in self.pos.keys():
                self.pos[i][0] -= sx
                self.pos[i][1] -= sy
                self.limit_screen(self.pos[i])
            #print 'Iteration:%s %s %s %s %s'%(it,energy,disp,self.pos,t)
        #print 'End:%s %s'%(energy,self.pos)
        return energy

    def limit_screen(self,p):
        if p[0] < self.m:
            p[0] = self.m
        elif p[0] > self.w - self.m:
            p[0] = self.w - self.m
        if p[1] < self.m + self.offset:
            p[1] = self.m + self.offset
        elif p[1] > self.h - self.m:
            p[1] = self.h - self.m  

    def get_node(self):
        """ for unitary test """
        return '%s'%self.lab

    def get_child(self):
        """ for unitary test """
        return '%s'%self.child

    def get_type(self):
        """ for unitary test """
        return '%s'%self.typ

    def get_connectors(self):
        """ for unitary test """
        return '%s'%self.connectors
    
    def graph(self):
        """  """
        mygit = _git()
        o = '<g %s>'%_SVGNS
        o += '<g id=".nodes">\n'
        for i in self.lab.keys():
            (x,y) = self.pos[i]
            style = (1,'gray','GOAL')
            role = ' role="%s"'%self.typ[i] if self.typ.has_key(i) else ''
            ref = ''
            if self.child.has_key(i):
                ref = ' href="%s"'%self.child[i]
                # test if attach doc exists
                #if os.path.isfile('%s/cg/ath/%s'%(__BASE__,self.child[i])):
                if self.rev and mygit.test(self.child[i],self.rev):
                    ref += ' attach="yes"'
            label = xml.sax.saxutils.quoteattr(self.lab[i])
            ed = ' class="node"' if self.edit else ' '
            o += '<g id="%s"%s%s label=%s transform="translate(%s,%s)" %s><title>%s</title>'%(i,ref,role,label,x,y,ed,i)
            if self.typ.has_key(i) and self.typ[i] == 'CLASS':
                o += cutline_class(xml.sax.saxutils.escape(self.lab[i]))
            else:
                o += cutline(xml.sax.saxutils.escape(self.lab[i]))
            o += '</g>'
        o += '</g>\n'
        for c in self.connectors:
            if len(c) > 2:
                o += '<connector n1="#%s" n2="#%s" type="%s"/>\n'%(c[0],c[1],c[2])
            else:
                o += '<connector n1="#%s" n2="#%s"/>\n'%(c[0],c[1])
        o += '<text class="stat" id=".stat" x="10" y="99%%" >%d nodes %d connectors</text>'%(len(self.lab.keys()),len(self.connectors))
        #o += '<g transform="translate(200,200)"><use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="#s1"/></g>'
        #o += '<use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="#s1"/>'
        return o + '</g>\n'

def lrac(x):
    """integer sqrt (heron)"""
    if x == 0:
        return 0
    lg = len(str(x))-1
    r1 = 10**(lg>>1)*[1,3][lg%2]  
    while True:
        r2 = (r1+x//r1)>>1 
        if abs(r1-r2) < 2:
            if r1*r1 <= x and (r1+1)*(r1+1) > x:
                return r1
        r1 = r2

def lrac1(x):
    """integer sqrt (heron)"""
    lg = len(str(x))-1
    return 10**(lg>>1)*[1,3][lg%2]
    
def get_ip(r):
    """ """
    r.add_common_vars()
    env = r.subprocess_env.copy()
    ip = env['REMOTE_ADDR'] if env.has_key('REMOTE_ADDR') else '0.0.0.0'
    return ip

def get_user(r):
    """ """
    r.add_common_vars()
    env = r.subprocess_env.copy()
    user = env['REMOTE_USER'] if env.has_key('REMOTE_USER') else 'anonymous'
    return user

#### Berkeley Database ####

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

def register_graph(content=''):
    """ If the same diagram is requested, diagram id does not change"""
    base='%s/cg'%__BASE__
    if not os.path.isdir(base):
        os.mkdir(base)
    rev = dbhash.open('%s/rev.db'%base,'c')
    if rev.has_key(content):
        gid = rev[content]
    else:
        gid = create_id(rev)
        rev[content] = gid
    rev.close()    
    return gid

def create_id(rev):
    """ Create a new diagram id"""
    rev['_'] = '%d'%(long(rev['_'])+1) if rev.has_key('_') else '0'
    return base64.urlsafe_b64encode(hashlib.sha1(rev['_']).digest())[:-18]

#### GIT CALL ####
class _git:
    """ All git methods share the same env """
    def __init__(self,user='anybody',ip='0.0.0.0'):
        """ create the GIT repository if needed"""
        base='%s/cg'%__BASE__
        e = os.environ.copy()
        e['GIT_AUTHOR_NAME'],e['GIT_AUTHOR_EMAIL'] = user,ip
        e['GIT_COMMITTER_NAME'],e['GIT_COMMITTER_EMAIL'] = 'laurent','pelinquin@gmail.com'
        e['GIT_DIR'] = '%s/.git'%base
        self.e = e
        if not os.path.isdir(e['GIT_DIR']):
            Popen(('git', 'init','-q'), env=e,close_fds=True).communicate()
            p = Popen(('git', 'hash-object','-w','--stdin'), env=e, stdout=PIPE, stdin=PIPE)
            li = '100644 blob %s\tstart\n'%p.communicate(' \n')[0].strip()
            q = Popen(('git', 'mktree'), env=e, stdout=PIPE, stdin=PIPE)
            r = Popen(('git', 'commit-tree', q.communicate(li)[0].strip()), env=e, stdout=PIPE, stdin=PIPE)
            Popen(('git', 'update-ref', 'refs/heads/master',r.communicate('start')[0].strip()), env=e, stdout=PIPE).communicate()

    def add_old(self):
        """ """
        p1 = Popen(('git', 'add','/tmp/cg/ath/2kuSN7rMzf'), env=self.e,stdout=PIPE,stderr=PIPE)
        out1, err1 = p1.communicate('')
        p2 = Popen(('git', 'commit','-a','-m0'), env=self.e,stdout=PIPE,stderr=PIPE)
        out2, err2 = p2.communicate('')
        return (err1,err2)

    def save_file(self,key):
        """ """
        k1 = '@%s'%key
        p = Popen(('git', 'show', 'master^{tree}:'+k1), env=self.e, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate('')
        p = Popen(('git', 'ls-tree', 'master^{tree}'), env=self.e, stdout=PIPE)
        liste = p.communicate()[0].strip()
        if err:
            liste += '\n100644 blob %s\t%s'%(self.sha_file(key),k1) 
            self.commit (liste,k1)
        else:
            self.commit(re.sub(r'(100644 blob) [0-9a-f]{40}(\t%s)'%k1,'\\1 %s\\2'%self.sha_file(key),liste),k1)
        p = Popen(('git', 'log','--pretty=format:%H','-1'), env=self.e, stdout=PIPE)
        return p.communicate()[0].strip()

    def save(self,key,c,state=''):
        """ """
        p = Popen(('git', 'show', 'master^{tree}:'+key), env=self.e, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate('')
        p = Popen(('git', 'ls-tree', 'master^{tree}'), env=self.e, stdout=PIPE)
        liste = p.communicate()[0].strip()
        if err:
            liste += '\n100644 blob %s\t%s'%(self.sha(c),key) 
            self.commit (liste,key)
        else:
            if out[:-1] != c:
                self.commit(re.sub(r'(100644 blob) [0-9a-f]{40}(\t%s)'%key,'\\1 %s\\2'%self.sha(c),liste),key+'\n'+state)
        p = Popen(('git', 'log','--pretty=format:%H','-1'), env=self.e, stdout=PIPE)
        return p.communicate()[0][:15]

    def save_mult(self,k1,k2,c1,c2,state=''):
        """ """
        p = Popen(('git', 'ls-tree', 'master^{tree}'), env=self.e, stdout=PIPE)
        liste = p.communicate()[0].strip()
        p = Popen(('git', 'show', 'master^{tree}:'+k1), env=self.e, stdout=PIPE, stderr=PIPE)
        out1, err1 = p.communicate('')
        p = Popen(('git', 'show', 'master^{tree}:'+k2), env=self.e, stdout=PIPE, stderr=PIPE)
        out2, err2 = p.communicate('')
        if err1:
            liste += '\n100644 blob %s\t%s'%(self.sha(c1),k1) 
        else:
            if out1[:-1] != c1:
                liste = re.sub(r'(100644 blob) [0-9a-f]{40}(\t%s)'%k1,'\\1 %s\\2'%self.sha(c1),liste)
        if err2:
            liste += '\n100644 blob %s\t%s'%(self.sha(c2),k2)
        else:
            if out2[:-1] != c2:
                liste = re.sub(r'(100644 blob) [0-9a-f]{40}(\t%s)'%k2,'\\1 %s\\2'%self.sha(c2),liste)
        self.commit (liste,k2+'\n'+state)

    def sha(self,content):
        """ """
        p = Popen(('git', 'hash-object','-w','--stdin'), env=self.e, stdout=PIPE, stdin=PIPE)
        return p.communicate(content+'\n')[0].strip()

    def sha_file(self,key):
        """ """
        p = Popen(('git', 'hash-object','-w','%s/cg/ath/%s'%(__BASE__,key)), env=self.e, stdout=PIPE, stdin=PIPE)
        return p.communicate()[0].strip()
    
    def commit(self,li,msg):
        """ """
        p = Popen(('git', 'mktree'), env=self.e, stdout=PIPE, stdin=PIPE)
        sha = p.communicate(li)[0].strip()
        p = Popen(('git', 'show-ref','--hash','refs/heads/master'), env=self.e, stdout=PIPE)
        parent = p.communicate()[0].strip()
        p = Popen(('git', 'commit-tree', sha,'-p',parent), env=self.e, stdout=PIPE, stdin=PIPE)
        mm = p.communicate(msg)[0].strip()
        p = Popen(('git', 'update-ref', 'refs/heads/master',mm), env=self.e, stdout=PIPE)

    def getlist(self):
        """ """
        p = Popen(('git', 'ls-tree', 'master^{tree}'), env=self.e, stdout=PIPE)
        liste = p.communicate()[0].strip()
        return liste.split('\n')

    def gethistory(self,key=''):
        """ """
        if key:
            p = Popen(('git', 'log', '--pretty=format:%H:%an:%ar:%s','--',key), env=self.e, stdout=PIPE)
        else:
            p = Popen(('git', 'log', '--pretty=format:%H:%an:%ar:%s'), env=self.e, stdout=PIPE)
        liste = p.communicate()[0].strip()
        return liste.split('\n')

    def gethead(self,key):
        """ """
        p = Popen(('git', 'log', '-1', '--pretty=format:%H:%an:%ar:%at','--',key), env=self.e, stdout=PIPE) # ar
        return p.communicate()[0].strip()
    
    def revision(self,key):
        """ """
        c = Popen(('git', 'log', '-1', '--pretty=format:%H','--', key), env=self.e, stdout=PIPE)
        return c.communicate()[0][:15]

    def date(self,key):
        """ """
        c = Popen(('git', 'log', '-1', '--pretty=format:%ci','--', key), env=self.e, stdout=PIPE)
        return c.communicate()[0][:-5]

    def cat(self,key):
        """ """
        p = Popen(('git', 'show', 'master^{tree}:'+key), env=self.e, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        return '[Diagram Not Found! cat]' if err else out[:-1]

    def cat_blob(self,key):
        """ """
        p = Popen(('git', 'show', key), env=self.e, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        return '' if err else out[:-1]

    def cat_revision(self,gid):
        """ """
        p = Popen(('git', 'show', 'master^{tree}:%s'%gid), env=self.e, stdout=PIPE, stderr=PIPE)
        content, err = p.communicate()
        c = Popen(('git', 'log', '-1', '--pretty=format:%H', '--', gid), env=self.e, stdout=PIPE)
        rev = c.communicate()[0]
        return ('','[Diagram Not Found cat_revision!]') if err else (rev[:15],content[:-1])

    def cat_getrev(self,rev):
        """ """
        c = Popen(('git', 'log', '--pretty=format:%H:%s','-1',rev), env=self.e, stdout=PIPE, stderr=PIPE)
        out,err = c.communicate()
        idd,cont = ['',''],'[Diagram Not Found!]'
        if not err:
            if out != '':
                idd = out.strip().split(':')
                p = Popen(('git', 'show','%s:%s'%(rev,idd[1])), env=self.e, stdout=PIPE, stderr=PIPE)
                cont = p.communicate()[0][:-1]
        return idd[0][:15],idd[1],cont

    def cat_full(self,key,arev):
        """ """
        c = Popen(('git', 'log', '--pretty=format:%H','-1',arev), env=self.e, stdout=PIPE, stderr=PIPE)
        out,err = c.communicate()
        rev,cont = '','[Diagram Not Found!]'
        if not err:
            if out != '':
                rev = out.strip()
                p = Popen(('git', 'show','%s:%s'%(rev,key)), env=self.e, stdout=PIPE, stderr=PIPE)
                cont = p.communicate()[0][:-1]
        return rev[:15],cont

    def cat_simple(self,key,rev):
        """ """
        p = Popen(('git', 'show','%s:%s'%(rev,key)), env=self.e, stdout=PIPE, stderr=PIPE)
        return p.communicate()[0][:-1]

    def test(self,key,rev):
        """ """
        c = Popen(('git', 'log', '%s:@%s'%(rev,key)), env=self.e, stdout=PIPE, stderr=PIPE)
        o,e = c.communicate()
        return False if e else True

#### GRAPHVIZ (DEPRECATED) ####

def graphviz(raw):
    """ call graphviz to get SVG """
    dot = 'digraph Diagram { graph [ rankdir=TB style=filled arrowType="inv"] node [fontname="purisa,cursive"] edge [arrowType="inv" color=grey]\n' + raw + '\n}\n'
    p = Popen(['dot', '-q', '-Tsvg'], stdout=PIPE, stdin=PIPE)
    o = p.communicate(input=dot)[0]
    o = re.sub('(font-size:[\d\.]+);',r'\1px;',o) # Graphviz bug
    o = re.sub('<!DOCTYPE[^\]]+\]>','',o)
    o = re.sub('<\!--[^\-]+-->','',o)
    o = re.sub('<\?xml[^\?]+\?>\n*<svg','<svg',o)
    return o

#### HMI ####

def mode_button(mG,mT):
    """ """
    o = '<g fill="#CCC" class="button" onclick="mode(evt);" stroke="white" transform="translate(1,1) scale(0.1)">'
    o += '<g stroke="white" id=".rmode" display="%s"><title>viewer mode</title><rect width="300" height="290" rx="50"/>'%mT
    o += '<path d="M 280,150 a 160,160 0 0,0 -260,0 a 160,160 0 0,0 260,0 M 130.5,96.4 a 57,57 0 1,1 -34.1,34.1" stroke="white" stroke-width="10" stroke-linecap="square"/>'
    o += '<path d="M 150,150 L 136.4,112 a 40,40 0 1,1 -24.4,24.4 z" stroke-width="0" fill="white"/>'
    o += '</g>'
    o += '<g id=".wmode" display="%s"><title>switch to editor mode</title>'%mG
    o += '<path d="M 246,4 L 49,4 C 24,4 4,24 4,49 L 3,136 L 159,292 L 246,292 C 271,292 292,271 292,246 L 292,49 C 292,24 271,4 246,4 z"/>'
    o += '<path d="M 246,4 L 176,4 L 68,111 L 27,268 L 185,228 L 292,120 L 292,49 C 292,24 271,4 246,4 z" style="fill:white"/>'
    o += '<path d="M 99,249 L 46,196 L 33,248 C 30,259 36,266 48,263 L 99,249 z"/>'
    o += '<path d="M 169,200 C 178,208 191,208 200,200 L 292,108 L 292,49 C 292,49 292,48 292,47 L 169,169 C 161,178 161,191 169,200 z M 259,5 L 133,132 C 124,141 124,154 132,163 C 141,171 154,171 163,163 L 290,36 C 287,29 284,22 278,17 L 278,17 C 273,12 267,8 259,5 z M 126,126 L 248,4 C 247,4 247,4 246,4 L 187,4 L 95,95 C 87,104 87,117 95,126 C 104,134 117,134 126,126 z"/>'
    o += '</g>'
    return o + '</g>'

def save_button(mygit,gid):
    """ """
    o = '<g class="button" onclick="save_all(evt);" fill="#CCC" transform="translate(32,1)"><title>save current diagram</title>'
    o += '<rect width="30" height="30" rx="5"/>'
    o += '<g transform="translate(3,3) scale(0.04)"><path fill="white" d="M 7,404 C 7,404 122,534 145,587 L 244,587 C 286,460 447,158 585,52 C 614,15 542,0 484,24 C 396,61 231,341 201,409 C 157,420 111,335 111,335 L 7,404 z"/></g>'
    # tags
    o += '<g id="tags" display="none"><foreignObject y="30" x="-12" width="80" height="70">' 
    o += '<div %s><title>GIT tag</title>'%_XHTMLNS
    o += '<input id=".tag" size="7" value="" onchange="record_tag();"/>'
    o += '</div></foreignObject></g>'
    # history
    o += '<g id="history" display="none" transform="translate(-25,50)"><text class="history">'
    for i in mygit.gethistory(gid)[:-1]:
        l = i.split(':')
        cat = mygit.cat(l[3])
        o += '<tspan x="0" rev="%s" title="%s" dy="0.9em">%s %s %s</tspan>'%(l[0],l[0][:15],l[1],l[2],short(extract_content(cat)))
    o += '</text></g>'
    return o + '</g>'

def connect_button():
    """ """
    o = '<g class="button" id="_connect" state="on" title="connector mode" onclick="connect(evt);" fill="#CCC" transform="translate(32,32)">'
    o += '<rect width="30" height="30" rx="5"/>'
    o += '<g transform="translate(3,3) scale(0.04)"><path fill="white" d="M 7,404 C 7,404 122,534 145,587 L 244,587 C 286,460 447,158 585,52 C 614,15 542,0 484,24 C 396,61 231,341 201,409 C 157,420 111,335 111,335 L 7,404 z"/></g>'
    return o + '</g>'

def load_session(req):
    """ """
    from mod_python import Session
    session = Session.DbmSession(req)
    session.load()
    mode = session['mode'] if session.has_key('mode') else 'graph'
    user = session['user'] if session.has_key('user') else ''
    return mode,user

#### UTILITIES ####

def extract_all(raw):
    """
    line1:parent id
    line2:ref table
    line3:layout
    line4:content
    """
    lines = raw.split('\n')
    lout = {}
    for n in lines[2].split():   #ici
        [tid,x,y] = n.split(':')
        lout[tid] = (int(x),int(y))
    content = '\n'.join(lines[3:]) #ici
    return lines[0],lout,content

def extract_content(raw):
    """ all lines after line 3"""
    lines = raw.split('\n')
    content = '\n'.join(lines[3:]) # ici
    return content

def extract_lout(raw):
    """ Third line"""
    lout,lines = {},raw.split('\n')
    for n in lines[2].split(): # ici
        [tid,x,y] = n.split(':')
        lout[tid] = (int(x),int(y))
    return lout

def update_child(raw,gid,name):
    """ inserts gid adress after the node(name,label)"""
    l = raw.split('\n')
    content = '\n'.join(l[1:]) 
    rev,n = {},0
    for m in __REG_NODES__.finditer(content):
        if m.group(1) or m.group(2):
            na,la = m.group(1),re.sub(r'\\','',m.group(2)[1:-1])
            na1,la1 = na,la
            if na:
                if not la:
                    la1=na
            else:
                if not rev.has_key(la):
                    na1,rev[la] = '.n%d'%n,na
                    n += 1
            if na1 == name:
                return l[0] + '\n' + content[:m.end(4)] + '@'+gid + content[m.end(4):]
    return 'pb!'

def update_g(req,g,label,name):
    """ """
    req.content_type = 'text/plain'
    return update_child_label(g.value,label,name)
    
def update_child_label(content,new_lab,n1):
    """ change label of the node(name)"""
    lab,position,has_label = {},{},{}
    rev,n = {},0
    result = {}
    for m in __REG_NODES__.finditer(content):
        if m.group(1) or m.group(2):
            name,label = m.group(1),re.sub(r'\\','',m.group(2)[1:-1])
            if label:
                deb,fin = m.start(2)+1,m.end(2)-1
            else:
                deb,fin = m.end(2),m.end(2)
            if name:
                if lab.has_key(name):
                    if label:
                        lab[name] = (True,deb,fin)
                else:
                    lab[name] = (True,deb,fin) if label else (False,deb,fin)
            else:
                if not rev.has_key(label):
                    tid = '.n%d'%n
                    lab[tid] = (True,deb,fin)
                    rev[label] = tid
                    n += 1
    if lab.has_key(n1):
        if lab[n1][0]:
            return content[:lab[n1][1]] +new_lab + content[lab[n1][2]:]
        else:
            return content[:lab[n1][1]] + '"'+new_lab+'"' + content[lab[n1][2]:]
    return 'pb!'

def short(content,title=False):
    """ """
    sh = content
    if len(content) >= 35:
        sh = xml.sax.saxutils.escape(content[:33]) + '...'
    else:
        sh = xml.sax.saxutils.escape(sh)
        if not title:
            sh += '&#160;'.join(['' for x in xrange(35-len(content))])
    return sh

def shortlog(content):
    """ """
    sh = re.sub('\n',' ',content)
    if len(content) >= 45:
        return sh[:43] + '...'
    else:
        return sh

def save_session(req,user='',mode=''):
    """ """
    from mod_python import Session
    session = Session.DbmSession(req)
    try:
        session['hits'] += 1
    except:
        session['hits'] = 1
    if mode:
        session['mode'] = mode
    session['user'] = user
    session.save()
    req.content_type = 'text/plain'
    return 'ok'

def get_server(r):
    """ """
    r.add_common_vars()
    env = r.subprocess_env.copy()
    se = 'http://%s%s'%(env['SERVER_NAME'],env['SCRIPT_NAME']) if (env.has_key('SERVER_NAME') and env.has_key('SCRIPT_NAME')) else ''
    return se

##### HTTP CALL ####

def new_graph(req,g,user,ip,name='',parent=''):
    """ GIT """
    mygit = _git(user,ip)
    gid = register_graph()
    old_content = mygit.cat(parent)
    remove_rev(old_content)
    tab = old_content.split('\n')
    new_raw = tab[0] + '\n' + tab[1] + '\n' + update_child(g.value,gid,name) # g->layout+content
    mygit.save_mult(gid,parent,'%s\n\n\n'%parent,new_raw,'NEW_CHILD') # ici
    return gid

def new_attach(req,g,user,ip,gid,typ):
    """ GIT """
    mygit = _git(user,ip)
    base='%s/cg/ath'%__BASE__
    if not os.path.isdir(base):
        os.mkdir(base)
    import tempfile
    (fd,dfile) = tempfile.mkstemp()
    da = os.fdopen(fd,'w')
    da.write(urllib.unquote(g.value))
    da.close()
    os.chmod(dfile,0777)
    target = '%s/cg/ath/%s'%(__BASE__,gid)
    import shutil
    pdfile = '%s.pdf'%dfile
    if typ == 'text/x-tex':
        Popen(('cd /tmp; pdflatex %s;mv %s %s'%(dfile,pdfile,target)), shell=True).communicate()
    elif typ == 'application/vnd.oasis.opendocument.text':
        Popen(('openoffice.org -headless -nofirststartwisard -accept="socket,host=localhost,port=8100;urp;StarOffice.Service"'), shell=True).communicate()
        sys.path.append('/home/laurent/formose/ConnectedGraph')
        import DocumentConverter
        cv = DocumentConverter.DocumentConverter()    
        cv.convert(dfile, pdfile)
        shutil.copy(pdfile,target)
    else:
        shutil.copy(dfile,target)
    if os.path.isfile(dfile):
        os.remove(dfile)
    rev = mygit.save_file(gid)
    return "Document saved with Git\n%s"%(rev)

def load_pdf(req,gid,rev):
    """ Read on GIT """
    req.content_type = 'application/pdf'
    mygit = _git()
    return mygit.cat_simple('@'+gid,rev)

def list(req,history=''):
    """ Temporary html listing (to be removed) """
    req.content_type = 'text/html'
    mygit = _git()
    o = '<html>'
    o += '<link href="../cg.css" rel="stylesheet" type="text/css"/>'
    o += '<div class="ribbon"><a href="https://github.com/pelinquin/ConnectedGraph">Fork me on GitHub</a></div>'
    o += '<h1>Connected Graph</h1>'
    n,t = 0, []
    o += '<table border="1" cellspacing="0" style="font-family: sans-serif; font-size: 8pt;}">'
    if not history:
        for i in sorted(mygit.getlist()):
            m = re.search(r'^100644 blob ([0-9a-f]{40})\t(\w+)$',i)
            if m:
                rev = m.group(1)
                gid = m.group(2)
                h =  mygit.gethead(gid).split(':')
                if gid != 'start':
                    n += 1
                    cat = mygit.cat_blob(rev)                
                    t.append([h[3],gid,rev,h[1],h[2],short( extract_content(cat))])
        o += '<tr><th>&nbsp;</th><th colspan="3">%d diagrams</th><th>Content</th></tr>'%n
        n = 0
        for i in sorted(t, key = lambda item:item[0],reverse=True):
            n+=1
            o += '<tr title="%s">'%i[1]
            o += '<td>%05d</td>'%n
            o += '<td><a href="edit?@%s" style="font-family:courier;">%s</a></td>'%(i[1],i[1])
            o += '<td>%s</td>'%i[3]
            o += '<td>%s</td>'%i[4]
            o += '<td>%s</td>'%i[5]
            o += '</tr>'
    else:
        n = 0
        for i in mygit.gethistory()[:-1]:
            n+=1
            l = i.split(':')
            if l[3][0] == '@':
                resume = 'PDF file'
            else:
                resume = short( extract_content(mygit.cat(l[3])))
            o += '<tr><td>%05d</td><td><a style="font-family:courier;" href="edit?%s">%s</a></td><td>%s</td><td>%s</td><td><a style="font-family:courier;" href="edit?@%s">%s</a></td><td>%s</td></tr>'%(n,l[0],l[0][:15],l[1],l[2],l[3],l[3],resume)
    return o + '</table><h6>%s</h6></html>'%__version__

def edit(req,login='',pw='',pw2=''):
    """ edit mode """
    #ch = True if check_user(login,pw) else False
    #mode,user_old = get_mode_user(req)
    #user = login if ch else user_old
    #msg =  'Bad login/password!' if login and not ch else ' '

    msg,mode,user = ' ','graph',''
    ip = get_ip(req)
    if login:
        if pw2:
            if register_user(login,pw,pw2,ip):
                msg = 'Welcome \'%s\', your account is well created'%login
                user = login
                save_session(req,user)
            else:
                msg = 'Error: login already used or more than 10 logins/ip or difference in repeated password or password too much simple'
        else:
            if check_user(login,pw):
                user = login
                msg = 'Welcome \'%s\''%login
                save_session(req,user)
            else:
                msg = 'Error: bad login/password'
    else:
        mode,user = load_session(req)
    return basic(req,True,mode,'','..',user,msg)

def view(req):
    """ view mode """
    return basic(req,False,'graph')

def index(req,edit=False):
    """ if called with no parameter"""
    valGet = '"Welcome to \'\'ConnectedGraph\'\'!"'
    return basic(req,False,'graph',valGet,'.')
    
def basic(req=None,edit=False,mode='graph',valGet='',pfx='..',user='',msg=''):
    """ common call """
    debug = ''
    base='%s/cg'%__BASE__
    if not os.path.isdir(base):
        os.mkdir(base)

    if not user:
        #user = get_user(req)
        user = 'anonymous'
    ip = get_ip(req)
    mygit = _git(user,ip)
        
    if not valGet:
        if req.args:
            valGet = re.sub('\$','#',re.sub('\\\\n','\n',urllib.unquote(req.args)))
            #valGet = re.sub('\$','#',re.sub('\\\\n','\n',req.args))
            #valGet = valGet.encode('iso-8859-1',replace)
    ##
    gid,rev,content,attrib,lout,praw = '','','','',{},''
    m0 = re.match('^([\da-f]{5,40})\s*$',valGet)
    if m0:
        rev,gid,raw = mygit.cat_getrev(m0.group(1))
        if rev != '':
            attrib,lout,content = extract_all(raw)
            praw = extract_content(mygit.cat(attrib))
    else:
        m1 = re.match('^@(\S{10})\s*$',valGet)
        if m1:
            gid = m1.group(1)
            rev,raw = mygit.cat_revision(gid)
            if rev:
                attrib,lout,content = extract_all(raw)
                praw = extract_content(mygit.cat(attrib))
            else:
                content,gid = '',''
        else:
            m2 = re.match('^@(\S{10}):([\da-f]{5,40})\s*$',valGet)
            if m2:
                gid = m2.group(1)
                rev,raw = mygit.cat_full(gid,m2.group(2))
                if rev:
                    attrib,lout,content = extract_all(raw)
                    praw = extract_content(mygit.cat(attrib))
            else:
                content = valGet
                if edit:
                    gid = register_graph(content)
                    rev = mygit.revision(gid)
                    if rev :
                        raw = mygit.cat(gid)
                        attrib,lout,content = extract_all(raw)
                        praw = extract_content(mygit.cat(attrib))
                    else:
                        raw = '\n\n\n%s'%content # ici
                        rev = mygit.save(gid,raw,'NEW') # no parent
        ###
    git_date = mygit.date(gid) if edit else ''
    req.content_type = 'application/xhtml+xml'

    # log
    log = open('%s/cg/cg.log'%__BASE__,'a')
    d = '%s'%datetime.datetime.now()
    log.write('[%s %s] %s %s %s %s\n'%(d[:19],ip,gid,rev[:10],user,shortlog(content)))
    log.close() 

    empty = True if re.match('^\s*$',content) else False
    o = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    o += '<?xml-stylesheet href="%s/cg.css" type="text/css" ?>\n'%pfx

    init_g = ' onload="init_graph();"' if edit else ' onload="init_graph(true);"'

    (cjs,jsdone) = (init_g,'yes') if (mode == 'graph') and not empty else ('','no')
    
    o += '<svg %s %s id=".base" onclick="closelink();" width="1066" height="852">\n'%(_SVGNS,cjs)
    #o += '<title id=".title">&#10025;%s%s&#8211;</title>'%('' if lout else '*',__TITLE__)
    o += '<title id=".title">%s%s &#8211; %s</title>'%('' if (lout or pfx == '.') else '*',__TITLE__,short(content,True))

    # Find a way to have SVG fav icon instead of png !
    o += '<link %s rel="shortcut icon" href="%s/logo16.png"/>\n'%(_XHTMLNS,pfx)
    o += js(pfx) + defs()

    (mG,mT) = ('inline','none') if mode == 'graph' else ('none','inline')
    xpos = 85 if edit else 10
    clicable = 'onclick="update_url(evt,true);"' if edit else 'onclick="update_url(evt,false);" '
    o += '<g transform="translate(%s,10)" %s>'%(xpos,clicable)
    o += '<text class="hd" id=".content" y="0"><title>content</title>%s</text>'%short(content)
    o += '<text class="hd" id=".gid" y="10"><title>diagram id</title>%s</text>'%gid
    o += '<text class="hd" id=".rev" y="20"><title>revision</title>%s</text>'%rev
    o += '</g>' + link_button()
    o += '<g transform="translate(%s,0)">'%xpos
    o += '<text class="hd1" id=".date" y="20" x="130" ><title>commit date</title>%s</text>'%git_date
    #o += '<text class="hd1" id=".state" title="Process based state (not yet supported!)" y="2" x="280">NEW</text>'
    o += '</g>'

    if edit:
        if user != 'anonymous':
            o += '<text class="hd1" id=".user" x="470" y="12" onclick="logout();"><title>logout</title>%s</text>'%user
        else:
            o += '<text display="none" id=".user">anonymous</text>' # revoir
            o += '<text class="hd" x="505" y="12" onclick="create();"><title>create a new account</title>Signup</text>'
            o += '<text class="hd" x="465" y="12" onclick="login();"><title>log in with existing accountLogin</title>Login</text>'
        o += '<text class="hd1" id=".ip" x="550" y="12"><title>ip address</title>%s</text>'%ip
        o += '<g id=".form" display="none">'
        o += '<foreignObject display="inline" y="1" x="328" width="80" height="70">' 
        o += '<div %s><form id="myform" method="post">'%_XHTMLNS
        o += '<input id="login" name="login" title="Login" size="7" value=""/>'
        o += '<input id="pw" name="pw" type="password" title="Password" size="7" value=""/>'
        o += '<input id="pw2" style="display:none" name="pw2" type="password" title="Password repeat" size="7" value=""/>'
        o += '</form></div>'
        o += '</foreignObject>'
        o += '<g onclick="check();" title="submit login/password" class="button" fill="#CCC" transform="translate(395,1)"><rect x="1" width="15" height="30" rx="5"/><path transform="translate(0,6)" d="M4,4 4,14 14,9" fill="white"/></g>'
        o += '</g>'
        o += '<text class="hd1" id=".status" title="status" x="640" y="12" fill="#999">%s</text>'%msg
    
    if attrib:
        server = get_server(req)
        up_link,disp = 'href="%s"'%attrib,'inline'
    else:
        up_link,disp = '','none'

    action = 'save_up()' if edit else 'go_up()'
    o += '<a title="parent" onclick="%s;" display="%s" id=".parent" %s fill="#CCC" transform="translate(1,31)"><rect rx="5" width="16" height="16"/><path d="M3,13 8,3 13,13" fill="white"/></a>'%(action,disp,up_link)

    o += cg_parent(praw,gid)

    size = len(content.split('\n')) + 2
    if size < 10:
        size = 10
    
    o += '<g id=".textarea" display="%s"><g transform="translate(4,0)"><text style="font-family:Arial;font-size:7pt;" fill="green" y="50">'%mT
    for l in range(size):
        o += '<tspan dy="12pt" x="0">%02d</tspan>'%(l+1)
    o += '</text></g>'
    o += '<foreignObject transform="translate(18,52)" width="99%" height="90%">'
    o += '<textarea %s id=".area" onchange="change_textarea();" spellcheck="false" rows="%d" style="border:1px solid #ccc;width:98.5%%;font-size: 10pt;">%s</textarea>'%(_XHTMLNS,size,xml.sax.saxutils.escape(content))
    o += '</foreignObject></g>'

    unsaved = 'no' if lout else 'layout'
    if debug:
        o += '<text id="debug" x="10" y="90%%">DEBUG: %s</text>'%debug
    s1 = sha1(req)
    o += '<text x="92%%" y="10" fill="gray" style="font-family:Arial;font-size:8pt;"><title>Tool version id:%s</title>%s [%s]</text>'%(s1,__version__,s1)
    o += '<g display="%s" id=".canvas" updated="yes" unsaved="%s" jsdone="%s" title="version %s">'%(mG,unsaved,jsdone,__version__) + run(content,lout,edit,rev) + '</g>'
    
    if edit:
        o += mode_button(mG,mT) + save_button(mygit,gid)
        #o += connect_button()
        #o += attach_button()
        o += '<g class="button" fill="#CCC" transform="translate(62,1)"><rect x="1" width="15" height="30" rx="5"/><path transform="translate(0,6)" d="M4,4 4,14 14,9" fill="white"/>'+ nodes_bar() + '</g>'
        
    if pfx == '.':
        n,t = 0,[]
        for i in mygit.getlist():
            m = re.search(r'^100644 blob ([0-9a-f]{40})\t(\w+)$',i)
            if m:
                rev = m.group(1)
                gid = m.group(2)
                h =  mygit.gethead(gid).split(':')
                if gid != 'start':
                    n+=1
                    cat = mygit.cat_blob(rev)
                    t.append([h[3],gid,rev,h[1],h[2],short( extract_content(cat))])
        o += '<g id="history" onclick="load_item(evt);" transform="translate(10,25)"><text id=".list" fill="#CCC" style="font-family:courier;font-size:11pt;">%d diagrams'%n
        for i in sorted(t, key = lambda item:item[0],reverse=True):
            o += '<tspan gid="%s" dy="0.9em"><title>%s</title>'%(i[1],i[2][:15])
            o += '<tspan x="0">%s %s</tspan>'%(i[1],i[3]) #0
            o += '<tspan x="190">%s</tspan>'%i[4] #180
            o += '<tspan x="330">%s</tspan>'%i[5] #300
            o += '</tspan>'
        o += '</text></g>'

    if edit or pfx == '.':
        o += '<g onclick="load_github();">' + formose() + '<title>FOrmal Requirements Modelling in an Open-Source Environment</title></g>'
    #return graphviz(content)
    return o + '</svg>'

def nodes_bar():
    """ """
    nodes = {'Goal':('G','<path d="M6,13 l22,0 -3,15 -22,0z"/>'),
             'Req':('R','<path d="M6,13 l22,0 -3,15 -22,0z"/>'), 
             'Agent':('A','<path d="M4,20 l5,-8 12,0 5,8 -5,8 -12,0 -5,-8z"/>'),
             'Expect':('E','<rect x="5" y="12" width="22" height="16"/>'), 
             'Asso':('S','<path d="M6,20 l10,-9 10,9 -10,9z"/>'), 
             'Entity':('T','<rect x="5" y ="12" width="22" height="16"/>'),
             'Event':('V','<path d="M6,13 l11,0 11,8 -11,8 -11,0z"/>'),
             'Prop':('P','<path d="M4,17 l11,-5 11,5 0,11 -22,0z"/>'),
             'Operation':('O','<ellipse cx="16" cy="21" rx="11" ry="8"/>'),
             'Obstacle':('B','<path d="M3,13 l22,0 4,15 -22,0z"/>')}
    o = '<g onclick="add_node(evt);" id="bar" transform="translate(16,0)" display="none" style="font-family:Arial;font-size:10pt;" stroke-width="0px">'
    i = 0
    for n in nodes.keys():
        o += '<g id="%s" class="button" cl="%s" fill="#CCC" display="inline" transform="translate(%d,0)"><title>%s</title>'%(n,nodes[n][0],32*i,n)
        o += '<rect width="32" height="32" rx="5" stroke-width="1px" stroke="white"/>'
        o += '<g fill="white">' + nodes[n][1] + '<text style="font-family:sans-serif;" x="11" y="25" fill="#CCC">%s</text>'%nodes[n][0] +'</g>'
        o += '<text x="3" y="10" stroke-width="1px" fill="white" style="font-family:sans-serif;font-size:6pt;">%s</text></g>'%n.upper()
        i += 1
    return o + '</g>'

def attach_button():
    """ """
    o = '<g class="button" onclick="save_attach();" title="Attach PDF document to current node" fill="#CCC" transform="translate(62,1)"><rect x="1" width="20" height="30" rx="5"/><g transform="translate(-1,4) scale(0.5)"><path stroke-linecap="round" fill="none" stroke="#fff" stroke-width="3" d="m21.615,8.810l-11.837,19.944l-0.349,2.677l0.582,2.67l1.28,1.746l5.122,3.143l2.793,0.349l2.095,-0.46l1.746,-1.047l1.746,-2.095l11.990,-20.838l0.698,-2.91l-0.465,-2.444l-1.28,-2.095l-1.746,-0.931l-1.979,-0.349l-1.629,0.349l-1.513,0.582l-1.746,1.280l-1.047,1.746l-9.080,16.065l-0.698,2.444l0.465,1.979l0.931,1.047l1.746,0.349l1.629,-0.814l1.164,-1.164l1.280,-1.629l4.656,-7.79l0.46,-0.81"/></g></g>'
    o += '<foreignObject display="none"><form %s id="myform" method="post"><input type="file" id="fileElem" accept="pdf/*" style="display:none" onchange="new_attach(this.files)"/></form></foreignObject>'%_XHTMLNS
    return o

def link_button():
    """ """
    o = '<foreignObject display="none" width="100%" height="32">'
    o += '<input %s readonly="y" id="linkstring" maxlength="2048" size="57" value=""/>'%_XHTMLNS
    return o + '</foreignObject>'

def run(content='',lout={},edit=False,rev=''):
    """ """
    if content[:14] == 'data:image/svg':
        o = ''
        for l in base64.b64decode(content[25:]).split('\n'):
            if not re.search(r'^<(\?|\/?svg)',l):
                o += re.sub(r'font-size="(\d+)"','style="font-size:\\1pt;"',l)
        return o
    if re.match('^\s*$',content):
        bullet = 'Empty diagram...use canvas toolbox or add text in text view'
        return '<text %s x="150" y="150" stroke-width="1px" fill="#EEE" style="font-family:Arial;font-size:64pt;" gid="" rev=""><title>%s</title>&#8709;</text><g id=".nodes"/>'%(_SVGNS,bullet)
    else:
        mygraph = cg(content,lout,edit,rev)
        if lout == {}:
            mygraph.layout(10,50)
        return mygraph.graph()

def update_graph(req,g,gid,user,ip,name='',label=''):
    """ load GIT"""
    req.content_type = 'image/svg+xml'
    if name and label:
        content = update_child_label(g.value,label,name)
    else:
        content = g.value
    mygit = _git(user,ip)
    raw = mygit.cat(gid)
    lout = extract_lout(raw)
    mygraph = cg(content,lout,True)
    #mygraph.layout(10,50)
    return mygraph.graph()
    
def remove_rev(raw):
    """ remove rev from rev database """
    lines = raw.split('\n')
    content =  '\n'.join(lines[3:]) # ici
    rev = dbhash.open('%s/cg/rev.db'%__BASE__,'c')
    if rev.has_key(content):
        del rev[content]
    rev.close()    

def save_layout(req,lout,gid,user,ip):
    """ IN GIT DB"""
    req.content_type = 'text/plain'
    mygit = _git(user,ip)
    #new_raw = re.sub('\n([^\n]*)\n','\n%s\n'%lout,mygit.cat(gid),1)
    new_raw = re.sub('(\n[^\n]*\n)[^\n]*\n','\\1%s\n'%lout,mygit.cat(gid),1)
    return mygit.save(gid,new_raw,'NEW')

def save_content(req,g,gid,user,ip,msg=''):
    """ IN GIT DB"""
    req.content_type = 'text/plain'
    mygit = _git(user,ip)
    raw = mygit.cat(gid)
    remove_rev(raw)
    new_raw = raw.split('\n')[0]+'\n' + raw.split('\n')[1]+'\n'+g.value
    return mygit.save(gid,new_raw,msg)

def get_env(r):
    """ """
    r.add_common_vars()
    env = r.subprocess_env.copy()
    ip = env['REMOTE_ADDR'] if env.has_key('REMOTE_ADDR') else '0.0.0.0'
    dname = os.path.dirname(env['SCRIPT_FILENAME'])
    bname = os.path.basename(env['SCRIPT_FILENAME'])
    return (dname,bname[:-3],ip)

def get_ip(r):
    """ """
    r.add_common_vars()
    env = r.subprocess_env.copy()
    ip = env['REMOTE_ADDR'] if env.has_key('REMOTE_ADDR') else '0.0.0.0'
    return ip

def sha1(req):
    """ return a partial sha1 to check version easilly """
    (pwd, name,ip) = get_env(req)
    dig = hashlib.sha1(open('%s/%s.py'%(pwd,name)).read() + open('%s/%smin.js'%(pwd,name)).read() + open('%s/%s.css'%(pwd,name)).read())    
    return dig.hexdigest()[:5]
    
def download(req):
    """ dowload all files to rebuild the application"""
    import zipfile
    req.content_type = 'application/zip'
    req.headers_out['Content-Disposition'] = 'attachment; filename=SVG_connectedGraph_%s.zip'%re.sub('\.','_',__version__)
    (pwd, name,ip) = get_env(req)
    dig = hashlib.sha1()    
    dig.update(open('%s/%s.py'%(pwd,name)).read())
    dig.update(open('%s/%s_test.py'%(pwd,name)).read())
    dig.update(open('%s/%s.js'%(pwd,name)).read())
    dig.update(open('%s/%s.css'%(pwd,name)).read())   
    signature = dig.hexdigest()
    sig = open('/tmp/sig','w')
    d = '%s'%datetime.datetime.now()
    sig.write('%s\n%s\n%s'%(d[:19],__version__,dig.hexdigest()))
    sig.close()    
    f = zipfile.ZipFile('/tmp/cg.zip', 'w')
    f.write('%s/%s.py'%(pwd,name),'%s.py'%name, zipfile.ZIP_DEFLATED)
    f.write('%s/%s_test.py'%(pwd,name),'%s_test.py'%name, zipfile.ZIP_DEFLATED)
    f.write('%s/%s.js'%(pwd,name),'%s.js'%name, zipfile.ZIP_DEFLATED)
    f.write('%s/%s.css'%(pwd,name),'%s.css'%name, zipfile.ZIP_DEFLATED)
    f.write('%s/logo16.png'%(pwd),'logo16.png', zipfile.ZIP_DEFLATED)
    f.write('%s/COPYING'%(pwd),'COPYING', zipfile.ZIP_DEFLATED)
    f.write('%s/README'%(pwd),'README', zipfile.ZIP_DEFLATED)
    f.write('%s/formose.conf'%(pwd),'formose.conf', zipfile.ZIP_DEFLATED)
    f.write('/tmp/sig','SHA1_SIGNATURE.txt', zipfile.ZIP_DEFLATED)
    f.close()
    log = open('%s/cg/cg.log'%__BASE__,'a')
    log.write('[%s %s] Download v%s\n'%(d[:19],ip,__version__))
    log.close()
    return open('/tmp/cg.zip').read()

def log(req):
    """ show log file """
    req.content_type = 'text/plain'
    return open('%s/cg/cg.log'%__BASE__).read()

def reset(req):
    """ show log file """
    (pwd, name,ip) = get_env(req)
    req.content_type = 'text/plain'
    #Popen(('rm -rf %s/cg;'%__BASE__), shell=True).communicate()
    return 'reset no allowed !'

def update(req):
    """ update  """
    import time
    (pwd, name,ip) = get_env(req)
    t = datetime.datetime.now()
    d = time.mktime(t.timetuple())
    rev = dbhash.open('%s/cg/rev.db'%__BASE__,'w')
    server,allow,delta = get_server(req),False,d - float(rev['_update_'])
    if rev.has_key('_update_') and not re.search('formose_dev',server):
        if delta > 120:
            rev['_update_'],allow = '%s'%d,True
    if not rev.has_key('_update_'):
        rev['_update_'] = '%s'%d
    rev.close()    
    if not allow:
        req.content_type = 'text/plain'
        return 'Error: Bad server or duration between updates [%f] less than 2 minutes !'%delta
    req.content_type = 'text/html'        
    cmd = 'cd %s/..; rm -rf ConnectedGraph; git clone git://github.com/pelinquin/ConnectedGraph.git; rm -rf ConnectedGraph/.git'%pwd
    out,err = Popen((cmd), shell=True,stdout=PIPE, stderr=PIPE).communicate()
    o = '<html>'
    o += '<link href="../cg.css" rel="stylesheet" type="text/css"/>'
    o += '<h1>Application Update v%s [%s]</h1>'%(__version__,sha1(req))
    o += '<p>Path: %s -> %s</p>'%(pwd,server)    
    if err:
        o += '<p>Error:%s</p>'%err
    else:
        o += '<p>%s</p>'%out
    o += '<a href="%s"><h2>Go to the application</h2></a>'%server    
    return o + '</html>'

def js(pfx):
    """ The content is copied and compressed from cg.js. Do not change this function"""
    return '<script %s type="text/ecmascript" xlink:href="%s/cgmin.js"></script>'%(_XLINKNS,pfx)

def update_js():
    """ to be used to include js in this script"""
    import sys
    js = Popen('./yui-compressor cg.js', stdout=PIPE, shell=True).communicate()
    out = ''
    if js[1] == None:
        found = False
        for l in open(sys.argv[0]).readlines():
            if re.search(r'<script.*<\/script>',l) and not found:
                out += '<script type="text/ecmascript"><![CDATA[ ' + js[0][:-1] + ' ]]></script>\n'
                found = True
            else:
                out += l
    if out:
        py = open(sys.argv[0],'w')
        d = '%s'%datetime.datetime.now()
        py.write(out)
        py.close() 

def formose():
    """ FORMOSE logo """
    return '<!-- Copyright 2010 Stephane Macario --><defs><radialGradient fx="0" fy="0" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(84.70,0.76,-0.76,84.70,171.57,-156.43)" spreadMethod="pad" id=".rd1"><stop style="stop-color:#94d787" offset="0"/><stop style="stop-color:#6bc62e" offset="1"/></radialGradient><radialGradient fx="0" fy="0" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(84.69,0.76,-0.76,84.69,171.58,-156.42)" spreadMethod="pad" id=".rd2"><stop style="stop-color:#94d787" offset="0"/><stop style="stop-color:#6bc62e" offset="1"/></radialGradient><radialGradient fx="0" fy="0" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(161.13,1.45,-1.45,161.13,99.46,-256.92)" spreadMethod="pad" id=".rd3"><stop style="stop-color:#bae381" offset="0"/><stop style="stop-color:#6bc62e" offset="1"/></radialGradient></defs><g transform="matrix(0.21,0,0,0.21,424,176)" style="fill:#ffffff;stroke:none"><g style="fill:#231f20;stroke:none"><path d="m 536.70,-701.72 c 0,0 -332.09,0 -332.09,0 0,0 0,-65.40 0,-65.40 0,0 332.09,0 332.09,0 0,0 0,65.40 0,65.40 z"/><path d="m 561.06,-675.65 c 0,0 -330.70,0 -330.70,0 0,0 0,-68.26 0,-68.26 0,0 330.70,0 330.70,0 0,0 0,68.26 0,68.26 z"/></g><path d="m 237.89,-737.15 c 0,0 0,9.74 0,9.74 0,0 15.65,0 15.65,0 0,0 0,6.37 0,6.37 0,0 -15.65,0 -15.65,0 0,0 0,19.25 0,19.25 0,0 -7.88,0 -7.88,0 0,0 0,-41.98 0,-41.98 0,0 29.34,0 29.34,0 0,0 0,6.61 0,6.61 0,0 -21.45,0 -21.45,0 z"/><path d="m 278.83,-723.11 c 0,4.90 0.88,8.69 2.64,11.38 1.76,2.68 4.32,4.03 7.69,4.03 3.95,0 6.96,-1.31 9.04,-3.94 2.07,-2.63 3.11,-6.45 3.11,-11.47 0,-9.82 -3.85,-14.73 -11.55,-14.73 -3.52,0 -6.23,1.33 -8.11,3.99 -1.88,2.66 -2.82,6.24 -2.82,10.74 z m -8.23,0 c 0,-5.96 1.73,-11.02 5.22,-15.15 3.47,-4.13 8.13,-6.19 13.95,-6.19 6.41,0 11.31,1.87 14.70,5.61 3.38,3.73 5.08,8.98 5.08,15.73 0,6.75 -1.77,12.11 -5.31,16.07 -3.54,3.96 -8.56,5.95 -15.08,5.95 -5.98,0 -10.58,-1.96 -13.77,-5.89 -3.19,-3.92 -4.79,-9.30 -4.79,-16.13 z" /><path d="m 331.08,-737.32 c 0,0 0,11.60 0,11.60 1.45,0.11 2.57,0.17 3.34,0.17 3.29,0 5.71,-0.43 7.24,-1.30 1.52,-0.87 2.29,-2.57 2.29,-5.10 0,-2.05 -0.82,-3.48 -2.45,-4.30 -1.63,-0.81 -4.22,-1.22 -7.74,-1.22 -0.85,0 -1.74,0.05 -2.67,0.17 z m 16.93,35.54 c 0,0 -11.91,-17.39 -11.91,-17.39 -1.19,-0.01 -2.86,-0.08 -5.01,-0.19 0,0 0,17.59 0,17.59 0,0 -8.23,0 -8.23,0 0,0 0,-42.01 0,-42.01 0.44,0 2.16,-0.06 5.14,-0.21 2.98,-0.14 5.38,-0.21 7.21,-0.21 11.32,0 16.98,4.12 16.98,12.37 0,2.48 -0.78,4.74 -2.34,6.78 -1.56,2.04 -3.52,3.48 -5.90,4.32 0,0 13.22,18.96 13.22,18.96 0,0 -9.16,0 -9.16,0 z" /><path d="m 408.88,-701.77 c 0,0 -7.65,0 -7.65,0 0,0 -4.69,-22.61 -4.69,-22.61 0,0 -8.98,23.19 -8.98,23.19 0,0 -2.78,0 -2.78,0 0,0 -8.98,-23.19 -8.98,-23.19 0,0 -4.81,22.61 -4.81,22.61 0,0 -7.65,0 -7.65,0 0,0 9.04,-41.98 9.04,-41.98 0,0 4.17,0 4.17,0 0,0 9.62,28.29 9.62,28.29 0,0 9.39,-28.29 9.39,-28.29 0,0 4.17,0 4.17,0 0,0 9.16,41.98 9.16,41.98 z" /><path d="m 426.17,-723.11 c 0,4.90 0.87,8.69 2.64,11.38 1.76,2.68 4.32,4.03 7.69,4.03 3.95,0 6.96,-1.31 9.04,-3.94 2.07,-2.63 3.11,-6.45 3.11,-11.47 0,-9.82 -3.85,-14.73 -11.55,-14.73 -3.52,0 -6.23,1.33 -8.11,3.99 -1.88,2.66 -2.82,6.24 -2.82,10.74 z m -8.23,0 c 0,-5.96 1.73,-11.02 5.22,-15.15 3.48,-4.13 8.13,-6.19 13.95,-6.19 6.41,0 11.31,1.87 14.70,5.61 3.38,3.73 5.08,8.98 5.08,15.73 0,6.75 -1.77,12.11 -5.31,16.07 -3.54,3.96 -8.56,5.95 -15.08,5.95 -5.98,0 -10.57,-1.96 -13.77,-5.89 -3.19,-3.92 -4.79,-9.30 -4.79,-16.13 z" /><path d="m 468.10,-704.12 c 0,0 2.92,-6.69 2.92,-6.69 3.12,2.08 6.20,3.13 9.23,3.13 4.65,0 6.97,-1.52 6.97,-4.57 0,-1.42 -0.54,-2.79 -1.64,-4.08 -1.09,-1.29 -3.35,-2.75 -6.77,-4.35 -3.41,-1.60 -5.71,-2.93 -6.90,-3.97 -1.18,-1.04 -2.10,-2.27 -2.73,-3.71 -0.64,-1.43 -0.95,-3.01 -0.95,-4.75 0,-3.24 1.25,-5.94 3.78,-8.08 2.52,-2.13 5.75,-3.21 9.70,-3.21 5.14,0 8.92,0.91 11.33,2.72 0,0 -2.40,6.43 -2.40,6.43 -2.77,-1.85 -5.70,-2.78 -8.78,-2.78 -1.82,0 -3.23,0.45 -4.24,1.35 -1.00,0.90 -1.50,2.08 -1.50,3.53 0,2.40 2.83,4.89 8.50,7.48 2.98,1.37 5.14,2.63 6.46,3.79 1.31,1.15 2.32,2.49 3.01,4.03 0.69,1.53 1.03,3.24 1.03,5.13 0,3.39 -1.42,6.18 -4.28,8.37 -2.85,2.19 -6.67,3.28 -11.47,3.28 -4.16,0 -7.92,-1.01 -11.27,-3.04 z" /><path d="m 516.24,-737.15 c 0,0 0,9.74 0,9.74 0,0 14.49,0 14.49,0 0,0 0,6.37 0,6.37 0,0 -14.49,0 -14.49,0 0,0 0,12.64 0,12.64 0,0 20.29,0 20.29,0 0,0 0,6.61 0,6.61 0,0 -28.18,0 -28.18,0 0,0 0,-41.98 0,-41.98 0,0 28.18,0 28.18,0 0,0 0,6.61 0,6.61 0,0 -20.29,0 -20.29,0 z" /><g transform="translate(-5.80,-492.07)"><path d="m 86.77,-176.29 c 0,0 -1.34,-5.21 -1.34,-5.21 -0.84,0.01 -1.69,0.03 -2.54,0.03 -16.44,-0.14 -32.02,-3.82 -46.07,-10.26 10.86,15.09 26.44,26.58 44.59,32.30 -0.05,-0.18 -0.12,-0.36 -0.17,-0.56 -1.57,-6.07 0.78,-12.28 5.55,-16.29 z" style="fill:url(#.rd1);stroke:none"/></g><g transform="translate(-5.80,-492.07)"><path d="m 194.97,-241.90 c 0.06,-7.29 -0.78,-14.39 -2.40,-21.18 -12.30,42.46 -48.78,74.56 -93.44,80.57 0,0 0.49,1.90 0.49,1.90 7.36,0.32 13.85,5.02 15.66,12.04 1.18,4.60 0.10,9.27 -2.55,13.00 45.51,-2.58 81.83,-40.09 82.25,-86.34 z" style="fill:url(#.rd2);stroke:none"/></g><g transform="translate(-5.80,-492.07)"><path d="m 174.53,-298.79 c -1.33,2.19 -3.38,4.04 -6.02,5.16 -5.24,2.22 -11.13,0.93 -14.64,-2.79 0,0 -66.45,27.28 -66.45,27.28 -1.04,4.29 -3.88,8.13 -7.94,10.55 0,0 7.64,29.58 7.64,29.58 0,0 50.14,-4.17 50.14,-4.17 0.72,-3.86 3.44,-7.37 7.59,-9.13 6.47,-2.74 13.96,-0.12 16.70,5.84 2.74,5.97 -0.28,13.04 -6.77,15.78 -5.77,2.44 -12.33,0.62 -15.64,-4.01 0,0 -49.83,4.15 -49.83,4.15 0,0 9.82,38.03 9.82,38.03 -4.48,0.60 -9.05,0.94 -13.69,1.00 0,0 -19.33,-74.79 -19.33,-74.79 -6.12,-1.26 -11.20,-5.59 -12.77,-11.67 -2.25,-8.71 3.54,-17.68 12.95,-20.06 8.58,-2.16 17.20,1.96 20.35,9.33 0,0 64.21,-26.35 64.21,-26.35 0.34,-3.82 2.68,-7.39 6.39,-9.47 -13.86,-9.58 -30.63,-15.26 -48.76,-15.42 -48.21,-0.43 -87.64,38.29 -88.07,86.50 -0.17,19.29 5.94,37.17 16.41,51.72 14.04,6.43 29.62,10.11 46.07,10.26 51.89,0.46 95.91,-34.09 109.68,-81.60 -3.19,-13.35 -9.47,-25.51 -18.03,-35.70 z" style="fill:url(#.rd3);stroke:none"/></g><path d="m 145.03,-797.14 c 0,0 -64.21,26.35 -64.21,26.35 -3.14,-7.37 -11.76,-11.49 -20.35,-9.33 -9.40,2.37 -15.20,11.35 -12.95,20.06 1.57,6.08 6.65,10.41 12.77,11.67 0,0 19.33,74.79 19.33,74.79 4.63,-0.05 9.20,-0.39 13.69,-1.00 0,0 -9.82,-38.03 -9.82,-38.03 0,0 49.83,-4.15 49.83,-4.15 3.30,4.64 9.86,6.45 15.64,4.01 6.48,-2.74 9.51,-9.81 6.77,-15.78 -2.74,-5.96 -10.22,-8.59 -16.70,-5.84 -4.14,1.75 -6.86,5.26 -7.59,9.13 0,0 -50.14,4.17 -50.14,4.17 0,0 -7.64,-29.58 -7.64,-29.58 4.05,-2.42 6.89,-6.25 7.94,-10.55 0,0 66.45,-27.28 66.45,-27.28 3.51,3.72 9.40,5.01 14.64,2.79 2.64,-1.11 4.68,-2.96 6.02,-5.16 -5.03,-5.99 -10.84,-11.29 -17.30,-15.75 -3.71,2.08 -6.05,5.65 -6.39,9.47 z" /><path d="m 109.47,-660.64 c -1.81,-7.01 -8.29,-11.71 -15.66,-12.04 0,0 -0.49,-1.90 -0.49,-1.90 -4.48,0.60 -9.05,0.94 -13.69,1.00 0,0 1.34,5.21 1.34,5.21 -4.76,4.00 -7.12,10.21 -5.55,16.29 0.04,0.19 0.12,0.37 0.17,0.56 8.05,2.54 16.61,3.95 25.49,4.03 1.95,0.01 3.89,-0.05 5.82,-0.16 2.65,-3.73 3.74,-8.40 2.55,-13.00 z"/></g>'
 
if __name__ == '__main__': 
    import sys
    print 'look at cg_test.py for non regression testing'

#end
