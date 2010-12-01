#!/usr/bin/python
# -*- coding: latin-1 -*-
#-----------------------------------------------------------------------------
# ©  Copyright 2010 Rockwell Collins, Inc 
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

 Another way to investicate is to use the Pyjama toolkit

MAIN TODO LIST (see Trac for the full feature request and bug tracking list:
- Install Trac (yes!)
- Define a GitHub project for source sharign
- Solve the problem of permalink on nested diagrams (Git expertise)
- Fix event capture bug for editing (shift click on a node)
- Implement a State Automaton on diagrams
   - Use a Metamodel to define the automaton
   - define user roles
   - Send emails on transitions on demand
- Implement Graphic Connector editing (drag&drop)
- Improve shapes for KAOS nodes types
- Fix problem of adjusting the page size to the current diagram size
- Improve the layout algorithm to avoid link crossing
- Chose MediaWiki or the Trac wiki
- Fix authentification code
- Find a way to insure that given source code = web application

"""

import os,re
import xml.sax.saxutils
import random
import urllib
import dbhash
import datetime
import hashlib,base64
from subprocess import Popen, PIPE

__version__  = '0.1.8'
_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml" '
_SVGNS    = 'xmlns="http://www.w3.org/2000/svg" '
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink" '
# Better use a directory not cleaned at server reset
#__BASE__ = '/db'
__BASE__ = '/tmp'
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
        (->|<-|-!-) #g5 connector
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
    o += '<radialGradient id=".gradyellow" cx="0%" cy="0%" r="90%"><stop offset="0%" stop-color="#FF5"/><stop offset="100%" stop-color="#DD5"/></radialGradient>'
    #o += '<linearGradient x1="0%" y1="0%" x2="100%" y2="100%" id=".grad2"><stop class="begin" offset="0%"/><stop class="end" offset="100%"/></linearGradient>'
    o += '<radialGradient id=".grad" cx="0%" cy="0%" r="90%"><stop offset="0%" stop-color="#FFF"/><stop offset="100%" stop-color="#DDD" class="end"/></radialGradient>'
    o += '<radialGradient id=".gradbackground" cx="5%" cy="5%" r="95%"><stop offset="0%" stop-color="#FFF"/><stop offset="100%" stop-color="#EEE" class="end"/></radialGradient>'
    o += '<pattern id="pattern" patternUnits="userSpaceOnUse" width="60" height="60"><circle fill="black" fill-opacity="0.5" cx="30" cy="30" r="10"/></pattern>'
  
    o += '<marker id=".arrow" viewBox="-13 -6 15 12" refX="0" refY="0" markerWidth="8" markerHeight="10" orient="auto"><path d="M-8,-6 L0,0 -8,6 Z" stroke="gray" fill="gray" stroke-linejoin="round" stroke-linecap="round"/></marker>'
    o += '<marker id=".conflict" viewBox="0 0 1000 1000" preserveAspectRatio="none" refX="0" refY="100" markerWidth="30" markerHeight="80" orient="auto"><path d="M100,0 l-20,80 l120,-20 l-100,140 l20,-80 l-120,20 Z" stroke="none" fill="red"/></marker>'

    o += '<marker id=".not" viewBox="-13 -6 10 12" refX="-20" markerWidth="8" markerHeight="16" orient="auto"><path d="M-10,-5 L-10,5" stroke="gray"/></marker>'
    o += '<filter id=".shadow" filterUnits="userSpaceOnUse"><feGaussianBlur in="SourceAlpha" result="blur" id=".feGaussianBlur" stdDeviation="2" /><feOffset dy="3" dx="3" in="blur" id=".feOffset" result="offsetBlur"/><feMerge><feMergeNode in="offsetBlur"/><feMergeNode in="SourceGraphic" /></feMerge></filter>'
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
    o = '<text x="18" y="50" id=".noderole" fill="#777" style="font-family:Arial;font-size:4pt;">%s </text>\n'%role
    o += '<text x="60" y="50" id=".nodelabel" fill="#777" style="font-family:purisa,cursive;font-size:16pt;">%s </text>\n'%emphasis(label)
    return o     

class cg:
    """ Connected Graphs class"""
    def __init__(self,raw,lout={},edit=False):
        self.lab,self.typ,self.pos,self.child = {},{},{},{}
        self.connectors = []
        self.r = {}
        self.w,self.h,self.m,self.offset = 600,400,40,40
        self.edit = edit
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
        out = '<g %s>'%_SVGNS
        out += '<g id=".nodes" style="font-family:purisa,cursive;">\n'
        for i in self.lab.keys():
            (x,y) = self.pos[i]
            style = (1,'gray','GOAL')
            role = ''
            if self.typ.has_key(i):
                role = ' role="%s"'%self.typ[i]
            ref = ''
            if self.child.has_key(i):
                ref = ' href="%s"'%self.child[i]
            label = xml.sax.saxutils.quoteattr(self.lab[i])
            ed = ' class="node"' if self.edit else ' '
            out += '<g id="%s"%s%s label=%s transform="translate(%s,%s)" %s title="%s">'%(i,ref,role,label,x,y,ed,i)
            out += cutline(xml.sax.saxutils.escape(self.lab[i]))
            out += '</g>'
        out += '</g>\n'
        for c in self.connectors:
            if len(c) > 2:
                out += '<connector n1="#%s" n2="#%s" type="%s"/>\n'%(c[0],c[1],c[2])
            else:
                out += '<connector n1="#%s" n2="#%s"/>\n'%(c[0],c[1])
        out += '<text id=".stat" x="10" y="99%%" fill="gray" style="font-family:Arial;font-size:8pt;">%d nodes %d connectors</text>'%(len(self.lab.keys()),len(self.connectors))
        return out + '</g>\n'

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
    def __init__(self,user,ip):
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
        return p.communicate()[0].strip()

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
        p = Popen(('git', 'log', '-1', '--pretty=format:%H:%an:%ar','--',key), env=self.e, stdout=PIPE)
        return p.communicate()[0].strip()
    
    def load(self,key):
        """ """
        p = Popen(('git', 'show', 'master^{tree}:'+key), env=self.e, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        return '' if err else out[:-1]

    def revision(self,key):
        """ """
        c = Popen(('git', 'log', '-1', '--pretty=format:%H','--', key), env=self.e, stdout=PIPE)
        return c.communicate()[0]

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
        return ('','[Diagram Not Found cat_revision!]') if err else (rev,content[:-1])

    def getrev(self,rev):
        """ """
        c = Popen(('git', 'log', '--pretty=format:%H:%s','-1',rev), env=self.e, stdout=PIPE, stderr=PIPE)
        out,err = c.communicate()
        if err:
            idd,cont = ['',''],'[Diagram Not Found!]'
        else:
            if out == '':
                idd,cont = ['',''],'[Diagram Not Found! 2]'
            else:
                idd = out.strip().split(':')
                p = Popen(('git', 'show','%s:%s'%(rev,idd[1])), env=self.e, stdout=PIPE, stderr=PIPE)
                cont = p.communicate()[0][:-1]
        return idd[0],idd[1],cont

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
    o += '<g stroke="white" id=".rmode" display="%s" title="viewer mode"><rect width="300" height="290" rx="50"/>'%mT
    o += '<path d="M 280,150 a 160,160 0 0,0 -260,0 a 160,160 0 0,0 260,0 M 130.5,96.4 a 57,57 0 1,1 -34.1,34.1" stroke="white" stroke-width="10" stroke-linecap="square"/>'
    o += '<path d="M 150,150 L 136.4,112 a 40,40 0 1,1 -24.4,24.4 z" stroke-width="0" fill="white"/>'
    o += '</g>'
    o += '<g id=".wmode" display="%s" title="editor mode">'%mG
    o += '<path d="M 246,4 L 49,4 C 24,4 4,24 4,49 L 3,136 L 159,292 L 246,292 C 271,292 292,271 292,246 L 292,49 C 292,24 271,4 246,4 z"/>'
    o += '<path d="M 246,4 L 176,4 L 68,111 L 27,268 L 185,228 L 292,120 L 292,49 C 292,24 271,4 246,4 z" style="fill:white"/>'
    o += '<path d="M 99,249 L 46,196 L 33,248 C 30,259 36,266 48,263 L 99,249 z"/>'
    o += '<path d="M 169,200 C 178,208 191,208 200,200 L 292,108 L 292,49 C 292,49 292,48 292,47 L 169,169 C 161,178 161,191 169,200 z M 259,5 L 133,132 C 124,141 124,154 132,163 C 141,171 154,171 163,163 L 290,36 C 287,29 284,22 278,17 L 278,17 C 273,12 267,8 259,5 z M 126,126 L 248,4 C 247,4 247,4 246,4 L 187,4 L 95,95 C 87,104 87,117 95,126 C 104,134 117,134 126,126 z"/>'
    o += '</g>'
    return o + '</g>'

def save_button(mygit,gid):
    """ """
    o = '<g class="button" title="save current diagram" onclick="save_all(evt);" fill="#CCC" transform="translate(32,1)">'
    o += '<rect width="30" height="30" rx="5"/>'
    o += '<g transform="translate(3,3) scale(0.04)"><path fill="white" d="M 7,404 C 7,404 122,534 145,587 L 244,587 C 286,460 447,158 585,52 C 614,15 542,0 484,24 C 396,61 231,341 201,409 C 157,420 111,335 111,335 L 7,404 z"/></g>'
    o += '<g id="history" display="none" transform="translate(-25,26)"><text fill="#CCC" style="font-family:courier;font-size:11pt;">'
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

def get_mode_user(req):
    """ """
    from mod_python import Session
    session = Session.DbmSession(req)
    session.load()
    if session.has_key('mode'):
        mode = session['mode']
    else:
        mode = 'graph'
    if session.has_key('user'):
        user = session['user']
    else:
        user = ''
    return mode,user

#### UTILITIES ####

def extract_all(raw):
    """ """
    lines = raw.split('\n')
    lout = {}
    for n in lines[1].split():
        [tid,x,y] = n.split(':')
        lout[tid] = (int(x),int(y))
    content = '\n'.join(lines[2:])
    return lines[0],lout,content

def extract_content(raw):
    """ """
    lines = raw.split('\n')
    content = '\n'.join(lines[2:])
    return content

def extract_lout(raw):
    """ """
    lout,lines = {},raw.split('\n')
    for n in lines[1].split():
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

def save_session(req,mode,user):
    """ """
    from mod_python import Session
    session = Session.DbmSession(req)
    try:
        session['hits'] += 1
    except:
        session['hits'] = 1
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

def empty_graph(req,gid='',rev=''):
    """ """
    req.content_type = 'image/svg+xml'
    bullet = 'Empty diagram...use canvas toolbox or add text in text view'
    return '<text %s x="150" y="150" stroke-width="1px" fill="#EEE" style="font-family:Arial;font-size:64pt;" title="%s" gid="%s" rev="%s">&#8709;</text><g id=".nodes"/>'%(_SVGNS,bullet,gid,rev)

def new_graph(req,g,user,ip,name='',parent=''):
    """ GIT """
    mygit = _git(user,ip)
    gid = register_graph()
    old_content = mygit.cat(parent)
    remove_rev(old_content)
    new_raw = old_content.split('\n')[0] + '\n' + update_child(g.value,gid,name)
    mygit.save_mult(gid,parent,'%s\n\n'%parent,new_raw,'NEW')
    return gid

def list(req):
    """ """
    req.content_type = 'text/html'
    user = 'anybody'
    mygit = _git(user,get_ip(req))
    out = '<html>'
    out += '<table border="1" cellspacing="0" style="font-family: sans-serif; font-size: 10pt;}">'
    n = 0
    for i in mygit.getlist():
        m = re.search(r'^100644 blob ([0-9a-f]{40})\t(\w+)$',i)
        if m:
            rev = m.group(1)
            gid = m.group(2)
            hh =  mygit.gethead(gid)
            if gid != 'start':
                n+=1
                cat = mygit.cat_blob(rev)
                out += '<tr><td>%05d</td><td title="%s"><a href="edit?@%s" style="font-family:courier;">%s</a></td><td>%s</td><td>%s</td></tr>'%(n,rev,gid,gid,short( extract_content(cat)),hh)
    out += '<table>'

    out += '<table border="1" cellspacing="0" style="font-family: sans-serif; font-size: 10pt;}">'
    n = 0
    for i in mygit.getlist():
        m = re.search(r'^100644 blob ([0-9a-f]{40})\t(\w+)$',i)
        if m:
            rev = m.group(1)
            gid = m.group(2)
            hh =  mygit.gethead(gid).split(':')
            if gid != 'start':
                n+=1
                cat = mygit.cat_blob(rev)
                out += '<tr><td>%05d</td><td title="%s"><a href="edit?@%s" style="font-family:courier;">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(n,rev,gid,gid,short( extract_content(cat)),hh[0][:20],hh[1],hh[2],gid)
    out += '<table>'



    out += '<table border="1" cellspacing="0" style="font-family: sans-serif; font-size: 10pt;">'
    n = 0
    for i in mygit.gethistory()[:-1]:
        n+=1
        l = i.split(':')
        cat = mygit.cat(l[3])
        out += '<tr><td>%05d</td><td><a style="font-family:courier;" href="edit?%s">%s</a></td><td>%s</td><td>%s</td><td><a style="font-family:courier;" href="edit?@%s">%s</a></td><td>%s</td></tr>'%(n,l[0],l[0][:20],l[1],l[2],l[3],l[3],short( extract_content(cat)))
    out += '<table>'
    return out + '</html>'

def createlogin(req,login='',pw1='',pw2=''):
    """ """
    ip = get_ip(req) 
    ch = True if register_user(login,pw1,pw2,ip) else False
    user = 'Welcome \'' + login + '\', your account is well created' if ch else 'Create a new login'
    msg =  'Error: login already used or more than 10 logins/ip or difference in repeated password or password too much simple' if login and not ch else ' '
    req.content_type = 'application/xhtml+xml'
    o = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    o += '<?xml-stylesheet href="../cg.css" type="text/css" ?>\n'
    o += '<svg %s >\n'%_SVGNS
    o += '<title id=".title">%s</title>'%(__TITLE__)
    o += '<link %s rel="shortcut icon" href="../logo16.png"/>\n'%(_XHTMLNS)
    o += js('..')
    title = 'go to main editor' if ch else 'create login'
    o += '<text class="hd" id=".user" title="%s" x="10" y="12" fill="#999" onclick="createlogin(\'%s\');">%s</text>'%(title,ch,user)
    o += '<text class="hd1" id="status" title="ip adsress" x="10" y="32" fill="red">%s</text>'%msg
    o += '<g id="loginform" display="none">'
    o += '<foreignObject display="inline" y="1" x="220" width="80" height="70">' 
    o += '<div %s>'%_XHTMLNS
    o += '<form id="myform" action="createlogin" method="post">'
    o += '<input id="login" name="login" title="Login" size="8" value=""/>'
    o += '<input id="pw1" name="pw1" type="password" title="Password" size="8" value=""/>'
    o += '<input id="pw2" name="pw2" type="password" title="Password repeat" size="8" value=""/>'
    o += '</form>'
    o += '</div>'
    o += '</foreignObject>'
    o += '<g onclick="check();" title="submit login/password" class="button" fill="#CCC" transform="translate(300,12)"><rect x="1" width="15" height="30" rx="5"/><path transform="translate(0,6)" d="M4,4 4,14 14,9" fill="white"/></g>'
    o += '</g>'
    return o + '</svg>'

def edit(req,login='',pw=''):
    """ """
    ch = True if check_user(login,pw) else False
    mode,user_old = get_mode_user(req)
    user = login if ch else user_old
    msg =  'Bad login/password!' if login and not ch else ' '
    return basic(req,True,mode,'','..',user,msg)

def view(req):
    """ view mode """
    return basic(req,False,'graph')

def index(req,edit=False):
    """ if called with no parameter"""
    valGet = '"Welcome to Connected Diagram Tool!"'
    return basic(req,False,'graph',valGet,'.')
    
def basic(req=None,edit=False,mode='graph',valGet='',pfx='..',user='',msg=''):
    """ common call """
    debug=''
    base='%s/cg'%__BASE__
    if not os.path.isdir(base):
        os.mkdir(base)

    if not user:
        user = get_user(req)
    ip = get_ip(req)
    mygit = _git(user,ip)
        
    if not valGet:
        if req.args:
            valGet = re.sub('\$','#',re.sub('\\\\n','\n',urllib.unquote(req.args)))
            #valGet = re.sub('\$','#',re.sub('\\\\n','\n',req.args))
            #valGet = valGet.encode('iso-8859-1',replace)
            #debug = valGet
    ##
    gid,rev,content,attrib,lout,praw = '','','','',{},''
    m0 = re.match('^([\da-f]{5,40})\s*$',valGet)
    if m0:
        rev,gid,raw = mygit.getrev(m0.group(1))
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
            content = valGet
            if edit:
                gid = register_graph(content)
                rev = mygit.revision(gid)
                if rev :
                    raw = mygit.cat(gid)
                    attrib,lout,content = extract_all(raw)
                    praw = extract_content(mygit.cat(attrib))
                else:
                    raw = '\n\n%s'%content
                    rev = mygit.save(gid,raw,'NEW') # no parent
        ###
    git_date = mygit.date(gid) if edit else ''
    req.content_type = 'application/xhtml+xml'
    #req.headers_out['Content-Disposition'] = 'attachment; filename=toto.txt'
    #req.content_type = 'application/zip'
    #req.headers_out['Content-Disposition'] = 'attachment; filename=SVG_connectedGraph_%s.zip'%re.sub('\.','_',__version__)

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
    
    o += '<svg %s %s onclick="closelink();" width="1066" height="852">\n'%(_SVGNS,cjs)
    #o += '<title id=".title">&#10025;%s%s&#8211;</title>'%('' if lout else '*',__TITLE__)
    o += '<title id=".title">%s%s &#8211; %s</title>'%('' if lout else '*',__TITLE__,short(content,True))

    # Find a way to have SVG fav icon instead of png !
    o += '<link %s rel="shortcut icon" href="%s/logo16.png"/>\n'%(_XHTMLNS,pfx)
    o += js(pfx) + defs()
        
    (mG,mT) = ('inline','none') if mode == 'graph' else ('none','inline')
    xpos = 80 if edit else 10
    clicable = 'onclick="update_url(evt,true);"' if edit else 'onclick="update_url(evt,false);" '
    o += '<g transform="translate(%s,10)" stroke-width="1px" fill="#EEE" %s style="font-family:Arial;font-size:8pt;">'%(xpos,clicable)
    o += '<text class="hd" id=".content" title="content" y="0">%s</text>'%short(content)
    o += '<text class="hd" id=".gid" title="diagram id" y="10">%s</text>'%gid
    o += '<text class="hd" id=".rev" title="revision" y="20">%s</text>'%rev
    o += '</g>' + link_button()
    o += '<g transform="translate(%s,10)" fill="#999">'%xpos
    o += '<text class="hd1" id=".date" title="commit date" y="10" x="100" >%s</text>'%git_date
    #o += '<text class="hd1" id=".state" title="Process based state (not yet supported!)" y="2" x="280">NEW</text>'
    o += '</g>'

    if edit:
        (title,way) = ('login',False) if user == 'anonymous' else ('logout',True)
        o += '<text class="hd" id=".user" title="%s" x="470" y="12" fill="#999" onclick="login(\'%s\');">%s</text>'%(title,way,user)
        o += '<text class="hd1" id=".status" title="status" x="640" y="12" fill="#999">%s</text>'%msg
        o += '<text class="hd1" id=".ip" title="ip address" x="540" y="12" fill="#999">%s</text>'%ip
        o += '<g id="loginform" display="none">'
        o += '<foreignObject display="inline" y="1" x="320" width="80" height="52">' 
        o += '<div %s>'%_XHTMLNS
        o += '<form id="myform" action="edit?%s" method="post">'%req.args
        o += '<input id="login" name="login" title="Login" size="8" value=""/>'
        o += '<input id="pw" name="pw" type="password" title="Password" size="8" value=""/>'
        o += '</form>'
        o += '</div>'
        o += '</foreignObject>'
        o += '<g onclick="check();" title="submit login/password" class="button" fill="#CCC" transform="translate(390,1)"><rect x="1" width="15" height="30" rx="5"/><path transform="translate(0,6)" d="M4,4 4,14 14,9" fill="white"/></g>'
        o += '</g>'
    
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
    o += '<text x="96%%" y="10" fill="gray" title="Tool version id:%s" style="font-family:Arial;font-size:8pt;">%s</text>'%(sha1(req),__version__)
    o += '<g display="%s" id=".canvas" updated="yes" unsaved="%s" jsdone="%s" title="version %s">'%(mG,unsaved,jsdone,__version__) + run(content,lout,edit) + '</g>'
    if edit:
        o += mode_button(mG,mT) + save_button(mygit,gid)
        #o += connect_button()
        o += '<g class="button" fill="#CCC" transform="translate(62,1)"><rect x="1" width="15" height="30" rx="5"/><path transform="translate(0,6)" d="M4,4 4,14 14,9" fill="white"/>'+ nodes_bar() + '</g>'

    if pfx == '.':
        o += '<g id="history" onclick="load_item(evt);" transform="translate(10,15)"><text id=".list" fill="#CCC" style="font-family:courier;font-size:11pt;">'
        n = 0
        for i in mygit.getlist():
            m = re.search(r'^100644 blob ([0-9a-f]{40})\t(\w+)$',i)
            if m:
                rev = m.group(1)
                gid = m.group(2)
                h =  mygit.gethead(gid).split(':')
                if gid != 'start':
                    n+=1
                    cat = mygit.cat_blob(rev)
                    o += '<tspan x="0" dy="0.9em" gid="%s" title="%s">%05d %s %s %s %s</tspan>'%(gid,rev,n,gid,h[1],h[2],short( extract_content(cat)))
        o += '</text></g>'

    if edit or pfx == '.':
        o += formose() 
        
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
        o += '<g id="%s" class="button" cl="%s" fill="#CCC" display="inline" title="%s" transform="translate(%d,0)">'%(n,nodes[n][0],n,32*i)
        o += '<rect width="32" height="32" rx="5" stroke-width="1px" stroke="white"/>'
        o += '<g fill="white">' + nodes[n][1] + '<text x="11" y="25" fill="#CCC">%s</text>'%nodes[n][0] +'</g>'
        o += '<text x="3" y="10" stroke-width="1px" fill="white" style="font-family:Arial;font-size:6pt;">%s</text></g>'%n.upper()
        i += 1
    return o + '</g>'

def link_button():
    """ """
    o = '<foreignObject display="none" width="100%" height="32">'
    o += '<input %s readonly="y" id="linkstring" maxlength="2048" size="57" value=""/>'%_XHTMLNS
    return o + '</foreignObject>'

def run(content='',lout={},edit=False):
    """ """
    empty = True if re.match('^\s*$',content) else False
    if empty:
        bullet = 'Empty diagram...use canvas toolbox or add text in text view'
        return '<text %s x="150" y="150" stroke-width="1px" fill="#EEE" style="font-family:Arial;font-size:64pt;" title="%s" gid="" rev="">&#8709;</text><g id=".nodes"/>'%(_SVGNS,bullet)
    else:
        mygraph = cg(content,lout,edit)
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
    """ """
    lines = raw.split('\n')
    content =  '\n'.join(lines[2:])
    rev = dbhash.open('%s/cg/rev.db'%__BASE__,'c')
    if rev.has_key(content):
        del rev[content]
    rev.close()    

def save_layout(req,lout,gid,user,ip):
    """ IN GIT DB"""
    req.content_type = 'plain/text'
    mygit = _git(user,ip)
    new_raw = re.sub('\n([^\n]*)\n','\n%s\n'%lout,mygit.cat(gid),1)
    return mygit.save(gid,new_raw,'NEW')

def save_content(req,g,gid,user,ip,msg=''):
    """ IN GIT DB"""
    req.content_type = 'plain/text'
    mygit = _git(user,ip)
    raw = mygit.cat(gid)
    remove_rev(raw)
    new_raw = raw.split('\n')[0]+'\n'+g.value
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
    """ """
    (pwd, name,ip) = get_env(req)
    dig = hashlib.sha1(open('%s/%s.py'%(pwd,name)).read())    
    return dig.hexdigest()[:5]
    
def download(req):
    """ """
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
    return 'reset no possible'
    #return 'reset done'

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
    return '<!-- Copyright 2010 Stephane Macario --><defs><radialGradient fx="0" fy="0" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(84.70,0.76,-0.76,84.70,171.57,-156.43)" spreadMethod="pad" id=".rd1"><stop style="stop-color:#94d787" offset="0"/><stop style="stop-color:#6bc62e" offset="1"/></radialGradient><radialGradient fx="0" fy="0" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(84.69,0.76,-0.76,84.69,171.58,-156.42)" spreadMethod="pad" id=".rd2"><stop style="stop-color:#94d787" offset="0"/><stop style="stop-color:#6bc62e" offset="1"/></radialGradient><radialGradient fx="0" fy="0" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="matrix(161.13,1.45,-1.45,161.13,99.46,-256.92)" spreadMethod="pad" id=".rd3"><stop style="stop-color:#bae381" offset="0"/><stop style="stop-color:#6bc62e" offset="1"/></radialGradient></defs><g transform="matrix(0.28,0,0,0.28,410,233)" style="fill:#ffffff;stroke:none" title="FOrmal Requirements Modelling in an Open-Source Environment"><g style="fill:#231f20;stroke:none"><path d="m 536.70,-701.72 c 0,0 -332.09,0 -332.09,0 0,0 0,-65.40 0,-65.40 0,0 332.09,0 332.09,0 0,0 0,65.40 0,65.40 z"/><path d="m 561.06,-675.65 c 0,0 -330.70,0 -330.70,0 0,0 0,-68.26 0,-68.26 0,0 330.70,0 330.70,0 0,0 0,68.26 0,68.26 z"/></g><path d="m 237.89,-737.15 c 0,0 0,9.74 0,9.74 0,0 15.65,0 15.65,0 0,0 0,6.37 0,6.37 0,0 -15.65,0 -15.65,0 0,0 0,19.25 0,19.25 0,0 -7.88,0 -7.88,0 0,0 0,-41.98 0,-41.98 0,0 29.34,0 29.34,0 0,0 0,6.61 0,6.61 0,0 -21.45,0 -21.45,0 z"/><path d="m 278.83,-723.11 c 0,4.90 0.88,8.69 2.64,11.38 1.76,2.68 4.32,4.03 7.69,4.03 3.95,0 6.96,-1.31 9.04,-3.94 2.07,-2.63 3.11,-6.45 3.11,-11.47 0,-9.82 -3.85,-14.73 -11.55,-14.73 -3.52,0 -6.23,1.33 -8.11,3.99 -1.88,2.66 -2.82,6.24 -2.82,10.74 z m -8.23,0 c 0,-5.96 1.73,-11.02 5.22,-15.15 3.47,-4.13 8.13,-6.19 13.95,-6.19 6.41,0 11.31,1.87 14.70,5.61 3.38,3.73 5.08,8.98 5.08,15.73 0,6.75 -1.77,12.11 -5.31,16.07 -3.54,3.96 -8.56,5.95 -15.08,5.95 -5.98,0 -10.58,-1.96 -13.77,-5.89 -3.19,-3.92 -4.79,-9.30 -4.79,-16.13 z" /><path d="m 331.08,-737.32 c 0,0 0,11.60 0,11.60 1.45,0.11 2.57,0.17 3.34,0.17 3.29,0 5.71,-0.43 7.24,-1.30 1.52,-0.87 2.29,-2.57 2.29,-5.10 0,-2.05 -0.82,-3.48 -2.45,-4.30 -1.63,-0.81 -4.22,-1.22 -7.74,-1.22 -0.85,0 -1.74,0.05 -2.67,0.17 z m 16.93,35.54 c 0,0 -11.91,-17.39 -11.91,-17.39 -1.19,-0.01 -2.86,-0.08 -5.01,-0.19 0,0 0,17.59 0,17.59 0,0 -8.23,0 -8.23,0 0,0 0,-42.01 0,-42.01 0.44,0 2.16,-0.06 5.14,-0.21 2.98,-0.14 5.38,-0.21 7.21,-0.21 11.32,0 16.98,4.12 16.98,12.37 0,2.48 -0.78,4.74 -2.34,6.78 -1.56,2.04 -3.52,3.48 -5.90,4.32 0,0 13.22,18.96 13.22,18.96 0,0 -9.16,0 -9.16,0 z" /><path d="m 408.88,-701.77 c 0,0 -7.65,0 -7.65,0 0,0 -4.69,-22.61 -4.69,-22.61 0,0 -8.98,23.19 -8.98,23.19 0,0 -2.78,0 -2.78,0 0,0 -8.98,-23.19 -8.98,-23.19 0,0 -4.81,22.61 -4.81,22.61 0,0 -7.65,0 -7.65,0 0,0 9.04,-41.98 9.04,-41.98 0,0 4.17,0 4.17,0 0,0 9.62,28.29 9.62,28.29 0,0 9.39,-28.29 9.39,-28.29 0,0 4.17,0 4.17,0 0,0 9.16,41.98 9.16,41.98 z" /><path d="m 426.17,-723.11 c 0,4.90 0.87,8.69 2.64,11.38 1.76,2.68 4.32,4.03 7.69,4.03 3.95,0 6.96,-1.31 9.04,-3.94 2.07,-2.63 3.11,-6.45 3.11,-11.47 0,-9.82 -3.85,-14.73 -11.55,-14.73 -3.52,0 -6.23,1.33 -8.11,3.99 -1.88,2.66 -2.82,6.24 -2.82,10.74 z m -8.23,0 c 0,-5.96 1.73,-11.02 5.22,-15.15 3.48,-4.13 8.13,-6.19 13.95,-6.19 6.41,0 11.31,1.87 14.70,5.61 3.38,3.73 5.08,8.98 5.08,15.73 0,6.75 -1.77,12.11 -5.31,16.07 -3.54,3.96 -8.56,5.95 -15.08,5.95 -5.98,0 -10.57,-1.96 -13.77,-5.89 -3.19,-3.92 -4.79,-9.30 -4.79,-16.13 z" /><path d="m 468.10,-704.12 c 0,0 2.92,-6.69 2.92,-6.69 3.12,2.08 6.20,3.13 9.23,3.13 4.65,0 6.97,-1.52 6.97,-4.57 0,-1.42 -0.54,-2.79 -1.64,-4.08 -1.09,-1.29 -3.35,-2.75 -6.77,-4.35 -3.41,-1.60 -5.71,-2.93 -6.90,-3.97 -1.18,-1.04 -2.10,-2.27 -2.73,-3.71 -0.64,-1.43 -0.95,-3.01 -0.95,-4.75 0,-3.24 1.25,-5.94 3.78,-8.08 2.52,-2.13 5.75,-3.21 9.70,-3.21 5.14,0 8.92,0.91 11.33,2.72 0,0 -2.40,6.43 -2.40,6.43 -2.77,-1.85 -5.70,-2.78 -8.78,-2.78 -1.82,0 -3.23,0.45 -4.24,1.35 -1.00,0.90 -1.50,2.08 -1.50,3.53 0,2.40 2.83,4.89 8.50,7.48 2.98,1.37 5.14,2.63 6.46,3.79 1.31,1.15 2.32,2.49 3.01,4.03 0.69,1.53 1.03,3.24 1.03,5.13 0,3.39 -1.42,6.18 -4.28,8.37 -2.85,2.19 -6.67,3.28 -11.47,3.28 -4.16,0 -7.92,-1.01 -11.27,-3.04 z" /><path d="m 516.24,-737.15 c 0,0 0,9.74 0,9.74 0,0 14.49,0 14.49,0 0,0 0,6.37 0,6.37 0,0 -14.49,0 -14.49,0 0,0 0,12.64 0,12.64 0,0 20.29,0 20.29,0 0,0 0,6.61 0,6.61 0,0 -28.18,0 -28.18,0 0,0 0,-41.98 0,-41.98 0,0 28.18,0 28.18,0 0,0 0,6.61 0,6.61 0,0 -20.29,0 -20.29,0 z" /><g transform="translate(-5.80,-492.07)"><path d="m 86.77,-176.29 c 0,0 -1.34,-5.21 -1.34,-5.21 -0.84,0.01 -1.69,0.03 -2.54,0.03 -16.44,-0.14 -32.02,-3.82 -46.07,-10.26 10.86,15.09 26.44,26.58 44.59,32.30 -0.05,-0.18 -0.12,-0.36 -0.17,-0.56 -1.57,-6.07 0.78,-12.28 5.55,-16.29 z" style="fill:url(#.rd1);stroke:none"/></g><g transform="translate(-5.80,-492.07)"><path d="m 194.97,-241.90 c 0.06,-7.29 -0.78,-14.39 -2.40,-21.18 -12.30,42.46 -48.78,74.56 -93.44,80.57 0,0 0.49,1.90 0.49,1.90 7.36,0.32 13.85,5.02 15.66,12.04 1.18,4.60 0.10,9.27 -2.55,13.00 45.51,-2.58 81.83,-40.09 82.25,-86.34 z" style="fill:url(#.rd2);stroke:none"/></g><g transform="translate(-5.80,-492.07)"><path d="m 174.53,-298.79 c -1.33,2.19 -3.38,4.04 -6.02,5.16 -5.24,2.22 -11.13,0.93 -14.64,-2.79 0,0 -66.45,27.28 -66.45,27.28 -1.04,4.29 -3.88,8.13 -7.94,10.55 0,0 7.64,29.58 7.64,29.58 0,0 50.14,-4.17 50.14,-4.17 0.72,-3.86 3.44,-7.37 7.59,-9.13 6.47,-2.74 13.96,-0.12 16.70,5.84 2.74,5.97 -0.28,13.04 -6.77,15.78 -5.77,2.44 -12.33,0.62 -15.64,-4.01 0,0 -49.83,4.15 -49.83,4.15 0,0 9.82,38.03 9.82,38.03 -4.48,0.60 -9.05,0.94 -13.69,1.00 0,0 -19.33,-74.79 -19.33,-74.79 -6.12,-1.26 -11.20,-5.59 -12.77,-11.67 -2.25,-8.71 3.54,-17.68 12.95,-20.06 8.58,-2.16 17.20,1.96 20.35,9.33 0,0 64.21,-26.35 64.21,-26.35 0.34,-3.82 2.68,-7.39 6.39,-9.47 -13.86,-9.58 -30.63,-15.26 -48.76,-15.42 -48.21,-0.43 -87.64,38.29 -88.07,86.50 -0.17,19.29 5.94,37.17 16.41,51.72 14.04,6.43 29.62,10.11 46.07,10.26 51.89,0.46 95.91,-34.09 109.68,-81.60 -3.19,-13.35 -9.47,-25.51 -18.03,-35.70 z" style="fill:url(#.rd3);stroke:none"/></g><path d="m 145.03,-797.14 c 0,0 -64.21,26.35 -64.21,26.35 -3.14,-7.37 -11.76,-11.49 -20.35,-9.33 -9.40,2.37 -15.20,11.35 -12.95,20.06 1.57,6.08 6.65,10.41 12.77,11.67 0,0 19.33,74.79 19.33,74.79 4.63,-0.05 9.20,-0.39 13.69,-1.00 0,0 -9.82,-38.03 -9.82,-38.03 0,0 49.83,-4.15 49.83,-4.15 3.30,4.64 9.86,6.45 15.64,4.01 6.48,-2.74 9.51,-9.81 6.77,-15.78 -2.74,-5.96 -10.22,-8.59 -16.70,-5.84 -4.14,1.75 -6.86,5.26 -7.59,9.13 0,0 -50.14,4.17 -50.14,4.17 0,0 -7.64,-29.58 -7.64,-29.58 4.05,-2.42 6.89,-6.25 7.94,-10.55 0,0 66.45,-27.28 66.45,-27.28 3.51,3.72 9.40,5.01 14.64,2.79 2.64,-1.11 4.68,-2.96 6.02,-5.16 -5.03,-5.99 -10.84,-11.29 -17.30,-15.75 -3.71,2.08 -6.05,5.65 -6.39,9.47 z" /><path d="m 109.47,-660.64 c -1.81,-7.01 -8.29,-11.71 -15.66,-12.04 0,0 -0.49,-1.90 -0.49,-1.90 -4.48,0.60 -9.05,0.94 -13.69,1.00 0,0 1.34,5.21 1.34,5.21 -4.76,4.00 -7.12,10.21 -5.55,16.29 0.04,0.19 0.12,0.37 0.17,0.56 8.05,2.54 16.61,3.95 25.49,4.03 1.95,0.01 3.89,-0.05 5.82,-0.16 2.65,-3.73 3.74,-8.40 2.55,-13.00 z"/></g>'
 
if __name__ == '__main__': 
    import sys
    print 'look at cg_test.py for non regression testing'
    #update_js()

#end
