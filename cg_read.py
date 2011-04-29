#!/usr/bin/python
# -*- coding: latin-1 -*-
#-----------------------------------------------------------------------------
# $Id: read_bb.py 14 2009-03-25 15:30:17Z laurent $
# @(#) read DBM database
# $Name:  $
#-----------------------------------------------------------------------------

import string,sys,os,dbhash

def print_db(db):
    """
    """
    d = dbhash.open(db, 'r')
    for item in d.keys():
        print '[%s] %s -> %s' % (db,item,d[item])
    d.close()


if __name__ == '__main__':
    """

    """
    for arg in sys.argv[1:]:
        print_db(arg)


# end #
