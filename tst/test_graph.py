#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys,re,dbhash,base64,hashlib,datetime
import xml.sax.saxutils, urllib
import svgapp, graph

_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml"'
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink"'

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

def my_app(environ,start_response):
    """ app """
    start_response('200 OK',[])
    return []

def utest(h,cpt):
    n,ok=0,0
    o = 'test_%s:'%cpt
    for i in h.keys():
        item = graph.cg(i)
        n+=1
        if item.get(cpt) != h[i]:
            ok += 1
            o += 'Item %d on |%s| Computed:%s|Expected:%s|\n'%(n, i, item.get(cpt),h[i])
    o += ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    o += '\n'
    return n,o

def add_entry(msg,ok=True):
    o = '<tspan x="0" dy="18" '
    o += 'fill="green"' if ok else 'fill="red"'
    return o + '>%s</tspan>'%msg

class test:
    """ """
    def __init__(self,app):
        self.app = app

    def __call__(self,environ, start_response):
        json_mode = environ['PATH_INFO'] == '/json'
        if json_mode:
            start_response('200 OK',[])
            return [test_json_connectors()]
        environ['test.data'] = 'OK'
        n1,o1 = utest(set_node,'node')
        n2,o2 = utest(set_type,'type')
        def custom_start_response(status, header):
            return start_response(status, header)
        response_iter = self.app(environ, custom_start_response)
        o = '<script %s type="text/ecmascript" xlink:href="/js/tst/test_graph.js"/>\n'%_XLINKNS 
        o += '<g transform="translate(5,20)"><text id=".results" stroke-width="0">'
        o += add_entry(o1)
        o += add_entry(o2)
        o += '</text></g>'
        a = ''
        response_string = o + ''.join(response_iter) + a 
        return [response_string]

set2 = {
    'AA:G':"{'AA': 'AA'}",
    #'A[label]':"{'A': 'label'}",
    'A B':"{'A': 'A', 'B': 'B'}",
    'A':"{'A': 'A'}",
    }

def test_json_connectors():
    return '%s'%set2


application = svgapp.svg_app(graph.graph(test(my_app)))

if __name__ == '__main__':
    print 'test'


