#!/usr/bin/python
# -*- coding: utf-8 -*-
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
 USAGE: test file for the cg.py script
 test cases are stored in dictionaries where:
  - the key is the input string
  - the value is the expected result
"""

import cg
set_syntax = {
    'A@RysH':'syntax error', # REVOIR
    }

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

set_child = {
    # anywhere
    'A@RysHufzywk':"{'A': 'RysHufzywk'}",
    'A[AA] A:G@RysHufzywk':"{'A': 'RysHufzywk'}",
    'A@RysHufzywk A[AA]':"{'A': 'RysHufzywk'}",
    'A@RysHufzywk:G':"{'A': 'RysHufzywk'}",
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

set_node_update = {
    ('A->B','NEW','A'):'A"NEW"->B',
    ('A->B','NEW','B'):'A->B"NEW"',
    ('A B','NEW','A'):'A"NEW" B',
    ('A B A','NEW','A'):'A"NEW" B A',
    ('A#com\nB','NEW','A'):'A"NEW"#com\nB',
    ('A[OLD] B','NEW','A'):'A[NEW] B',
    ('[OLD]','NEW','.n0'):'[NEW]',
    ('A[OLD] B[OLD]','NEW','A'):'A[NEW] B[OLD]',
    ('A[OLD] B[OLD]','NEW','B'):'A[OLD] B[NEW]',
    ('A X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','NEW','A'):'A"NEW" X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A',
    ('A X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','NEW','B'):'A X@_l27z-XOfimIuMabz9_e B"NEW":G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A',
    ('A X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','NEW','C'):'A X@_l27z-XOfimIuMabz9_e B:G C[NEW]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A',
    ('A X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','NEW','D'):'A X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[NEW]:G # [E E] I\n [E E] # A \n[F F]:R A',
    ('A X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','NEW','.n0'):'A X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[D D]:G # [E E] I\n [NEW] # A \n[F F]:R A',
    ('A X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','NEW','.n1'):'A X@_l27z-XOfimIuMabz9_e B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[NEW]:R A',        
    }

set_node_adress = {
    ('A->B','A','A'):'LAYOUT\nA@ZZZZZZZZZZ->B',
    ('A X@fimIuMabz9 B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','A'):'LAYOUT\nA@ZZZZZZZZZZ X@fimIuMabz9 B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A',
    ('A X@fimIuMabz9 B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','B'):'LAYOUT\nA X@fimIuMabz9 B:G@ZZZZZZZZZZ C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A',
    ('A X@fimIuMabz9 B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','C'):'LAYOUT\nA X@fimIuMabz9 B:G C[C C]@ZZZZZZZZZZ\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A',
    ('A X@fimIuMabz9 B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','D'):'LAYOUT\nA X@fimIuMabz9 B:G C[C C]\n D[D D]:G@ZZZZZZZZZZ # [E E] I\n [E E] # A \n[F F]:R A',
    ('A X@fimIuMabz9 B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','.n0'):'LAYOUT\nA X@fimIuMabz9 B:G C[C C]\n D[D D]:G # [E E] I\n [E E]@ZZZZZZZZZZ # A \n[F F]:R A',
    ('A X@fimIuMabz9 B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R A','.n1'):'LAYOUT\nA X@fimIuMabz9 B:G C[C C]\n D[D D]:G # [E E] I\n [E E] # A \n[F F]:R@ZZZZZZZZZZ A',
    ('[how]','.n0','how'):'LAYOUT\n[how]@ZZZZZZZZZZ',
    ('[B?]','.n0','B?'):'LAYOUT\n[B?]@ZZZZZZZZZZ',
    }
    
def test_syntax():
    n,ok=0,0
    for i in set_syntax.keys():
        item = cg.cg(i)
        n+=1
        value = item.check(i)
        if value != set_syntax[i]:
            ok += 1
            print 'Item %d %s Computed:%s|Expected:%s|'%(n, i, value,set_syntax[i])
    print ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    return n

def test_node():
    n,ok=0,0
    for i in set_node.keys():
        item = cg.cg(i)
        n+=1
        if item.get_node() != set_node[i]:
            ok += 1
            print 'Item %d %s Computed:%s|Expected:%s|'%(n, i, item.get_node(),set_node[i])
    print ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    return n

def test_link():
    n,ok=0,0
    for i in set_link.keys():
        item = cg.cg(i)
        n+=1
        if item.get_link() != set_link[i]:
            ok += 1 
            print 'Item %d %s Computed:%s|Expected:%s|'%(n, i, item.get_link(),set_link[i])
    print ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    return n

def test_child():
    n,ok=0,0
    for i in set_child.keys():
        item = cg.cg(i)
        n+=1
        if item.get_child() != set_child[i]:
            ok += 1 
            print 'Item %d %s Computed:%s|Expected:%s|'%(n, i, item.get_child(),set_child[i])
    print ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    return n

def test_type():
    n,ok=0,0
    for i in set_type.keys():
        item = cg.cg(i)
        n+=1
        if item.get_type() != set_type[i]:
            ok += 1 
            print 'Item %d %s Computed:%s|Expected:%s|'%(n, i, item.get_type(),set_type[i])
    print ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    return n

def test_connectors():
    n,ok=0,0
    for i in set_connectors.keys():
        item = cg.cg(i)
        n+=1
        if item.get_connectors() != set_connectors[i]:
            ok += 1 
            print 'Item %d %s Computed:%s|Expected:%s|'%(n, i, item.get_connectors(),set_connectors[i])
    print ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    return n

def test_update_child_label():
    n,ok=0,0
    for i in set_node_update.keys():
        n+=1
        new_raw = cg.update_child_label(i[0],i[1],i[2])
        if new_raw != set_node_update[i]:
            ok += 1
            print 'Item %d\n%s\nComputed\n%s\nExpected\n%s'%(n, i, new_raw,set_node_update[i])
    print ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    return n

def test_update_child_adress():
    n,ok=0,0
    for i in set_node_adress.keys():
        n+=1
        new_raw = cg.update_child('LAYOUT\n'+i[0],'ZZZZZZZZZZ',i[1])
        if new_raw != set_node_adress[i]:
            ok += 1
            print 'Item %d\n%s\nComputed\n%s\nExpected\n%s'%(n, i, new_raw,set_node_adress[i])
    print ('Test OK (%d cases)'%n if ok==0 else 'Test KO on %d tests'%ok)
    return n

def test_breakline():
    """ Test"""
    for i in range(10):
        for l in range(20):
            x = ''
            for j in range(l+1):
                for k in range(i+1):
                    x += 'Z'
                x += ' '
            return cg.cutline_0(x[:-1])

def test5():
    x = 'A[Mastering complex systems]\
    B[Enhance requirements engineering methods] B->A\
    C[Methods evolutivity] C->B\
    D[Extended enterprise] D->B\
    E[User-friendliness] E->B\
    F[Take into account certain NFRs] F->B\
    G[Enhance architectural design methods] G->A\
    H[Take zigzags into account (?)] H->G H->B\
    FLOSS->C\
    Extendability->C\
    K[Collaboration support] K->D K->E\
    L[Viewpoint-based language] L->E L->F\
    [Requirements evolution]->B\
    [Validate requirements as early as possible]->B\
    [Safe method]->B'
    #x = 'A B A->B'
    x = 'A B C D A->B C->D A->C B->D'
    mygraph = cg.cg(x,{})
    mygraph.layout(10,100)
    mygraph = cg.cg(x,{})
    print 'k=%s'%mygraph.get_k()
    for i in range (2,2):
        n,sum = 0,0
        for j in range(10):
            n+=1
            mygraph = cg(x,{})
            sum += mygraph.layout(i,40)
        print '%s %s'%(i,sum/n)        
    

def check(raw):
    """ """
    raw = re.sub(r'#[^\n]*\n','',raw)
    #raw = re.sub(r'\\[\(\[<"\]\)>"]','',raw)
    #reg_nodes = re.compile(r'\\[\(\[<"\]\)>"]')
    reg_nodes = re.compile(r'(\[)')
    for m in reg_nodes.finditer(raw):
        print m.start()
    return raw

if __name__ == '__main__':
    n = 0
    #test_syntax()
    n += test_node()
    #n += test_link()
    n += test_type()
    n += test_child()
    n += test_connectors()
    n += test_update_child_label()
    n += test_update_child_adress()
    print '%s tests cases'%n
    #test_breakline()
    
    
   
