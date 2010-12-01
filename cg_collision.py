#!/usr/bin/python
# -*- coding: latin-1 -*-
"""
find SHA1 collisions on integers
find the highest collision function of of range and size
"""
import os,re
import urllib
import dbhash
import hashlib,base64

__version__  = '0.1'
__BASE__ = '/tmp'

##### RESULTS ######
#size 6 Collision:   529116 (MkS9pK)   [4:10] <- BEST size 6
#size 7 collision:  4596223 (ltCAxXc)  [0:7]  <- BEST size 7
#size 7 collision:  2603729 (MlkbhG7)  [1:8]
#size 7 collision:  1307407 (k5vpUL6)  [2:9]
#size 7 collision:  2919342 (Zgso-GW)  [3:10]
#size 7 collision:  2506338 (7zAz0m-)  [4:11]
#size 7 collision:  3829096 (frlhVtF)  [5:12]
#size 7 collision:  2430902 (fzxAMyq)  [6:13]
#size 7 collision:  3356971 (LZmDLF-)  [7:14]
#size 7 collision:  1122510 (J6rM2On)  [8:15]
#size 7 collision:  1208610 (lpk16NZ)  [9:16]
#size 7 collision:  2129906 (jCBXLOE)  [10:17]
#size 7 collision:  2163364 (H8gF0ga)  [11:18]
#size 7 collision:  3716090 (N7TQXvm)  [12:19]
#size 7 collision:  1362869 (bgCZdsL)  [13:20]
#size 7 collision:  1827589 (ln0Udmt)  [14:21]
#size 7 collision:  3076511 (UjFyyeP)  [15:22]
#size 7 collision:  1427979 (clDZjA-)  [16:23]
#size 7 collision:  2842575 (z2krPfp)  [17:24]
#size 7 collision:  3319709 (GebBSej)  [18:25]
#size 7 collision:  2412781 (LDDPq2b)  [19:26]
#size 7 collision:  2952456 (2O-RyiI)  [20:27]
#size 8 collision: 19926426 (DnFsMR1a) [0:8] 
#size 8 collision: 18649453 (A10TcwCw) [1:9]
#size 8 collision:  3824006 (-JNFix0c) [2:10]
#size 8 collision: 28584323 (PuU5NcQO) [3:11] 
#size 8 collision: 24454781 (KsgAEbcP) [4:12]
#size 8 collision: 15401297 (vEGmx31x) [5:13]
#size 8 not found in range > 39999999  [6:14] <- BEST size 8 ?
#size 8 collision: 10669943 (tRqKk0bW) [7:15]
#size 8 collision: 20721103 (fvUChW2r) [8:16]
#size 8 collision:  4416271 (kZB1HfuU) [9:17]
#size 8 collision: 27767172 (3jqs_UPU) [10:18]
#size 8 collision: 23689860 (wEP8EhGa) [11:19]
#size 8 collision:  8961398 (vf2Dv6UN) [13:21]
#size 8 collision: 23341633 (VL02VtPi) [14:22]
#size 8 collision: 24956234 (IqpJXDXm) [15:23]
#size 8 not found in range >(39999999) [16:24] <- BEST size 8 ?
#size 8 collision: 35682669 (dfy8yD3c) [17:25]
#size 8 collision: 16937134 (o_0ZD1uq) [18:26]
#size 8 collision:  5459315 (cxfnoGIo) [19:27]

def test_db(l,start,stop,disp):
    seen = dbhash.open('/tmp/collision.db','n')
    rate = 10000L
    for i in range(l):
        key = '%d'%(long(i)) 
        val = base64.urlsafe_b64encode(hashlib.sha1(key).digest())[start:stop-28]
        if seen.has_key(val):
            seen.close() 
            return '#size %d collision: %s (%s) [%s:%s]'%(stop-start, i,val,start,stop)
        else:
            seen[val] = None
        if disp:
            if i%rate == 0:
                print (i,val)
    seen.close() 
    return '#size %s not found in range(%s) [%s:%s]'%(stop-start,l,start,stop)

if __name__ == '__main__':
    print test_db(49999999L,16,24,False)
    print test_db(49999999L,6,14,False)
    #for i in range(13,18):
    #    print test_db(39999999L,i,i+8,False)
    #for i in range(15,19):
    #    print test_db(39999999L,i,i+8,False)

