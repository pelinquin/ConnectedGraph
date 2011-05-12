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
 USAGE: test file for the server script
 test cases are stored in dictionaries where:
  - the key is the input string
  - the value is the expected result
"""

import ui

set_node = {
    # with child
    'A@RysHufzywk':"{'A': 'A'}",
    'A[AA] A@RysHufzywk':"{'A': 'AA'}",
    'A@RysHufzywk A[AA]':"{'A': 'AA'}",
    'A:R@RysHufzywk':"{'A': 'A'}",
    '[A]:G@Ct58LPl_dd':"{'.n0': 'A'}",
    '[A]@Ct58LPl_dd':"{'.n0': 'A'}",
    '[A]@Ct58LPl_dd B@RysHufzywk':"{'B': 'B', '.n0': 'A'}",
    # one node several definitions
    'AA':"{'AA': 'AA'}",
    ' AA':"{'AA': 'AA'}",
    'AA ':"{'AA': 'AA'}",
    ' AA ':"{'AA': 'AA'}",
    'AA:G':"{'AA': 'AA'}",
    'AA:Goal':"{'AA': 'AA'}",
    'AA[long label]':"{'AA': 'long label'}",
    'AA(long label)':"{'AA': 'long label'}",
    'AA<long label>':"{'AA': 'long label'}",
    'AA(long label)':"{'AA': 'long label'}",
    'AA"long label"':"{'AA': 'long label'}",
    'AA[long label]:G':"{'AA': 'long label'}",
    '[long label]':"{'.n0': 'long label'}",
    '[long label]:G':"{'.n0': 'long label'}",
    # from 1 to 4 nodes
    'A':"{'A': 'A'}",
    'A B':"{'A': 'A', 'B': 'B'}",
    'A B C':"{'A': 'A', 'C': 'C', 'B': 'B'}",
    'A B C D':"{'A': 'A', 'C': 'C', 'B': 'B', 'D': 'D'}",
    # multiple definitions
    'A A A':"{'A': 'A'}",
    'A A[label]':"{'A': 'label'}",
    'A[label] A':"{'A': 'label'}",
    'A[label] A A[label]:G':"{'A': 'label'}",
    '[AA] [AA]:G':"{'.n0': 'AA'}", 
    '[AA] A[AA]:G':"{'A': 'AA', '.n0': 'AA'}",
    # conflicting label
    'A[label1] A[label2]:G':"{'A': 'label2'}", # the last definition win !
    # several nodes with same label
    'A[label] B[label]':"{'A': 'label', 'B': 'label'}",
    'A[label] [label]':"{'A': 'label', '.n0': 'label'}",
    # auto id labels
    '[label0] [label1]':"{'.n1': 'label1', '.n0': 'label0'}",
    # nested brackets
    '[A<B>C(D)]':"{'.n0': 'A<B>C(D)'}",
    # -+=/:|@%&?!. signs
    '[A-B+C=D/E:F|G@H%I&J?K!L.M,N;]':"{'.n0': 'A-B+C=D/E:F|G@H%I&J?K!L.M,N;'}",
    'A-B':"{'A': 'A', 'B': 'B'}",
    'A+B':"{'A': 'A', 'B': 'B'}",
    'A.B':"{'A': 'A', 'B': 'B'}",
    'A,B':"{'A': 'A', 'B': 'B'}",
    # various forms with two nodes 
    'AA BB':"{'AA': 'AA', 'BB': 'BB'}",
    'AA BB:G':"{'AA': 'AA', 'BB': 'BB'}",
    'AA:G BB:G':"{'AA': 'AA', 'BB': 'BB'}",
    'AA:G BB':"{'AA': 'AA', 'BB': 'BB'}",
    'AA BB[BB BB]':"{'AA': 'AA', 'BB': 'BB BB'}",
    'AA BB[BB BB]:G':"{'AA': 'AA', 'BB': 'BB BB'}",
    'AA:G BB[BB BB]:G':"{'AA': 'AA', 'BB': 'BB BB'}",
    'AA:G BB[BB BB]':"{'AA': 'AA', 'BB': 'BB BB'}",
    'AA [BB BB]':"{'AA': 'AA', '.n0': 'BB BB'}",
    'AA [BB BB]:G':"{'AA': 'AA', '.n0': 'BB BB'}",
    'AA:G [BB BB]:G':"{'AA': 'AA', '.n0': 'BB BB'}",
    'AA:G [BB BB]':"{'AA': 'AA', '.n0': 'BB BB'}",
    'AA[AA AA] BB':"{'AA': 'AA AA', 'BB': 'BB'}",
    'AA[AA AA] BB:G':"{'AA': 'AA AA', 'BB': 'BB'}",
    'AA[AA AA]:G BB:G':"{'AA': 'AA AA', 'BB': 'BB'}",
    'AA[AA AA]:G BB':"{'AA': 'AA AA', 'BB': 'BB'}",
    'AA[AA AA] BB[BB BB]':"{'AA': 'AA AA', 'BB': 'BB BB'}",
    'AA[AA AA] BB[BB BB]:G':"{'AA': 'AA AA', 'BB': 'BB BB'}",
    'AA[AA AA]:G BB[BB BB]:G':"{'AA': 'AA AA', 'BB': 'BB BB'}",
    'AA[AA AA]:G BB[BB BB]':"{'AA': 'AA AA', 'BB': 'BB BB'}",
    'AA[AA AA] [BB BB]':"{'AA': 'AA AA', '.n0': 'BB BB'}",
    'AA[AA AA] [BB BB]:G':"{'AA': 'AA AA', '.n0': 'BB BB'}",
    'AA[AA AA]:G [BB BB]:G':"{'AA': 'AA AA', '.n0': 'BB BB'}",
    'AA[AA AA]:G [BB BB]':"{'AA': 'AA AA', '.n0': 'BB BB'}",
    '[AA AA] BB':"{'BB': 'BB', '.n0': 'AA AA'}",
    '[AA AA] BB:G':"{'BB': 'BB', '.n0': 'AA AA'}",
    '[AA AA]:G BB:G':"{'BB': 'BB', '.n0': 'AA AA'}",
    '[AA AA]:G BB':"{'BB': 'BB', '.n0': 'AA AA'}",
    '[AA AA] BB[BB BB]':"{'BB': 'BB BB', '.n0': 'AA AA'}",
    '[AA AA] BB[BB BB]:G':"{'BB': 'BB BB', '.n0': 'AA AA'}",
    '[AA AA]:G BB[BB BB]:G':"{'BB': 'BB BB', '.n0': 'AA AA'}",
    '[AA AA]:G BB[BB BB]':"{'BB': 'BB BB', '.n0': 'AA AA'}",
    '[AA AA] [BB BB]':"{'.n1': 'BB BB', '.n0': 'AA AA'}",
    '[AA AA] [BB BB]:G':"{'.n1': 'BB BB', '.n0': 'AA AA'}",
    '[AA AA]:G [BB BB]:G':"{'.n1': 'BB BB', '.n0': 'AA AA'}",
    '[AA AA]:G [BB BB]':"{'.n1': 'BB BB', '.n0': 'AA AA'}",
    # spaces
    '    A \n B  ':"{'A': 'A', 'B': 'B'}",
    '\nA\nB\n':"{'A': 'A', 'B': 'B'}",
    '<A B>':"{'.n0': 'A B'}",
    '( A B   )':"{'.n0': ' A B   '}", # no strip!
    # comments
    'A\nB # This is a comment \nC':"{'A': 'A', 'C': 'C', 'B': 'B'}",
    'A# This is a comment\nB':"{'A': 'A', 'B': 'B'}",

    # keyworks (no conflict with '.canvas',...) ids
    '.canvas':"{'canvas': 'canvas'}",
    ' .textarea ':"{'textarea': 'textarea'}",
    ' ...nodes ':"{'nodes': 'nodes'}",
    ' .n0 ..n1 n2 ':"{'n0': 'n0', 'n1': 'n1', 'n2': 'n2'}",

    # some math operators 
    'A+B':"{'A': 'A', 'B': 'B'}",
    'A * B':"{'A': 'A', 'B': 'B'}",
    'A = B':"{'A': 'A', 'B': 'B'}",
    '^A':"{'A': 'A'}",
    'A = B + ^C':"{'A': 'A', 'C': 'C', 'B': 'B'}",
    '[A+B]':"{'.n0': 'A+B'}",
    '[A*B]':"{'.n0': 'A*B'}",
    '[A-B]':"{'.n0': 'A-B'}",
    '[A:B]':"{'.n0': 'A:B'}",
    '[^A]':"{'.n0': '^A'}",
    '[A&B]':"{'.n0': 'A&B'}",
    '[A|B]':"{'.n0': 'A|B'}",
    '[A&&B]':"{'.n0': 'A&&B'}",
    '[A||B]':"{'.n0': 'A||B'}",

    # conflict with < separator/operator
    '<A>-><B>':"{'.n1': 'B', '.n0': 'A'}",
    '<A><-<B>':"{'.n1': 'B', '.n0': 'A'}",
    'A<-<B>':"{'A': 'A', '.n0': 'B'}",
    'A <-    <B>':"{'A': 'A', '.n0': 'B'}",

    # conflict delimiters
    'B[lab(elB] A(labelA)->B':"{'A': 'labelA', 'B': 'lab(elB'}",
    # escape delimiters
    'A(A\)A)':"{'A': 'A)A'}",
    'A(A\(A)':"{'A': 'A(A'}",
    'A[A\]A]':"{'A': 'A]A'}",
    'A[A\[A]':"{'A': 'A[A'}",
    'A<A\>A>':"{'A': 'A>A'}",
    'A<A\<A>':"{'A': 'A<A'}",
    # various test cases found
    '[A\'A]->A':"{'A': 'A', '.n0': \"A'A\"}",
    # non ascii characters
    #'A[˘]':"{'A': '˘'}",
    #'A[éçè]':"{'A': 'éçè'}",
    }

set_connectors = {
    # anywhere
    '{A B}>C':"[('C', 'A:B')]",
    '{  A  B }  >   C':"[('C', 'A:B')]",
    '{[A A] [B B]}>[C C]':"[('.n2', '.n0:.n1')]",
    '{A B}>X {C D}>X E->X':"[('X', 'E'), ('X', 'A:B'), ('X', 'C:D')]",
    # delimiters
    'A->B':"[('B', 'A')]",
    '[A]->[B]':"[('.n1', '.n0')]",
    'B[lab\(elB] A(labelA)->B':"[('B', 'A')]",
    # two ways
    'A->B':"[('A', 'B')]",
    'B<-A':"[('B', 'A')]",
    # self reference
    'A->A':"[]",
    'A->A["A"]':"[]",
    'A:G->A':"[]",
    '[AA]->[AA]:G':"[]", 
    'A[AA]->B[AA]':"[('B', 'A')]",
    # spaces
    'A->B':"[('B', 'A')]",
    ' A ->B':"[('B', 'A')]",
    'A-> B ':"[('B', 'A')]",
    ' B <- A ':"[('B', 'A')]",
    # several cases
    'AA->BB':"[('BB', 'AA')]",
    'AA->BB:G':"[('BB', 'AA')]",
    'AA:G->BB:G':"[('BB', 'AA')]",
    'AA:G->BB':"[('BB', 'AA')]",
    'AA->BB[BB BB]':"[('BB', 'AA')]",
    'AA->BB[BB BB]:G':"[('BB', 'AA')]",
    'AA:G->BB[BB BB]:G':"[('BB', 'AA')]",
    'AA:G->BB[BB BB]':"[('BB', 'AA')]",
    'AA->[BB BB]':"[('.n0', 'AA')]",
    'AA->[BB BB]:G':"[('.n0', 'AA')]",
    'AA:G->[BB BB]:G':"[('.n0', 'AA')]",
    'AA:G->[BB BB]':"[('.n0', 'AA')]",
    'AA[AA AA]->BB':"[('BB', 'AA')]",
    'AA[AA AA]->BB:G':"[('BB', 'AA')]",
    'AA[AA AA]:G->BB:G':"[('BB', 'AA')]",
    'AA[AA AA]:G->BB':"[('BB', 'AA')]",
    'AA[AA AA]->BB[BB BB]':"[('BB', 'AA')]",
    'AA[AA AA]->BB[BB BB]:G':"[('BB', 'AA')]",
    'AA[AA AA]:G->BB[BB BB]:G':"[('BB', 'AA')]",
    'AA[AA AA]:G->BB[BB BB]':"[('BB', 'AA')]",
    'AA[AA AA]->[BB BB]':"[('.n0', 'AA')]",
    'AA[AA AA]->[BB BB]:G':"[('.n0', 'AA')]",
    'AA[AA AA]:G->[BB BB]:G':"[('.n0', 'AA')]",
    'AA[AA AA]:G->[BB BB]':"[('.n0', 'AA')]",
    
    '[AA AA]->BB':"[('BB', '.n0')]",
    '[AA AA]->BB:G':"[('BB', '.n0')]",
    '[AA AA]:G->BB:G':"[('BB', '.n0')]",
    '[AA AA]:G->BB':"[('BB', '.n0')]",
    '[AA AA]->BB[BB BB]':"[('BB', '.n0')]",
    '[AA AA]->BB[BB BB]:G':"[('BB', '.n0')]",
    '[AA AA]:G->BB[BB BB]:G':"[('BB', '.n0')]",
    '[AA AA]:G->BB[BB BB]':"[('BB', '.n0')]",
    '[AA AA]->[BB BB]':"[('.n1', '.n0')]",
    '[AA AA]->[BB BB]:G':"[('.n1', '.n0')]",
    '[AA AA]:G->[BB BB]:G':"[('.n1', '.n0')]",
    '[AA AA]:G->[BB BB]':"[('.n1', '.n0')]",
    
    '<AA AA>-><BB BB>':"[('.n1', '.n0')]",
    '(AA AA)->(BB BB)':"[('.n1', '.n0')]",
    '"AA AA"->"BB BB"':"[('.n1', '.n0')]",    
    # with child
    '[A]@Ct58LPl_dd->B@RysHufzywk':"[('B', '.n0')]",
    '[A]:G@Ct58LPl_dd->B:G@RysHufzywk':"[('B', '.n0')]",
    # OR Operator
    'A->B A->C':"[('B', 'A'), ('C', 'A')]",
    'B->A C->A':"[('A', 'B'), ('A', 'C')]",
    # various test cases found
    '[A\'A]->A':"[('A', '.n0')]",
    # Connextion with quantificators (to review)
    'A-B':"[('A', 'B', '-')]",
    # Connextion with quantificators (to review)
    'A-!-B':"[('A', 'B', 'conflict')]",
    # error
    'A--B':"[]",
    # error
    'A---B':"[]",
    # error
    '{A B}>-C':"[]",
    }

set_type = {
    # anywhere
    'A:G':"{'A': 'GOAL'}",
    '[A]:G':"{'.n0': 'GOAL'}",
    'A:G@RysHufzywk':"{'A': 'GOAL'}",
    '[A]:G@RysHufzywk':"{'.n0': 'GOAL'}",
    # full type names
    'A:Goal':"{'A': 'GOAL'}",
    'A:GOAl':"{'A': 'GOAL'}",
    # Unknown type 
    'A:mytype':"{}",
    # implicit types
    'A':"{}",
    '[A A]':"{'.n0': 'REQUIREMENT'}",
    '(A A)':"{'.n0': 'GOAL'}",
    '"A A"':"{}",
    '<A A>':"{'.n0': 'AGENT'}",
    # priority
    '<A A>:G':"{'.n0': 'GOAL'}",
    # all types
    'A:G':"{'A': 'GOAL'}",
    'A:O':"{'A': 'OPERATION'}",
    'A:B':"{'A': 'OBSTACLE'}",
    'A:R':"{'A': 'REQUIREMENT'}",
    'A:A':"{'A': 'AGENT'}",
    }

#### TEMPORARY SETS

set1 = {
    'A->B':"[('B', 'A')]",
    ' A ->B':"[('B', 'A')]",
    'A-> B ':"[('B', 'A')]",
    ' B <- A ':"[('B', 'A')]",
    'A->B A->C':"[('B', 'A'), ('C', 'A')]",
    'B->A C->A':"[('A', 'B'), ('A', 'C')]",
    'A-!-B':"[('A', 'B', 'conflict')]",
    'A--B':"[]",
    'A---B':"[]",
    }

set2 = {
    'AA:G':"{'AA': 'AA'}",
    #'A[label]':"{'A': 'label'}",
    'A B':"{'A': 'A', 'B': 'B'}",
    'A':"{'A': 'A'}",
    }
##### TEST GLUE #####

def utest(h,cpt):
    n,ok=0,0
    o = 'test_%s:'%cpt
    for i in h.keys():
        item = ui.cg(i)
        n+=1
        if item.get(cpt) != h[i]:
            ok += 1
            o += 'Item %d on |%s| Computed:%s|Expected:%s|\n'%(n, i, item.get(cpt),h[i])
    o += ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    o += '\n'
    return n,o

def test_json_connectors(req):
    req.content_type = 'application/json'
    return '%s'%set2

def run_server(req=None):
    if req:
        req.content_type = 'text/plain'
    n,o = 0,''
    n1,o1 = utest(set_node,'node')
    n2,o2 = utest(set_type,'type')
    #...
    o += o1 + o2
    o += '%s tests cases\n'%(n1+n2)
    if req:
        o += 'Git Commit: ' + ui.sha1_pkg(req)
    return o 

def clean(req):
    from subprocess import Popen, PIPE
    req.content_type = 'text/plain'
    Popen(['rm', '-f', '/tmp/cg/stack.db'],stdout=PIPE).communicate()
    return 'ok'

def get_env(r):
    """ """
    import os
    r.add_common_vars()
    env = r.subprocess_env.copy()
    ip = env['REMOTE_ADDR'] if env.has_key('REMOTE_ADDR') else '0.0.0.0'
    dname = os.path.dirname(env['SCRIPT_FILENAME'])
    bname = os.path.basename(env['SCRIPT_FILENAME'])
    return (dname,bname[:-3],ip)

def update_tool(req):
    """ update the tool from github """
    import datetime,time,dbhash,re
    from subprocess import Popen, PIPE
    (pwd, name,ip) = get_env(req)
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
    req.content_type = 'text/plain'  
    if not allow:
        return 'Error: Time since last update is %d secondes; should be greater than 2 minutes!'%int(delta)
    cmd = 'cd %s/..; rm -rf ConnectedGraph; git clone git://github.com/pelinquin/ConnectedGraph.git; cd ConnectedGraph; git submodule update --init'%pwd
    out,err = Popen((cmd), shell=True,stdout=PIPE, stderr=PIPE).communicate()
    o = 'Application Updating from %s commit...\n'%(ui.sha1_pkg(req))
    if err:
        o += 'Error:%s\n'%err
    else:
        o += 'Message:%s\nUpdate OK\n'%out
    return o 

def index(req):
    """ main test page """
    req.content_type = 'application/xhtml+xml'
    o = '<?xml version="1.0" encoding="UTF-8"?>\n'
    o += '<?xml-stylesheet href="%s" type="text/css"?>\n'%ui.__CSS__
    o += '<svg %s editable="yes" test="yes">\n'%ui._SVGNS
    o += '<title id=".title">Test</title>'
    o += '<link %s rel="shortcut icon" href="logo16.png"/>\n'%ui._XHTMLNS
    o += ui.include_ace('.')
    o += '<script %s type="text/ecmascript" xlink:href="xregexp-min.js"></script>\n'%ui._XLINKNS
    o += '<script %s type="text/ecmascript" xlink:href="%s"></script>\n'%(ui._XLINKNS,ui.__JS__)
    o += '<script %s type="text/ecmascript" xlink:href="test_client.js"></script>\n'%ui._XLINKNS
    o += '<foreignObject display="none" width="100%%" height="100%%"><div %s id=".editor" class="editor"></div></foreignObject>'%ui._XHTMLNS
    mygraph = ui.cg('')
    o += mygraph.draw() + ui.menu() + ui.gui_elements() + ui.menubar(req,'reload')
    o += '<g onclick="run_tests();"><rect x="160" width="70" height="18" fill="red" class="button"/><text y="12" x="166" class="button" fill="white">Run tests</text></g><g transform="translate(5,20)"><text id=".results" stroke-width="0"/></g>'
    o += '<g onclick="update_tool();"><rect x="245" width="80" height="18" fill="red" class="button"/><text y="12" x="251" class="button" fill="white">Update tool</text></g>'
    return o + '</svg>'

if __name__ == '__main__':
    print run_server()
    
    
   
