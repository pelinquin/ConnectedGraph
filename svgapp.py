#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,re,dbhash,base64,hashlib,Cookie
import time,datetime

_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml"'
_SVGNS    = 'xmlns="http://www.w3.org/2000/svg"'
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink"'

def get_ip(environ):
    """ get client ip address """
    ip = environ['REMOTE_ADDR'] if environ.has_key('REMOTE_ADDR') else '0.0.0.0'
    return ip

def get_user(environ):
    """ """
    login,logout,pw,pw2 = '','','',''
    if environ.has_key('CONTENT_TYPE'):
        if not re.match(r'^multipart',environ['CONTENT_TYPE']):
            args = environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH',0)))
            for i in args.split('&'):
                l = i.split('=')
                if l[0] == 'login':
                    login = l[1]
                elif l[0] == 'pw':
                    pw = l[1]
                elif l[0] == 'pw2':
                    pw2 = l[1]
                elif l[0] == 'logout':
                    logout = l[1]
    user,msg,sid,hpw = '','','',''
    if logout:
        user = ''
        
        if login and pw and pw2:
            if change_pw_user(login,pw,pw2):
                user,msg = login,'Hi!:%s, your password is changed!'%login
            else:
                msg = 'Error:New password not different or new password too much simple'
    if login and not logout:
        """ Add button to change password"""
        if pw2:
            if register_user(login,pw,pw2,get_ip(environ)):
                user,msg = login,'Hi!:%s, your account is well created!'%login
            else:
                msg = 'Error:Login already used or login too long (20) or more than 10 logins/ip or difference in repeated password or password too much simple!'
        else:
            if check_user(login,pw):
                user,msg = login,'Hi!:%s, welcome!'%login
            else:
                msg = 'Error:Bad login or password!'
    f = '/tmp/pw.db'
    if user:
        s = dbhash.open(f,'c')
        sid = hashlib.sha1(os.urandom(10)).hexdigest()
        # find a way to delete old sid !
        dat = '%s'%time.mktime(datetime.datetime.now().timetuple())
        s[sid] = '%s:%s:%s'%(user,get_ip(environ),dat[:-2])
        s.close()   
    elif environ.has_key('HTTP_COOKIE') and not logout:
        co = Cookie.SimpleCookie(environ['HTTP_COOKIE'])  
        if co.has_key('id'):
            sid = co['id'].value
            if os.path.isfile(f):
                s = dbhash.open('/tmp/pw.db')
                if s.has_key(sid):
                    d = s[sid].split(':')
                    if d[1] == get_ip(environ):
                        user = d[0]
                s.close()   
    if environ.has_key('HTTP_COOKIE') and logout:
        co = Cookie.SimpleCookie(environ['HTTP_COOKIE'])  
        if co.has_key('id') and os.path.isfile(f):
            s = dbhash.open('/tmp/pw.db','c')
            del s[co['id'].value]
            s.close()       
    if user and pw:
        hpw = hashlib.sha1('%s_%s'%(user,pw)).hexdigest()
        environ['svgapp.start'] = 'yes' 
    elif environ.has_key('HTTP_COOKIE') and not logout:
        co = Cookie.SimpleCookie(environ['HTTP_COOKIE']) 
        if co.has_key('hpw'):
            hpw = co['hpw'].value
    return user,msg,logout,sid,hpw

def set_cook(user,header,sid,hpw):
    """ """
    if user:
        header.append(('Set-Cookie','id=%s;HttpOnly'%sid))
        if hpw:
            dat = '%s'%time.mktime(datetime.datetime.now().timetuple())
            header.append(('Set-Cookie','hpw=%s'%hpw))
            header.append(('Set-Cookie','dat=%s'%dat[:-2]))
    else:
        header.append(('Set-Cookie','id=; Expires=Thu, 01-Jan-1970 00:00:01 GMT;'))
        header.append(('Set-Cookie','hpw=; Expires=Thu, 01-Jan-1970 00:00:01 GMT;'))
        header.append(('Set-Cookie','dat=; Expires=Thu, 01-Jan-1970 00:00:01 GMT;'))

def js():
    """ javascript glue """
    o = """
if (typeof($)=='undefined') { function $(id) { return document.getElementById(id.replace(/^#/,'')); } }
//window.onunload = function () { alert ('quit!'); };
function signin() { $('.loginpage').setAttribute('display','inline'); }
function create_account(obj) {
  $('pw2').setAttribute('style','display:inline');
  $('pw2').setAttribute('onchange','submit();');
  $('pw').removeAttribute('onchange');
  $('msg').setAttribute('display','inline');
  obj.setAttribute('display','none');
  $('.cp').setAttribute('display','none');
}
function change_pw(obj) {
  $('pw2').setAttribute('style','display:inline');
  $('pw2').setAttribute('onchange','submit();');
  $('pw').removeAttribute('onchange');
  obj.setAttribute('display','none');
  $('.ca').setAttribute('display','none');
  $('pw').setAttribute('title','Old password');
  $('pw2').setAttribute('title','New password');
  $('lout').setAttribute('value','change');
  $('msg').firstChild.nodeValue = 'New password:';
  $('msg').setAttribute('x','102');
  $('msg').setAttribute('y','260');
  $('msg').setAttribute('display','inline');
}
function check() { $('myform').submit(); }
function logout() { $('lout').setAttribute('value','yes'); $('myform').submit(); }
function help() { alert('help');}
"""
    return o

def change_pw_user(login,pw,pw2):
    """ Change password for a registered user"""
    result, base = False, '/tmp/pw.db'
    if login and pw and pw2 and os.path.isfile(base):
        db = dbhash.open(base,'c')
        if db.has_key(login):
            if db[login] == hashlib.sha1(login+pw).hexdigest():
                if (len(pw2) > 4) and (pw2 != pw) and (pw2 != login):
                    db[login],result = hashlib.sha1(login+pw2).hexdigest(),True
        db.close() 
    return result

def register_user(login,pw1,pw2,ip):
    """ Store up to 10 login/pw per ip"""
    import hmac
    result, base = False, '/tmp/pw.db'
    db = dbhash.open(base,'c')
    if not db.has_key(ip):
        db[ip] = '%d'%0
    if login and len(pw1) > 4 and len(login) < 20 :
        if login != pw1:
            if not re.match('^anonymous$',login,re.IGNORECASE):
                if (pw1 == pw2) and login:
                    if int(db[ip]) < 10:
                        if not db.has_key(login):
                            db[login],result = hashlib.sha1(login+pw1).hexdigest(),True
                            #db['_____'+login+'_____'] = hmac.new('AA','BLABLA',hashlib.sha1).hexdigest()
                            db[ip] = '%d'%(int(db[ip]) + 1)
    db.close()    
    return result

def check_user(login,pw):
    """ check if user registered with good password """
    result, base = False, '/tmp/pw.db'
    if login and pw:
        if os.path.isfile(base):
            db = dbhash.open(base)
            if db.has_key(login):
                if db[login] == hashlib.sha1(login+pw).hexdigest():
                    result = True
            db.close()    
    return result

def logo(full=True): 
    """ """
    o = '<!-- Copyright 2010 Stephane Macario -->'
    if full:
        o += '<g onclick="fork();" transform="matrix(0.5,0,0,0.5,120,460)" style="fill:#ffffff;stroke:none">'
    else:
        o += '<g onclick="switch_mode();" transform="matrix(0.2,0,0,0.2,0,166)" style="fill:#ffffff;stroke:none">'
    if full:
        o += '<g style="fill:#231f20;stroke:none"><path d="m 536.70,-701.72 c 0,0 -332.09,0 -332.09,0 0,0 0,-65.40 0,-65.40 0,0 332.09,0 332.09,0 0,0 0,65.40 0,65.40 z"/><path d="m 561.06,-675.65 c 0,0 -330.70,0 -330.70,0 0,0 0,-68.26 0,-68.26 0,0 330.70,0 330.70,0 0,0 0,68.26 0,68.26 z"/></g><path d="m 237.89,-737.15 c 0,0 0,9.74 0,9.74 0,0 15.65,0 15.65,0 0,0 0,6.37 0,6.37 0,0 -15.65,0 -15.65,0 0,0 0,19.25 0,19.25 0,0 -7.88,0 -7.88,0 0,0 0,-41.98 0,-41.98 0,0 29.34,0 29.34,0 0,0 0,6.61 0,6.61 0,0 -21.45,0 -21.45,0 z"/><path d="m 278.83,-723.11 c 0,4.90 0.88,8.69 2.64,11.38 1.76,2.68 4.32,4.03 7.69,4.03 3.95,0 6.96,-1.31 9.04,-3.94 2.07,-2.63 3.11,-6.45 3.11,-11.47 0,-9.82 -3.85,-14.73 -11.55,-14.73 -3.52,0 -6.23,1.33 -8.11,3.99 -1.88,2.66 -2.82,6.24 -2.82,10.74 z m -8.23,0 c 0,-5.96 1.73,-11.02 5.22,-15.15 3.47,-4.13 8.13,-6.19 13.95,-6.19 6.41,0 11.31,1.87 14.70,5.61 3.38,3.73 5.08,8.98 5.08,15.73 0,6.75 -1.77,12.11 -5.31,16.07 -3.54,3.96 -8.56,5.95 -15.08,5.95 -5.98,0 -10.58,-1.96 -13.77,-5.89 -3.19,-3.92 -4.79,-9.30 -4.79,-16.13 z"/><path d="m 331.08,-737.32 c 0,0 0,11.60 0,11.60 1.45,0.11 2.57,0.17 3.34,0.17 3.29,0 5.71,-0.43 7.24,-1.30 1.52,-0.87 2.29,-2.57 2.29,-5.10 0,-2.05 -0.82,-3.48 -2.45,-4.30 -1.63,-0.81 -4.22,-1.22 -7.74,-1.22 -0.85,0 -1.74,0.05 -2.67,0.17 z m 16.93,35.54 c 0,0 -11.91,-17.39 -11.91,-17.39 -1.19,-0.01 -2.86,-0.08 -5.01,-0.19 0,0 0,17.59 0,17.59 0,0 -8.23,0 -8.23,0 0,0 0,-42.01 0,-42.01 0.44,0 2.16,-0.06 5.14,-0.21 2.98,-0.14 5.38,-0.21 7.21,-0.21 11.32,0 16.98,4.12 16.98,12.37 0,2.48 -0.78,4.74 -2.34,6.78 -1.56,2.04 -3.52,3.48 -5.90,4.32 0,0 13.22,18.96 13.22,18.96 0,0 -9.16,0 -9.16,0 z"/><path d="m 408.88,-701.77 c 0,0 -7.65,0 -7.65,0 0,0 -4.69,-22.61 -4.69,-22.61 0,0 -8.98,23.19 -8.98,23.19 0,0 -2.78,0 -2.78,0 0,0 -8.98,-23.19 -8.98,-23.19 0,0 -4.81,22.61 -4.81,22.61 0,0 -7.65,0 -7.65,0 0,0 9.04,-41.98 9.04,-41.98 0,0 4.17,0 4.17,0 0,0 9.62,28.29 9.62,28.29 0,0 9.39,-28.29 9.39,-28.29 0,0 4.17,0 4.17,0 0,0 9.16,41.98 9.16,41.98 z"/><path d="m 426.17,-723.11 c 0,4.90 0.87,8.69 2.64,11.38 1.76,2.68 4.32,4.03 7.69,4.03 3.95,0 6.96,-1.31 9.04,-3.94 2.07,-2.63 3.11,-6.45 3.11,-11.47 0,-9.82 -3.85,-14.73 -11.55,-14.73 -3.52,0 -6.23,1.33 -8.11,3.99 -1.88,2.66 -2.82,6.24 -2.82,10.74 z m -8.23,0 c 0,-5.96 1.73,-11.02 5.22,-15.15 3.48,-4.13 8.13,-6.19 13.95,-6.19 6.41,0 11.31,1.87 14.70,5.61 3.38,3.73 5.08,8.98 5.08,15.73 0,6.75 -1.77,12.11 -5.31,16.07 -3.54,3.96 -8.56,5.95 -15.08,5.95 -5.98,0 -10.57,-1.96 -13.77,-5.89 -3.19,-3.92 -4.79,-9.30 -4.79,-16.13 z"/><path d="m 468.10,-704.12 c 0,0 2.92,-6.69 2.92,-6.69 3.12,2.08 6.20,3.13 9.23,3.13 4.65,0 6.97,-1.52 6.97,-4.57 0,-1.42 -0.54,-2.79 -1.64,-4.08 -1.09,-1.29 -3.35,-2.75 -6.77,-4.35 -3.41,-1.60 -5.71,-2.93 -6.90,-3.97 -1.18,-1.04 -2.10,-2.27 -2.73,-3.71 -0.64,-1.43 -0.95,-3.01 -0.95,-4.75 0,-3.24 1.25,-5.94 3.78,-8.08 2.52,-2.13 5.75,-3.21 9.70,-3.21 5.14,0 8.92,0.91 11.33,2.72 0,0 -2.40,6.43 -2.40,6.43 -2.77,-1.85 -5.70,-2.78 -8.78,-2.78 -1.82,0 -3.23,0.45 -4.24,1.35 -1,0.9 -1.50,2.08 -1.5,3.53 0,2.4 2.83,4.89 8.50,7.48 2.98,1.37 5.14,2.63 6.46,3.79 1.31,1.15 2.32,2.49 3.01,4.03 0.69,1.53 1.03,3.24 1.03,5.13 0,3.39 -1.42,6.18 -4.28,8.37 -2.85,2.19 -6.67,3.28 -11.47,3.28 -4.16,0 -7.92,-1.01 -11.27,-3.04 z"/><path d="m 516.24,-737.15 c 0,0 0,9.74 0,9.74 0,0 14.49,0 14.49,0 0,0 0,6.37 0,6.37 0,0 -14.49,0 -14.49,0 0,0 0,12.64 0,12.64 0,0 20.29,0 20.29,0 0,0 0,6.61 0,6.61 0,0 -28.18,0 -28.18,0 0,0 0,-41.98 0,-41.98 0,0 28.18,0 28.18,0 0,0 0,6.61 0,6.61 0,0 -20.29,0 -20.29,0 z"/>'
    o += '<g transform="translate(-5.8,-492.07)"><path d="m 86.77,-176.29 c 0,0 -1.34,-5.21 -1.34,-5.21 -0.84,0.01 -1.69,0.03 -2.54,0.03 -16.44,-0.14 -32.02,-3.82 -46.07,-10.26 10.86,15.09 26.44,26.58 44.59,32.30 -0.05,-0.18 -0.12,-0.36 -0.17,-0.56 -1.57,-6.07 0.78,-12.28 5.55,-16.29 z" style="fill:url(#.rd1);stroke:none"/></g>'
    o += '<g transform="translate(-5.8,-492.07)"><path d="m 194.97,-241.90 c 0.06,-7.29 -0.78,-14.39 -2.40,-21.18 -12.30,42.46 -48.78,74.56 -93.44,80.57 0,0 0.49,1.90 0.49,1.90 7.36,0.32 13.85,5.02 15.66,12.04 1.18,4.60 0.10,9.27 -2.55,13.00 45.51,-2.58 81.83,-40.09 82.25,-86.34 z" style="fill:url(#.rd2);stroke:none"/></g>'
    o += '<g transform="translate(-5.8,-492.07)"><path d="m 174.53,-298.79 c -1.33,2.19 -3.38,4.04 -6.02,5.16 -5.24,2.22 -11.13,0.93 -14.64,-2.79 0,0 -66.45,27.28 -66.45,27.28 -1.04,4.29 -3.88,8.13 -7.94,10.55 0,0 7.64,29.58 7.64,29.58 0,0 50.14,-4.17 50.14,-4.17 0.72,-3.86 3.44,-7.37 7.59,-9.13 6.47,-2.74 13.96,-0.12 16.70,5.84 2.74,5.97 -0.28,13.04 -6.77,15.78 -5.77,2.44 -12.33,0.62 -15.64,-4.01 0,0 -49.83,4.15 -49.83,4.15 0,0 9.82,38.03 9.82,38.03 -4.48,0.60 -9.05,0.94 -13.69,1.00 0,0 -19.33,-74.79 -19.33,-74.79 -6.12,-1.26 -11.20,-5.59 -12.77,-11.67 -2.25,-8.71 3.54,-17.68 12.95,-20.06 8.58,-2.16 17.20,1.96 20.35,9.33 0,0 64.21,-26.35 64.21,-26.35 0.34,-3.82 2.68,-7.39 6.39,-9.47 -13.86,-9.58 -30.63,-15.26 -48.76,-15.42 -48.21,-0.43 -87.64,38.29 -88.07,86.50 -0.17,19.29 5.94,37.17 16.41,51.72 14.04,6.43 29.62,10.11 46.07,10.26 51.89,0.46 95.91,-34.09 109.68,-81.60 -3.19,-13.35 -9.47,-25.51 -18.03,-35.70 z" style="fill:url(#.rd3);stroke:none"/></g>'
    o += '<path d="m 145.03,-797.14 c 0,0 -64.21,26.35 -64.21,26.35 -3.14,-7.37 -11.76,-11.49 -20.35,-9.33 -9.40,2.37 -15.20,11.35 -12.95,20.06 1.57,6.08 6.65,10.41 12.77,11.67 0,0 19.33,74.79 19.33,74.79 4.63,-0.05 9.20,-0.39 13.69,-1.00 0,0 -9.82,-38.03 -9.82,-38.03 0,0 49.83,-4.15 49.83,-4.15 3.30,4.64 9.86,6.45 15.64,4.01 6.48,-2.74 9.51,-9.81 6.77,-15.78 -2.74,-5.96 -10.22,-8.59 -16.70,-5.84 -4.14,1.75 -6.86,5.26 -7.59,9.13 0,0 -50.14,4.17 -50.14,4.17 0,0 -7.64,-29.58 -7.64,-29.58 4.05,-2.42 6.89,-6.25 7.94,-10.55 0,0 66.45,-27.28 66.45,-27.28 3.51,3.72 9.40,5.01 14.64,2.79 2.64,-1.11 4.68,-2.96 6.02,-5.16 -5.03,-5.99 -10.84,-11.29 -17.30,-15.75 -3.71,2.08 -6.05,5.65 -6.39,9.47 z"/><path d="m 109.47,-660.64 c -1.81,-7.01 -8.29,-11.71 -15.66,-12.04 0,0 -0.49,-1.90 -0.49,-1.90 -4.48,0.60 -9.05,0.94 -13.69,1.00 0,0 1.34,5.21 1.34,5.21 -4.76,4.00 -7.12,10.21 -5.55,16.29 0.04,0.19 0.12,0.37 0.17,0.56 8.05,2.54 16.61,3.95 25.49,4.03 1.95,0.01 3.89,-0.05 5.82,-0.16 2.65,-3.73 3.74,-8.40 2.55,-13.00 z"/>'
    return o +  '</g>\n'

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

class svg_app:
    """ """

    def __init__(self,app,withlogo=True):
        self.app = app
        self.withlogo = withlogo

    def menubar(self,user,msg):
        """ """
        o = '<g id=".menubar">'
        (txt,act) = (user,'logout') if user else ('Sign in','signin')
        o += '<text class="button" onclick="%s();" fill="white" text-anchor="end" x="95%%" y="12">%s<title>%s</title></text>'%(act,txt,act)
        help_button = '?'
        o += '<text class="button" onclick="help();" fill="white" text-anchor="end" x="99%%" y="12">%s<title>Help</title></text>'%(help_button)
        color = 'red' if msg[:5] == 'Error' else 'white'
        [txt,title] = msg.split(':') if msg else ['','']
        o += '<text class="msg" id=".msg" fill="%s" text-anchor="end" x="88%%" y="12"> %s<title>%s</title></text>'%(color, txt, title)
        o += self.login_page()
        return o + '</g>\n'

    def login_page(self):
        """ display the login page"""
        o = '<g id=".loginpage" display="none">'
        o += '<rect x="0" y="0" width="100%" height="100%" opacity=".9" fill="#DDD"/>'
        o += '<text x="130" y="220">Login:</text>'
        o += '<text x="130" y="240">Password:</text>'
        o += '<text id=".ca" class="button" onclick="create_account(this);" x="200" y="170">Create a new account<title>...if you are new user</title></text>'
        o += '<text id=".cp" class="button" onclick="change_pw(this);" x="200" y="190">Change password<title>...if you already have an account</title></text>'
        o += '<text id="msg" display="none" x="200" y="190" fill="red">New account:</text>'
        o += '<foreignObject display="inline" y="200" x="200" width="120" height="80">' 
        o += '<div %s><form id="myform" method="post">'%_XHTMLNS
        o += '<input id="login" name="login" title="Login" size="10" value=""/>'
        o += '<input id="pw" onchange="submit();" name="pw" type="password" title="Password" size="10" value=""/>'
        o += '<input id="pw2" style="display:none" name="pw2" type="password" title="Password repeat" size="10" value=""/>'
        o += '<input id="lout" name="logout" type="hidden" value=""/>'
        o += '</form></div>'
        o += '</foreignObject>'
        o += '<g onclick="check();" title="submit login/password" class="button" fill="#444" transform="translate(320,208)"><rect x="1" width="15" height="30" rx="5"/><path transform="translate(0,6)" d="M4,4 4,14 14,9" fill="white"/></g>'
        if self.withlogo:
            o += logo()
        return o + '</g>'

    def __call__(self,environ, start_response):
        user = ''
        edit_mode = environ['PATH_INFO'] == "/edit"
        view_mode = environ['PATH_INFO'] == ""
        user,msg,logout,sid,hpw = get_user(environ)
        environ['svgapp.user'] = user
        environ['svgapp.hpw'] = hpw
        def custom_start_response(status, header): 
            if edit_mode or view_mode:
                header.append(('Content-type','application/xhtml+xml')) 
                if edit_mode:
                    set_cook(user,header,sid,hpw)
            else:
                header.append(('Content-type','text/plain')) 
            return start_response(status, header)
        response_iter = self.app(environ, custom_start_response)
        a,o = '',''
        if edit_mode or view_mode:
            o += '<?xml version="1.0" encoding="UTF-8"?>\n'
            o += '<?xml-stylesheet href="css/svgapp.css" type="text/css"?>\n'
            o += '<svg %s editable="%s"%s>\n'%(_SVGNS, 'yes' if edit_mode else 'no',' user="%s"'%user if user else '')
            o += '<script %s type="text/ecmascript">%s</script>\n'%(_XLINKNS,js()) 
            o += defs()
            if edit_mode:
                o += '<rect class="theme" width="100%" height="18"/>'
                a = self.menubar(user,msg)
                a += '<text id=".debug" class="small" x="300" y="12"> </text>\n'
                #a += '<text x="300" y="32">%s|%s </text>\n'%(user,hpw)
            a += '</svg>'            
        response_string = o + ''.join(response_iter) + a 
        return [response_string]

def my_app(environ,start_response):
    """ app """
    start_response('200 OK',[])
    return []

#application = svgapp.svg_app(my_app)

if __name__ == '__main__':
    print 'end'
