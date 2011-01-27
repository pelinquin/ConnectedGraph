#!/usr/bin/python
"""
Controlling Cars on a Bridge 

USAGE
 NO OPTION
 \tRun simulation
 -h --help
 \tDisplay this help


This is a simple case study for FORMOSE

see http://deploy-eprints.ecs.soton.ac.uk/112/

and chapter 2 of the book...

REQUIREMENTS:
FUN1 The system is controlling cars on a bridge between the mainland and an island 
FUN2 The number of cars on the bridge and the island is limited
FUN3 The bridge is one way or the other, not both at the same time

EQP1 The system has two traffic lights with two colors: green and red
EQP2 The traffic lights control the entrance to the bridge at both ends of it
EQP3 Cars are not supposed to pass on a red traffic light, only on a green one
EQP4 The system is equipped with four car sensors each with two states: on or off
EQP5 The sensors are used to detect the presence of cars entering or leaving the bridge

Added requirements:
FUN6 The controler policy shall not set both red lights more time than needed
(It exist one time when traffic lights become green)
FUN7 The controler policy shall minimize the total waiting time on traffic light
(Also minimize the average/dispersion of the waiting time)

(FUN8) At reset, the number of cars on the bridge and on the island has to be set manually if not null.

ROB1 if cars are created/destroyed on bridge/island, the system shall work with an error on the total car number.

NOT NEEDED! FUN4 Once started, the system should work for ever 
NOT NEEDED! FUN5 The controller must be fast enough so as to be able to treat all the information coming from the environment

Remarks on first study:
* ml_pass and il_pass variable not needed !
* why cloning variables a -> A, b->B IL_IN_SR -> il_in_10 if seen from controler/env ?
* -> introducing complexity
* 253 proofs for such a simple example !!
* refinement should also be on the controler policy (basic -> adptative -> optimal)

mi: Mainland Input sensor
mo: Mainland Output sensor
ii: Island   Input sensor
io: Island   Output sensor
tli:Island   Traffic Lights
tlm:Mainland Traffic Lights

"""
__version__  = '0.1'

def boolrd():
    """ return random choice False or True """
    import random
    return random.choice((False,True))

def environment(tli,tlm,S):
    """
    Env can see the S State vector, but do not write it !
    """
    assert S[0] >= 0 and S[1] >= 0 and S[2] >= 0 # ROB1
    assert S[0] == 0 or S[2] == 0 # FUN3
    assert S[0] + S[1] + S[2] <= 10   # FUN2
    assert tli == red or tlm == red # part of FUN3
    # we use a simple 50% random choice for presence or not of a vehicule on a sensor;
    # this is a high simplification
    # A more realistic model would estimate some car line;
    # cars are close each other in the line before traffic light, but far each other if traffic light is green for a long time.
    # A traffic simulation may be needed
    # no need to optimize this code; can even use a database with some experimental data
    mo = boolrd()
    ii = boolrd() if S[0]>0 else False
    io = boolrd() if S[1]>0 else False
    mi = boolrd() if S[2]>0 else False
    return mi,mo,ii,io

def update_state(S,mi,mo,ii,io,tli,tlm):
    """
    This is part of the controler
    """
    if mo and tlm == green:
        S[0] += 1; S[5] += S[3]; S[3] = 0
    else:
        S[3] += 1
    if ii:
        S[0] -= 1; S[1] += 1
    if io and tli == green:
        S[1] -= 1; S[2] += 1; S[5] += S[4]; S[4] = 0
    else:
        S[4] += 1
    if mi:
        S[2] -= 1

def controler(policy,mi,mo,ii,io,S):
    """
    FUN1
    Controler is updating its own S state vector (ie simple environment model)
    It seems that the optimal policy may depend on the bridge length (time to cross the bridge), the duration distribution of parking time on the Island.
    Also the sensitive cost for waiting is not exactly proportional to waiting time
    waiting time is here the duration when a car (sensor on) stay at red traffic light, we do not count waiting time for car after the second position on the line.
    Maybe a tradeoff is to found between the performance and the environment model accuracy in the controler memory.
    Should the environment model be accurate to achieve a better performance or is it better to build a pessimistic model.
    For adaptive policies, how to mesure performance ?
    """
    MAX_NB_CARS = 10
    if policy == basic: # Basic policy (not optimal) ! #FUN6
        tli,tlm = green,green
    elif policy == rand: # Random policy (not optimal)
        tli,tlm = boolrd(),boolrd()
    else:
        # Put here an optimal policy that minimise waiting time metrics
        # I do not know if such policy is better than the basic one !
        if S[3] > 15 and S[2] > 0 and controler.oldtli == green:
            tli,tlm = red,green
        elif S[4] > 15 and S[0] > 0 and controler.oldtlm == red:
            tli,tlm = green,red
        else:
            tli,tlm = green,green
    # Only Five constraints
    # 3 // constraints:
    if S[0]+S[1]+S[2] >= MAX_NB_CARS-1: # FUN2
        tlm = red
    if S[0] > 0:
        tli = red
    if S[2] > 0:
        tlm = red
    # FUN3
    # 2 linked constraints; sort is important since car are coming from the Mainland
    # There is no car manufacture on the Island !
    if tlm == green:
        tli = red
    if tli == green:
        tlm = red
    controler.oldtli,controler.oldtlm = tli,tlm
    update_state(S,mi,mo,ii,io,tli,tlm)
    return tli,tlm
controler.oldtli = 0
controler.oldtlm = 0

def print_state(S):
    """
    S[0]: Number of cars on the bridge going from Mainland to Island
    S[1]: Number of cars on the Island
    S[2]: Number of cars on the bridge going from Island to Mandland
    S[3]: Current Waiting time on Mainland traffic lights
    S[4]: Current Waiting time on Island traffic lights
    S[5]: Cumulative Waiting time on traffic lights
    """
    w = '<-' if tli else '->' if tlm else '--'
    dtli = 'green' if tli == green else 'red'
    dtlm = 'green' if tlm == green else 'red'
    print '%03d%s(MI:%5s,MO:%5s,II:%5s,IO:%5s) I:%5s,M:%5s %s'%(t,w,mi,mo,ii,io,dtli,dtlm,S)

def install(req,upid='',pw=''):
    """ Update On The Web ! """
    import os,hashlib,zipfile
    req.content_type = 'text/html'
    out = '<html><p>%s</p>'%__version__
    req.add_common_vars()
    env = req.subprocess_env.copy()
    sf = env['SCRIPT_FILENAME']
    bb = sf[:-3]
    nn = os.path.basename(sf)[:-3]
    dd = os.path.dirname(sf)
    #li = ['%s.py'%nn,'%s.js'%nn,'%s.css'%nn]
    li = ['%s.py'%nn,]
    f = zipfile.ZipFile('%s.zip'%bb, 'w')
    for item in li:
        f.write('%s/%s'%(dd,item),item, zipfile.ZIP_DEFLATED)
    f.close()
    if upid:
        if pw and hashlib.sha1(pw).hexdigest() == '96b0ac8aace54854cec8325fce9394f295703014':
            prg = open('%s/tmp.zip'%dd,'w')
            prg.write(upid.value)
            prg.close()
            zf = zipfile.ZipFile('%s/tmp.zip'%dd)
            for item in li:
                p1 = open('%s/%s'%(dd,item),'w')
                p1.write(zf.read(item))
                p1.close()
            out += 'Update OK (%d bytes)'%len(upid.value)
        else:
            out += 'Wrong Password!'
    else:
        out += '<form method="post" action="install" enctype="multipart/form-data"><input type="file" name="upid"><input type="submit"><input type="password" name="pw"></form>'
    return out + '</html>' 

def index(req):
    """ On The Web """
    import os,sys,pydoc
    req.content_type = 'text/html'
    req.add_common_vars()
    env = req.subprocess_env.copy()
    dname = os.path.dirname(env['SCRIPT_FILENAME'])
    #sys.path.append(os.path.dirname(__file__))
    doc = pydoc.HTMLDoc()
    module = __import__('cg')
    res = doc.docmodule(module)
    return '<html>%s</html>'%res

if __name__ == '__main__':
    """
    Run this script
    """
    import os,sys,getopt
    opts, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
    run = True
    for r in opts:
        if r[0] in ('-h','--help'):
            run = False
            help(os.path.basename(sys.argv[0])[:-3])
    (green, red) = range(2)
    (basic,rand,optimal1,optimal2,odapt1) = range(5)
    if run:
        duration = 10000
        S = [0,0,0,0,0,0] # manual setting if cars on bridge or on island at init
        mi,mo,ii,io,tlm,tli = False,False,False,False,False,False
        for t in range(duration):
            tli,tlm = controler(basic,mi,mo,ii,io,S)
            mi,mo,ii,io = environment(tli,tlm,S)
            print_state(S)
        print 'Average waiting time:%d'%(100*int(S[5])/t)


