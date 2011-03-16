#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Warning: UNDER_CONSTRUCTION
This is a modified code from Kjell Magne Fauske initial code 
...with requirements:
- fit on one python file (avoid library complex setup for user)
- only used for Python API 
- no need to store SVG input in a file (use serializing string)
- not an Inkscape extension anymore
- not used in command line

Unless KMF not adding features requested on google code, I will try to implement
the features I need for ConnectedGraph
- remove <title> tags
- do not display if attribute value of display equal none
- support markers
- text size
- ...

Laurent 
"""


"""\
Convert SVG to TikZ/PGF commands for use with (La)TeX

This script is an Inkscape extension for exporting from SVG to (La)TeX. The
extension recreates the SVG drawing using TikZ/PGF commands, a high quality TeX
macro package for creating graphics programmatically.

The script is tailored to Inkscape SVG, but can also be used to convert arbitrary
SVG files from the command line. 

Author: Kjell Magne Fauske
"""

# Copyright (C) 2008, 2009, 2010 Kjell Magne Fauske, http://www.fauskes.net
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__version__ = '0.1dev'
__author__ = 'Kjell Magne Fauske'

# Todo:
# Basic functionality:

# Stroke properties
#   - markers (map from Inkscape to TikZ arrow styles. No 1:1 mapping)
# Fill properties
#   - linear shading
#   - radial shading
# Paths:
#
# Text
# 
# Other stuff:
# - Better output code formatting!
# - Add a + prefix to coordinates to speed up pgf parsing
# - Transformations
#   - default property values.The initial fill property is set to 'black'.
#     This is currently not handled. 
# - ConTeXt template support.
# TODO: Add a testing interface
import sys
from itertools import izip
from copy import deepcopy
import itertools
import string
import StringIO
import copy
from lxml import etree 
import pprint, os, re,math
from math import sin, cos, atan2, ceil

NSS = {
u'svg'      :u'http://www.w3.org/2000/svg',
u'xlink'    :u'http://www.w3.org/1999/xlink',
}

def addNS(tag, ns=None):
    val = tag
    if ns!=None and len(ns)>0 and NSS.has_key(ns) and len(tag)>0 and tag[0]!='{':
        val = "{%s}%s" % (NSS[ns], tag)
    return val

uuconv = {'in':90.0, 'pt':1.25, 'px':1, 'mm':3.5433070866, 'cm':35.433070866, 'pc':15.0}
def unittouu(string):
    '''Returns userunits given a string representation of units in another system'''
    unit = re.compile('(%s)$' % '|'.join(uuconv.keys()))
    param = re.compile(r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')

    p = param.match(string)
    u = unit.search(string)    
    if p:
        retval = float(p.string[p.start():p.end()])
    else:
        retval = 0.0
    if u:
        try:
            return retval * uuconv[u.string[u.start():u.end()]]
        except KeyError:
            pass
    return retval

#### Utility functions and classes

class Bunch(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    def __str__(self):
        return self.__dict__.__str__()
    def __repr__(self):
        return self.__dict__.__repr__()

def nsplit(seq, n=2):
    """Split a sequence into pieces of length n

    If the length of the sequence isn't a multiple of n, the rest is discarded.
    Note that nsplit will strings into individual characters.

    Examples:
    >>> nsplit('aabbcc')
    [('a', 'a'), ('b', 'b'), ('c', 'c')]
    >>> nsplit('aabbcc',n=3)
    [('a', 'a', 'b'), ('b', 'c', 'c')]

    # Note that cc is discarded
    >>> nsplit('aabbcc',n=4)
    [('a', 'a', 'b', 'b')]
    """
    return [xy for xy in izip(*[iter(seq)]*n)]


def chunks(s, cl):
    """Split a string or sequence into pieces of length cl and return an iterator
    """
    for i in xrange(0, len(s), cl):
        yield s[i:i+cl]

#### Output configuration section

TEXT_INDENT = "  "

CROP_TEMPLATE = r"""
\usepackage[active,tightpage]{preview}
\PreviewEnvironment{tikzpicture}
"""


# Templates
STANDALONE_TEMPLATE=r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{tikz}
%(cropcode)s
\begin{document}
%(colorcode)s
\begin{tikzpicture}[y=0.80pt,x=0.80pt,yscale=-1, inner sep=0pt, outer sep=0pt%(extraoptions)s]
%(pathcode)s
\end{tikzpicture}
\end{document}
"""

SCALE = 'scale'
DICT = 'dict'
DIMENSION = 'dimension'
FACTOR = 'factor' # >= 1

# Map Inkscape/SVG stroke and fill properties to corresponding TikZ options.
# Format:
#   'svg_name' : ('tikz_name', value_type, data)
PROPERTIES_MAP = {
    'opacity' : ('opacity',SCALE,''),
    # filling    
    'fill-opacity' : ('fill opacity', SCALE,''),
    'fill-rule' : ('',DICT,
                   dict(nonzero='nonzero rule',evenodd='even odd rule')),
    # stroke    
    'stroke-opacity' : ('draw opacity', SCALE,''),
    'stroke-linecap' : ('line cap',DICT,
                        dict(butt='butt',round='round',square='rect')),
    'stroke-linejoin' : ('line join',DICT,
                         dict(miter='miter',round='round',bevel='bevel')),
    'stroke-width' : ('line width',DIMENSION,''),
    'stroke-miterlimit' : ('miter limit', FACTOR,''),
    'stroke-dashoffset' : ('dash phase',DIMENSION,'0')
}

# default values according to the SVG spec.
DEFAULT_PAINTING_VALUES = {
    # fill
    'fill' : 'black',
    'fill-rule' : 'nonzero',
    'fill-opacity' : 1,
    # stroke
    'stroke' : 'none',
    'stroke-width' : 1,
    'stroke-linecap' : 'butt',
    'stroke-linejoin' : 'miter',
    'stroke-miterlimit' : 4,
    'stroke-dasharray' : 'none',
    'stroke-dashoffset' : 0,
    'stroke-opacity' : 1,
}

STROKE_PROPERTIES = set([
    'stroke', 'stroke-width', 'stroke-linecap', 
    'stroke-linejoin', 'stroke-miterlimit',
    'stroke-dasharray', 'stroke-dashoffset',
    'stroke-opacity',
])

FILL_PROPERTIES = set([
    'fill', 'fill-rule', 'fill-opacity',
])


# The calc_arc function is based on the calc_arc function in the
# paths_svg2obj.py script bundled with Blender 3D
# Copyright (c) jm soler juillet/novembre 2004-april 2007, 
def calc_arc(cpx, cpy, rx, ry, ang, fa, fs, x, y) :
    """
    Calc arc paths
    """
    PI = math.pi
    ang = math.radians(ang)
    rx = abs(rx)
    ry = abs(ry)
    px = abs((cos(ang)*(cpx-x)+sin(ang)*(cpy-y))*0.5)**2.0
    py = abs((cos(ang)*(cpy-y)-sin(ang)*(cpx-x))*0.5)**2.0
    rpx = rpy = 0.0
    if abs(rx) > 0.0:
        rpx = px/(rx**2.0)
    if abs(ry) > 0.0:
        rpy = py/(ry**2.0)
    pl = rpx+rpy
    if pl>1.0:
        pl = pl**0.5
        rx*=pl;ry*=pl
    carx = sarx = cary = sary = 0.0
    if abs(rx) > 0.0:
        carx = cos(ang)/rx
        sarx = sin(ang)/rx
    if abs(ry) > 0.0:
        cary = cos(ang)/ry
        sary=sin(ang)/ry
    x0 = (carx)*cpx+(sarx)*cpy
    y0 = (-sary)*cpx+(cary)*cpy
    x1 = (carx)*x+(sarx)*y
    y1 = (-sary)*x+(cary)*y
    d = (x1-x0)*(x1-x0)+(y1-y0)*(y1-y0)
    if abs(d) > 0.0:
        sq=1.0/d-0.25
    else:
        sq=-0.25
    if sq <0.0:
        sq=0.0
    sf = sq**0.5
    if fs == fa:
        sf=-sf
    xc = 0.5*(x0+x1)-sf*(y1-y0)
    yc = 0.5*(y0+y1)+sf*(x1-x0)
    ang_0 = atan2(y0-yc,x0-xc)
    ang_1 = atan2(y1-yc,x1-xc)
    ang_arc = ang_1-ang_0
    if (ang_arc < 0.0 and fs==1):
        ang_arc += 2.0 * PI
    elif (ang_arc > 0.0 and fs==0):
        ang_arc-=2.0*PI
    
    ang0 = math.degrees(ang_0)
    ang1 = math.degrees(ang_1)

    if ang_arc > 0:
        if (ang_0 < ang_1):
            pass
        else:
            ang0 -= 360
    else:
        if (ang_0 < ang_1):
            ang1 -= 360

    return (ang0, ang1, rx, ry)

def parse_transform(transf):
    """Parse a transformation attribute and return a list of transformations"""
    # Based on the code in parseTransform in the simpletransform.py module.
    # Copyright (C) 2006 Jean-Francois Barraud
    # Reimplemented here due to several bugs in the version shipped with
    # Inkscape 0.46
    if transf=="" or transf==None:
        return(mat)
    stransf = transf.strip()
    result = re.match("(translate|scale|rotate|skewX|skewY|matrix)\s*\(([^)]*)\)\s*,?",stransf)
    transforms = []
    #-- translate --
    if result.group(1) == "translate":
        args=result.group(2).replace(',',' ').split()
        dx = float(args[0])
        if len(args) == 1:
            dy = 0.0
        else:
            dy = float(args[1])
        matrix = [[1,0,dx],[0,1,dy]]
        transforms.append(['translate',(dx,dy)])
    #-- scale --
    if result.group(1)== "scale":
        args = result.group(2).replace(',',' ').split()
        sx = float(args[0])
        if len(args) == 1:
            sy = sx
        else:
            sy = float(args[1])
        matrix=[[sx,0,0],[0,sy,0]]
        transforms.append(['scale', (sx,sy)])
    #-- rotate --
    if result.group(1) == "rotate":
        args = result.group(2).replace(',', ' ').split()
        a = float(args[0])#*math.pi/180
        if len(args) == 1:
            cx, cy = (0.0,0.0)
        else:
            cx, cy = map(float, args[1:])
        matrix=[[math.cos(a),-math.sin(a),cx],[math.sin(a),math.cos(a),cy]]
        transforms.append(['rotate',(a,cx,cy)])
    #-- skewX --
    if result.group(1) == "skewX":
        a = float(result.group(2))#"*math.pi/180
        matrix = [[1,math.tan(a),0],[0,1,0]]
        transforms.append(['skewX',(a,)])
    #-- skewY --
    if result.group(1) == "skewY":
        a=float(result.group(2))#*math.pi/180
        matrix=[[1,0,0],[math.tan(a),1,0]]
        transforms.append(['skewY',(a,)])
    #-- matrix --
    if result.group(1) == "matrix":
        #a11,a21,a12,a22,v1,v2=result.group(2).replace(' ',',').split(",")
        mparams = tuple(map(float, result.group(2).replace(',',' ').split()))
        a11,a21,a12,a22,v1,v2 = mparams
        matrix=[[a11, a12, v1], [a21, a22, v2]]
        transforms.append(['matrix', mparams])

    if result.end() < len(stransf):
        return transforms + parse_transform(stransf[result.end():])
    else:
        return transforms

def parseColor(c):
    """Creates a rgb int array"""
    # Based on the code in parseColor in the simplestyle.py module
    # Fixes a few bugs. Should be removed when fixed upstreams.
    if c in simplestyle.svgcolors.keys():
        c = simplestyle.svgcolors[c]
    # need to handle 'currentColor'
    if c.startswith('#') and len(c) == 4:
        c='#'+c[1:2]+c[1:2]+c[2:3]+c[2:3]+c[3:]+c[3:]
    elif c.startswith('rgb('):
        # remove the rgb(...) stuff
        tmp = c.strip()[4:-1]
        numbers = [number.strip() for number in tmp.split(',')]
        converted_numbers = []
        if len(numbers) == 3:
            for num in numbers:
                if num.endswith(r'%'):
                    converted_numbers.append( int(float(num[0:-1])*255/100))
                else:
                    converted_numbers.append(int(num))
            return tuple(converted_numbers)
        else:    
            return (0,0,0)
    try:
        r=int(c[1:3],16)
        g=int(c[3:5],16)
        b=int(c[5:],16)
    except:
        return (0,0,0)
    return (r,g,b)

def parseStyle(s):
    """Create a dictionary from the value of an inline style attribute"""
    # This version strips leading and trailing whitespace from keys and values
    if s:
        return dict([map(string.strip,i.split(":")) for i in s.split(";") if len(i)])
    else:
        return {}

class GraphicsState(object):
    """A class for handling the graphics state of an SVG element
    The graphics state includs fill, stroke and transformations.
    """
    fill = {}
    stroke = {}
    is_visible = True
    transform = []
    color = None
    opacity = 1
    def __init__(self, svg_node):
        self.svg_node = svg_node
        self._parent_states = None
        self._get_graphics_state(svg_node)
        
    def _get_graphics_state(self, node):
        """Return the painting state of the node SVG element"""
        if node is None: return
        style = parseStyle(node.get('style',''))
        stroke = {}
        fill = {}
        
        for stroke_property in STROKE_PROPERTIES:
            stroke_val = style.get(stroke_property) or node.get(stroke_property)
            if stroke_val:
                stroke[stroke_property] = stroke_val
                
        for fill_property in FILL_PROPERTIES:
            fill_val = style.get(fill_property) or node.get(fill_property)
            if fill_val:
                fill[fill_property] = fill_val
        
        display = style.get('display') or node.get('display')
        visibility = style.get('visibility') or node.get('visibility')
        if display == 'none' or visibility == 'hidden':
            is_visible = False
        else:
            is_visible = True
        
        self.color = style.get('color') or node.get('color')
        self.stroke = stroke
        self.fill = fill
        self.is_visible = is_visible
        opacity = style.get('opacity') or node.get('opacity')
        if opacity:
            self.opacity = opacity
        else:
            self.opacity = 1
        
        transform = node.get('transform','')
        if transform:
            self.transform = parse_transform(transform)
        else:
            self.transform = []
        
    def _get_parent_states(self, node=None):
        """Returns the parent's graphics states as a list"""
        if node == None:
            node = self.svg_node
        parent_node = node.getparent()
        if not parent_node:
            return None
        parents_state = []
        while parent_node:
            parents_state.append(GraphicsState(parent_state))
            parent_node = parent_node.getparent()
        return parents_state
            
            
    parent_states = property(fget=_get_parent_states)
    
    def accumulate(self, state):
        newstate = GraphicsState(None)
        newstate.fill = copy.copy(self.fill)
        newstate.stroke = copy.copy(self.stroke)
        newstate.transform = copy.copy(self.transform)
        newstate.opacity = copy.copy(self.opacity)
        newstate.fill.update(state.fill)
        newstate.stroke.update(state.stroke)
        if newstate.stroke.get('stroke','') == 'none':
            del newstate.stroke['stroke']
        if newstate.fill.get('fill','') == 'none':
            del newstate.fill['fill']
        newstate.transform += state.transform
        newstate.is_visible = self.is_visible and state.is_visible
        if state.color:
            newstate.color = state.color
            
        newstate.opacity *= state.opacity
        return newstate
        
    def __str__(self):
        return "fill %s\nstroke: %s\nvisible: %s\ntransformations: %s" %\
        (self.fill, self.stroke, self.is_visible, self.transform)
    
class TikZPathExporter():
    def __init__(self):
        self.document=None
        self.selected={}
        self.options=None
        self.args=None
        self.text_indent = ''
        self.x_o = self.y_o = 0.0
        # px -> cm scale factors
        self.x_scale = 0.02822219;
        # SVG has its origin in the upper left corner, while TikZ' origin is
        # in the lower left corner. We therefore have to reverse the y-axis.
        self.y_scale = -0.02822219;
        self.colors = {}
        self.colorcode = ""
        self.shadecode = ""
        self.output_code = ""

    def parse(self, file_or_string=None):
        self.document = etree.parse(StringIO.StringIO(file_or_string))

    def getselected(self):
        self.selected_sorted = []
        self.selected = {}
        return

    def get_node_from_id(self,node_ref):
        if node_ref.startswith('url('):
            node_id = re.findall(r'url\((.*?)\)', node_ref)
            if len(node_id) > 0:
                ref_id = node_id[0]
        else:
            ref_id = node_ref
        if ref_id.startswith('#'):
            ref_id = ref_id[1:]
    
        ref_node = self.document.xpath('//*[@id="%s"]' % ref_id,
                                           namespaces=NSS)
        if len(ref_node) == 1:
            return ref_node[0]
        else:
            return None
    
    def transform(self, coord_list, cmd=None):
        """Apply transformations to input coordinates"""
        coord_transformed = []
        # TEMP:
        if cmd == 'Q':
            return tuple(coord_list)
        try:
            if not len(coord_list) % 2:
                for x, y in nsplit(coord_list,2):
                    coord_transformed.append("%.4f" % x)
                    coord_transformed.append("%.4f" % y)
            elif len(coord_list)==1:
                coord_transformed = ["%.4fcm" % (coord_list[0]*self.x_scale)]
            else:
                coord_transformed = coord_list
        except:
            coord_transformed = coord_list
        return tuple(coord_transformed)

    def get_color(self, color):
        """Return a valid xcolor color name and store color"""

        if color in self.colors:
            return self.colors[color]
        else:
            r,g,b = parseColor(color)
            if not (r or g or b):
                return "black"
            if color.startswith('rgb'):
                xcolorname = "c%02x%02x%02x" % (r,g,b)
            else:
                xcolorname = color.replace('#','c')
            self.colors[color] = xcolorname
            self.colorcode += "\\definecolor{%s}{RGB}{%s,%s,%s}\n" \
                              % (xcolorname,r,g,b)
            return xcolorname
    
    def _convert_gradient(self, gradient_node):
        """Convert an SVG gradient to a PGF gradient"""
        # http://www.w3.org/TR/SVG/pservers.html
        pass
    
    def _handle_gradient(self, gradient_ref, node=None):
        grad_node = self.get_node_from_id(gradient_ref)
        if grad_node == None:
            return []
        return ['shade', 'shading=%s' % grad_node.get('id')]
        
    def convert_svgstate_to_tikz(self, state, accumulated_state=None, node=None):
        """Return a node's SVG styles as a list of TikZ options"""
        if state.is_visible == False:
            return [], []
            
        options = []
        transform = []
        
        if state.color:
            options.append('color=%s' % self.get_color(state.color))
        
        stroke = state.stroke.get('stroke','')
        if stroke <> 'none':
            if stroke:
                if stroke == 'currentColor':
                    options.append('draw')
                else:
                    options.append('draw=%s' % self.get_color(stroke))
            else:
                # need to check if parent element has stroke set
                if 'stroke' in accumulated_state.stroke:
                    options.append('draw')
                
        fill = state.fill.get('fill')
        if fill <> 'none':
            if fill:
                if fill == 'currentColor':
                    options.append('fill')
                #elif fill.startswith('url('):
                #    shadeoptions = self._handle_gradient(fill)
                #    options.extend(shadeoptions)
                else:
                    options.append('fill=%s' % self.get_color(fill))
            else:
                # Todo: check parent element
                if 'fill' in accumulated_state.fill:
                    options.append('fill')
    
        # dash pattern has to come before dash phase. This is a bug in TikZ 2.0
        # Fixed in CVS.             
        dasharray = state.stroke.get('stroke-dasharray')
        if dasharray and dasharray <> 'none':
            lengths = map(unittouu, [i.strip() for i in dasharray.split(',')])
            dashes = []
            for idx, length in enumerate(lengths):
                lenstr = "%0.2fpt" % (length*0.8)
                if idx % 2 :
                    dashes.append("off %s" % lenstr)
                else:
                    dashes.append("on %s" % lenstr)
            options.append('dash pattern=%s' % " ".join(dashes))
        
        try:
            opacity = float(state.opacity)
            if opacity < 1.0:
                options.append('opacity=%.03f' % opacity)
        except:
            pass
        
        for svgname, tikzdata in PROPERTIES_MAP.iteritems():
            tikzname, valuetype,data = tikzdata
            value = state.fill.get(svgname) or state.stroke.get(svgname)
            if not value: continue
            if valuetype == SCALE:
                val = float(value)
                if not val == 1:
                    options.append('%s=%.3f' % (tikzname,float(value)))
            elif valuetype == DICT:
                if tikzname:
                    options.append('%s=%s' % (tikzname,data.get(value,'')))
                else:
                    options.append('%s' % data.get(value,''))
            elif valuetype == DIMENSION:
                # FIXME: Handle different dimensions in a general way
                if value and value <> data:
                    options.append('%s=%.3fpt' % (tikzname,unittouu(value)*0.80)),
            elif valuetype == FACTOR:
                try:
                    val = float(value)
                    if val >= 1.0:
                        options.append('%s=%.2f' % (tikzname,val))
                except ValueError:
                    pass
            
        if len(state.transform) > 0:
            transform = self._convert_transform_to_tikz(state.transform)
        else:
            transform = []
               
        return options, transform
    
    
    def _convert_transform_to_tikz(self, transform):
        """Convert a SVG transform attribute to a list of TikZ transformations"""
        #return ""
        if not transform:
            return []

        options = []
        for cmd, params in transform:
            if cmd == 'translate':
                x, y = params
                options.append("shift={(%s,%s)}" % (x or '0',y or '0'))
                # There is bug somewere.
                # shift=(400,0) is not equal to xshift=400
                
            elif cmd == 'rotate':
                if params[1] or params[2]:
                    options.append("rotate around={%s:(%s,%s)}" % params)
                else:
                    options.append("rotate=%s" % params[0])
            elif cmd == 'matrix':
                options.append("cm={{%s,%s,%s,%s,(%s,%s)}}" % params)
            elif cmd == 'skewX':
                options.append("xslant=%.3f" % math.tan(params[0]*math.pi/180))
            elif cmd == 'skewY':
                options.append("yslant=%.3f" % math.tan(params[0]*math.pi/180))
            elif cmd == 'scale':
                if params[0]==params[1]:
                    options.append("scale=%.3f" % params[0])
                else:
                    options.append("xscale=%.3f,yscale=%.3f" % params)

        return options

    def _handle_group(self, groupnode, graphics_state, accumulated_state):
        s = ""
        tmp = self.text_indent
        self.text_indent += TEXT_INDENT
        id = groupnode.get('id')
        if groupnode.get('display') == 'none':
            return s
        code = self._output_group(groupnode, accumulated_state.accumulate(graphics_state))
        self.text_indent = tmp
        extra = ''
        goptions, transformation = self.convert_svgstate_to_tikz(graphics_state, graphics_state, groupnode)
        options = transformation + goptions
        if len(options) > 0:
            pstyles = [','.join(options)]
            if 'opacity' in pstyles[0]:
                pstyles.append('transparency group')
            
            s += "%s\\begin{scope}[%s]%s\n%s%s\\end{scope}\n" % \
                (self.text_indent,",".join(pstyles), extra,
                 code,self.text_indent)
        else:
            s += code
        return s

    def _handle_path(self, node):
        p = parsePath(node.get('d'))
        return p, []
    
    def _handle_shape(self, node):
        """Extract shape data from node"""
        options = []
        if node.tag == addNS('rect','svg'):
            inset = node.get('rx','0') or node.get('ry','0')
            # TODO: ry <> rx is not supported by TikZ. Convert to path?
            x = unittouu(node.get('x','0'))
            y = unittouu(node.get('y','0'))
            # map from svg to tikz
            width = unittouu(node.get('width','0'))
            height = unittouu(node.get('height','0'))
            if (width == 0.0 or height == 0.0):
                return None, []
            if inset:
                # TODO: corner radius is not scaled by PGF. Find a better way to fix this. 
                options = ["rounded corners=%s" % self.transform([unittouu(inset)*0.8])]
            return ('rect',(x,y,width+x,height+y)),options
        elif node.tag in [addNS('polyline','svg'),
                          addNS('polygon','svg'),
                          ]:
            points = node.get('points','').replace(',',' ')
            points = map(unittouu,points.split())
            if node.tag == addNS('polyline','svg'):
                cmd = 'polyline'
            else:
                cmd = 'polygon'
    
            return (cmd,points),options
        elif node.tag in addNS('line','svg'):
            points = [node.get('x1'),node.get('y1'),
                      node.get('x2'),node.get('y2')]
            points = map(unittouu,points)
            # check for zero lenght line
            if not ((points[0] == points[2]) and (points[1] == points[3])):
                return ('polyline',points),options

        if node.tag == addNS('circle','svg'):
            # ugly code...
            center = map(unittouu,[node.get('cx','0'),node.get('cy','0')])
            r = unittouu(node.get('r','0'))
            if r > 0.0:
                return ('circle',self.transform(center)+self.transform([r])),options

        elif node.tag == addNS('ellipse','svg'):
            center = map(unittouu,[node.get('cx','0'),node.get('cy','0')])
            rx = unittouu(node.get('rx','0'))
            ry = unittouu(node.get('ry','0'))
            if rx > 0.0 and ry > 0.0:
                return ('ellipse',self.transform(center)+self.transform([rx])
                                 +self.transform([ry])),options
        else:
            return None,options
        
        return None, options
            
    def _handle_text(self, node):
        textstr = etree.tostring(node,method="text")
        size = node.get('font-size')
        opt = [] if size == '12' else []
        x = node.get('x','0')
        y = node.get('y','0')

        style = parseStyle(node.get('style',''))
        size = style.get('font-size')
        if size == '3pt' or size == '4pt' or size == '5pt':
            textstr = '\\tiny ' + textstr 
        p = [('M',[x,y]),('TXT',textstr)]
        return p, opt
    
    def _handle_use(self, node, graphics_state, accumulated_state=None):
        # Find the id of the use element link
        ref_id = node.get(addNS('href', 'xlink'))
        if ref_id.startswith('#'):
            ref_id = ref_id[1:]
    
        use_ref_node = self.document.xpath('//*[@id="%s"]' % ref_id,
                                           namespaces=NSS)
        if len(use_ref_node) == 1:
            use_ref_node = use_ref_node[0]
        else:
            return ""
        
        # create a temp group
        g_wrapper = etree.Element(addNS('g', 'svg'))
        use_g = etree.SubElement(g_wrapper,addNS('g', 'svg'))
        
        # transfer attributes from use element to new group except
        # x, y, width, height and href
        for key in node.keys():
            if key not in ('x', 'y', 'width', 'height',
                           addNS('href', 'xlink')):
                use_g.set(key, node.get(key))
        if node.get('x') or node.get('y'):
            transform = node.get('transform','')
            transform += ' translate(%s,%s) '\
                % (node.get('x',0), node.get('y',0))
            use_g.set('transform', transform)       
        #
        use_g.append( deepcopy(use_ref_node) )
        return self._output_group(g_wrapper, accumulated_state)
    
    def _write_tikz_path(self, pathdata, options=[], node=None):
        """Convert SVG paths, shapes and text to TikZ paths"""
        s = pathcode = ""
        #print "Pathdata %s" % pathdata
        if not pathdata or len(pathdata) == 0:
            return ""
        if node is not None:
            id = node.get('id', '')
        else:
            id = ''
        
        current_pos = [0.0,0.0]
        for cmd,params in pathdata:
            # transform coordinates
            tparams = self.transform(params,cmd)
            # SVG paths
            # moveto
            if cmd == 'M':
                s += "(%s,%s)" % tparams
                current_pos = params[-2:]
            # lineto
            elif cmd == 'L':
                s += " -- (%s,%s)" % tparams
                current_pos = params[-2:]
            # cubic bezier curve
            elif cmd == 'C':
                s += " .. controls (%s,%s) and (%s,%s) .. (%s,%s)" % tparams
                current_pos = params[-2:]
            # quadratic bezier curve 
            elif cmd == 'Q':
                # need to convert to cubic spline
                #CP1 = QP0 + 2/3 *(QP1-QP0)
                #CP2 = CP1 + 1/3 *(QP2-QP0)
                # http://fontforge.sourceforge.net/bezier.html
                qp0x, qp0y = current_pos
                qp1x,qp1y,qp2x,qp2y = tparams
                cp1x = qp0x +(2.0/3.0)*(qp1x-qp0x)
                cp1y = qp0y +(2.0/3.0)*(qp1y-qp0y)
                cp2x = cp1x +(qp2x-qp0x)/3.0
                cp2y = cp1y +(qp2y-qp0y)/3.0
                s += " .. controls (%.4f,%.4f) and (%.4f,%.4f) .. (%.4f,%.4f)"\
                     % (cp1x,cp1y,cp2x,cp2y,qp2x,qp2y)
                current_pos = params[-2:]
            # close path
            elif cmd == 'Z':
                s += " -- cycle"
                closed_path = True
            # arc
            elif cmd == 'A':
                start_ang_o, end_ang_o, rx, ry = calc_arc(current_pos[0],current_pos[1],*params)
                # pgf 2.0 does not like angles larger than 360
                # make sure it is in the +- 360 range
                start_ang = start_ang_o % 360
                end_ang = end_ang_o % 360
                if start_ang_o < end_ang_o and not (start_ang < end_ang):
                    start_ang -= 360
                elif start_ang_o > end_ang_o and not (start_ang > end_ang):
                    end_ang -= 360  
                ang = params[2]
                if rx == ry:
                    # Todo: Transform radi
                    radi = "%.3f" % rx
                else:
                    radi = "%3f and %.3f" % (rx,ry)
                if ang <> 0.0:
                    s += "{[rotate=%s] arc(%.3f:%.3f:%s)}" % (ang,start_ang,end_ang,radi)
                else:
                    s += "arc(%.3f:%.3f:%s)" % (start_ang,end_ang,radi)
                current_pos = params[-2:]
                pass
            elif cmd == 'TXT':
                s += " node[above right] (%s) {%s}" %(id,params)
            # Shapes
            elif cmd == 'rect':
                s += "(%s,%s) rectangle (%s,%s)" % tparams
                closed_path = True
            elif cmd in ['polyline','polygon']:
                points = ["(%s,%s)" % (x,y) for x,y in chunks(tparams,2)]
                if cmd == 'polygon':
                    points.append('cycle')
                    closed_path = True
                s += " -- ".join(points)
            # circle and ellipse does not use the transformed parameters
            elif cmd == 'circle':
                s += "(%s,%s) circle (%s)" % params
                closed_path = True
            elif cmd == 'ellipse':
                s += "(%s,%s) ellipse (%s and %s)" % params
                closed_path = True
        
        if options:
            optionscode = "[%s]" % ','.join(options)
        else:
            optionscode = ""
            
        pathcode = "\\path%s %s;" % (optionscode,s)
        pathcode = "\n".join([self.text_indent + line for line in pathcode.splitlines(False)])+"\n"
        return pathcode
    
    def _output_group(self, group, accumulated_state=None):
        """Proceess a group of SVG nodes and return corresponding TikZ code
        The group is processed recursively if it contains sub groups. 
        """
        s = ""
        options = []
        transform = []
        for node in group:
            pathdata = None
            options = []
            graphics_state = GraphicsState(node)
            #print graphics_state 
            id = node.get('id')
            if node.tag == addNS('path','svg'):
                pathdata, options = self._handle_path(node)
                
                
            # is it a shape?
            elif node.tag in [addNS('rect','svg'),
                              addNS('polyline','svg'),
                              addNS('polygon','svg'),
                              addNS('line','svg'),
                              addNS('circle','svg'),
                              addNS('ellipse','svg'),]:
                shapedata, options = self._handle_shape(node)
                if shapedata:
                    pathdata = [shapedata]
                
            # group node
            elif node.tag == addNS('g', 'svg'):
                s += self._handle_group(node, graphics_state, accumulated_state)
                continue
                
            elif node.tag == addNS('text', 'svg'):
                pathdata, options = self._handle_text(node)
                
            elif node.tag == addNS('use', 'svg'):
                s += self._handle_use(node, graphics_state, accumulated_state)

            else:
                # unknown element
                pass
            
            goptions, transformation = self.convert_svgstate_to_tikz(graphics_state, accumulated_state, node)
            #print goptions, transformation, options
            options = transformation + goptions + options
            s += self._write_tikz_path(pathdata, options, node)
        return s

    def effect(self):
        s = ""
        nodes = self.selected_sorted
        # If no nodes is selected convert whole document. 
        if len(nodes) == 0:
            nodes = self.document.getroot()
            graphics_state = GraphicsState(nodes)
        else:
            graphics_state = GraphicsState(None)
        goptions, transformation = self.convert_svgstate_to_tikz(graphics_state, graphics_state, self.document.getroot())
        options = transformation + goptions
        # Recursively process list of nodes or root node
        s = self._output_group(nodes, graphics_state)

        # Add necessary boiling plate code to the generated TikZ code. 
        if len(options) > 0:
            extraoptions = ',\n%s' % ','.join(options)
        else:
            extraoptions = ''
        cropcode = ""
        output = STANDALONE_TEMPLATE % dict(pathcode=s,\
                                                colorcode=self.colorcode,\
                                                cropcode=cropcode,\
                                                extraoptions=extraoptions)
        self.output_code = output    
        return output
                
    def output(self):
        print self.output_code.encode('utf8')
            
    def convert(self,svg_file):
        self.parse(svg_file)
        self.getselected()
        return self.effect()
        
# Entry call
def convert_code(source):
    effect = TikZPathExporter();
    return effect.convert(source)
#######

def lexPath(d):
    """
    returns and iterator that breaks path data 
    identifies command and parameter tokens
    """
    offset = 0
    length = len(d)
    delim = re.compile(r'[ \t\r\n,]+')
    command = re.compile(r'[MLHVCSQTAZmlhvcsqtaz]')
    parameter = re.compile(r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')
    while 1:
        m = delim.match(d, offset)
        if m:
            offset = m.end()
        if offset >= length:
            break
        m = command.match(d, offset)
        if m:
            yield [d[offset:m.end()], True]
            offset = m.end()
            continue
        m = parameter.match(d, offset)
        if m:
            yield [d[offset:m.end()], False]
            offset = m.end()
            continue
        #TODO: create new exception
        raise Exception, 'Invalid path data!'
'''
pathdefs = {commandfamily:
    [
    implicitnext,
    #params,
    [casts,cast,cast],
    [coord type,x,y,0]
    ]}
'''
pathdefs = {
    'M':['L', 2, [float, float], ['x','y']], 
    'L':['L', 2, [float, float], ['x','y']], 
    'H':['H', 1, [float], ['x']], 
    'V':['V', 1, [float], ['y']], 
    'C':['C', 6, [float, float, float, float, float, float], ['x','y','x','y','x','y']], 
    'S':['S', 4, [float, float, float, float], ['x','y','x','y']], 
    'Q':['Q', 4, [float, float, float, float], ['x','y','x','y']], 
    'T':['T', 2, [float, float], ['x','y']], 
    'A':['A', 7, [float, float, float, int, int, float, float], [0,0,0,0,0,'x','y']], 
    'Z':['L', 0, [], []]
    }

def parsePath(d):
    """
    Parse SVG path and return an array of segments.
    Removes all shorthand notation.
    Converts coordinates to absolute.
    """
    retval = []
    lexer = lexPath(d)

    pen = (0.0,0.0)
    subPathStart = pen
    lastControl = pen
    lastCommand = ''
    
    while 1:
        try:
            token, isCommand = lexer.next()
        except StopIteration:
            break
        params = []
        needParam = True
        if isCommand:
            if not lastCommand and token.upper() != 'M':
                raise Exception, 'Invalid path, must begin with moveto.'    
            else:                
                command = token
        else:
            #command was omited
            #use last command's implicit next command
            needParam = False
            if lastCommand:
                if lastCommand.isupper():
                    command = pathdefs[lastCommand][0]
                else:
                    command = pathdefs[lastCommand.upper()][0].lower()
            else:
                raise Exception, 'Invalid path, no initial command.'    
        numParams = pathdefs[command.upper()][1]
        while numParams > 0:
            if needParam:
                try: 
                    token, isCommand = lexer.next()
                    if isCommand:
                        raise Exception, 'Invalid number of parameters'
                except StopIteration:
                    raise Exception, 'Unexpected end of path'
            cast = pathdefs[command.upper()][2][-numParams]
            param = cast(token)
            if command.islower():
                if pathdefs[command.upper()][3][-numParams]=='x':
                    param += pen[0]
                elif pathdefs[command.upper()][3][-numParams]=='y':
                    param += pen[1]
            params.append(param)
            needParam = True
            numParams -= 1
        #segment is now absolute so
        outputCommand = command.upper()
    
        #Flesh out shortcut notation    
        if outputCommand in ('H','V'):
            if outputCommand == 'H':
                params.append(pen[1])
            if outputCommand == 'V':
                params.insert(0,pen[0])
            outputCommand = 'L'
        if outputCommand in ('S','T'):
            params.insert(0,pen[1]+(pen[1]-lastControl[1]))
            params.insert(0,pen[0]+(pen[0]-lastControl[0]))
            if outputCommand == 'S':
                outputCommand = 'C'
            if outputCommand == 'T':
                outputCommand = 'Q'

        #current values become "last" values
        if outputCommand == 'M':
            subPathStart = tuple(params[0:2])
            pen = subPathStart
        if outputCommand == 'Z':
            pen = subPathStart
        else:
            pen = tuple(params[-2:])

        if outputCommand in ('Q','C'):
            lastControl = tuple(params[-4:-2])
        else:
            lastControl = pen
        lastCommand = command

        retval.append([outputCommand,params])
    return retval

def formatPath(a):
    """Format SVG path data from an array"""
    return "".join([cmd + " ".join([str(p) for p in params]) for cmd, params in a])

def translatePath(p, x, y):
    for cmd,params in p:
        defs = pathdefs[cmd]
        for i in range(defs[1]):
            if defs[3][i] == 'x':
                params[i] += x
            elif defs[3][i] == 'y':
                params[i] += y

def scalePath(p, x, y):
    for cmd,params in p:
        defs = pathdefs[cmd]
        for i in range(defs[1]):
            if defs[3][i] == 'x':
                params[i] *= x
            elif defs[3][i] == 'y':
                params[i] *= y

def rotatePath(p, a, cx = 0, cy = 0):
    if a == 0:
        return p
    for cmd,params in p:
        defs = pathdefs[cmd]
        for i in range(defs[1]):
            if defs[3][i] == 'x':
                x = params[i] - cx
                y = params[i + 1] - cy
                r = math.sqrt((x**2) + (y**2))
                if r != 0:
                    theta = math.atan2(y, x) + a
                    params[i] = (r * math.cos(theta)) + cx
                    params[i + 1] = (r * math.sin(theta)) + cy

svgcolors={
    'aliceblue':'#f0f8ff',
    'antiquewhite':'#faebd7',
    'aqua':'#00ffff',
    'aquamarine':'#7fffd4',
    'azure':'#f0ffff',
    'beige':'#f5f5dc',
    'bisque':'#ffe4c4',
    'black':'#000000',
    'blanchedalmond':'#ffebcd',
    'blue':'#0000ff',
    'blueviolet':'#8a2be2',
    'brown':'#a52a2a',
    'burlywood':'#deb887',
    'cadetblue':'#5f9ea0',
    'chartreuse':'#7fff00',
    'chocolate':'#d2691e',
    'coral':'#ff7f50',
    'cornflowerblue':'#6495ed',
    'cornsilk':'#fff8dc',
    'crimson':'#dc143c',
    'cyan':'#00ffff',
    'darkblue':'#00008b',
    'darkcyan':'#008b8b',
    'darkgoldenrod':'#b8860b',
    'darkgray':'#a9a9a9',
    'darkgreen':'#006400',
    'darkgrey':'#a9a9a9',
    'darkkhaki':'#bdb76b',
    'darkmagenta':'#8b008b',
    'darkolivegreen':'#556b2f',
    'darkorange':'#ff8c00',
    'darkorchid':'#9932cc',
    'darkred':'#8b0000',
    'darksalmon':'#e9967a',
    'darkseagreen':'#8fbc8f',
    'darkslateblue':'#483d8b',
    'darkslategray':'#2f4f4f',
    'darkslategrey':'#2f4f4f',
    'darkturquoise':'#00ced1',
    'darkviolet':'#9400d3',
    'deeppink':'#ff1493',
    'deepskyblue':'#00bfff',
    'dimgray':'#696969',
    'dimgrey':'#696969',
    'dodgerblue':'#1e90ff',
    'firebrick':'#b22222',
    'floralwhite':'#fffaf0',
    'forestgreen':'#228b22',
    'fuchsia':'#ff00ff',
    'gainsboro':'#dcdcdc',
    'ghostwhite':'#f8f8ff',
    'gold':'#ffd700',
    'goldenrod':'#daa520',
    'gray':'#808080',
    'grey':'#808080',
    'green':'#008000',
    'greenyellow':'#adff2f',
    'honeydew':'#f0fff0',
    'hotpink':'#ff69b4',
    'indianred':'#cd5c5c',
    'indigo':'#4b0082',
    'ivory':'#fffff0',
    'khaki':'#f0e68c',
    'lavender':'#e6e6fa',
    'lavenderblush':'#fff0f5',
    'lawngreen':'#7cfc00',
    'lemonchiffon':'#fffacd',
    'lightblue':'#add8e6',
    'lightcoral':'#f08080',
    'lightcyan':'#e0ffff',
    'lightgoldenrodyellow':'#fafad2',
    'lightgray':'#d3d3d3',
    'lightgreen':'#90ee90',
    'lightgrey':'#d3d3d3',
    'lightpink':'#ffb6c1',
    'lightsalmon':'#ffa07a',
    'lightseagreen':'#20b2aa',
    'lightskyblue':'#87cefa',
    'lightslategray':'#778899',
    'lightslategrey':'#778899',
    'lightsteelblue':'#b0c4de',
    'lightyellow':'#ffffe0',
    'lime':'#00ff00',
    'limegreen':'#32cd32',
    'linen':'#faf0e6',
    'magenta':'#ff00ff',
    'maroon':'#800000',
    'mediumaquamarine':'#66cdaa',
    'mediumblue':'#0000cd',
    'mediumorchid':'#ba55d3',
    'mediumpurple':'#9370db',
    'mediumseagreen':'#3cb371',
    'mediumslateblue':'#7b68ee',
    'mediumspringgreen':'#00fa9a',
    'mediumturquoise':'#48d1cc',
    'mediumvioletred':'#c71585',
    'midnightblue':'#191970',
    'mintcream':'#f5fffa',
    'mistyrose':'#ffe4e1',
    'moccasin':'#ffe4b5',
    'navajowhite':'#ffdead',
    'navy':'#000080',
    'oldlace':'#fdf5e6',
    'olive':'#808000',
    'olivedrab':'#6b8e23',
    'orange':'#ffa500',
    'orangered':'#ff4500',
    'orchid':'#da70d6',
    'palegoldenrod':'#eee8aa',
    'palegreen':'#98fb98',
    'paleturquoise':'#afeeee',
    'palevioletred':'#db7093',
    'papayawhip':'#ffefd5',
    'peachpuff':'#ffdab9',
    'peru':'#cd853f',
    'pink':'#ffc0cb',
    'plum':'#dda0dd',
    'powderblue':'#b0e0e6',
    'purple':'#800080',
    'red':'#ff0000',
    'rosybrown':'#bc8f8f',
    'royalblue':'#4169e1',
    'saddlebrown':'#8b4513',
    'salmon':'#fa8072',
    'sandybrown':'#f4a460',
    'seagreen':'#2e8b57',
    'seashell':'#fff5ee',
    'sienna':'#a0522d',
    'silver':'#c0c0c0',
    'skyblue':'#87ceeb',
    'slateblue':'#6a5acd',
    'slategray':'#708090',
    'slategrey':'#708090',
    'snow':'#fffafa',
    'springgreen':'#00ff7f',
    'steelblue':'#4682b4',
    'tan':'#d2b48c',
    'teal':'#008080',
    'thistle':'#d8bfd8',
    'tomato':'#ff6347',
    'turquoise':'#40e0d0',
    'violet':'#ee82ee',
    'wheat':'#f5deb3',
    'white':'#ffffff',
    'whitesmoke':'#f5f5f5',
    'yellow':'#ffff00',
    'yellowgreen':'#9acd32'
}
def parseStyle(s):
    """Create a dictionary from the value of an inline style attribute"""
    return dict([i.split(":") for i in s.split(";") if len(i)])
def formatStyle(a):
    """Format an inline style attribute from a dictionary"""
    return ";".join([":".join(i) for i in a.iteritems()])
def isColor(c):
    """Determine if its a color we can use. If not, leave it unchanged."""
    if c.startswith('#') and (len(c)==4 or len(c)==7):
        return True
    if c in svgcolors.keys():
        return True
    #might be "none" or some undefined color constant or rgb()
    #however, rgb() shouldnt occur at this point
    return False
def parseColor(c):
    """Creates a rgb int array"""
    if c in svgcolors.keys():
        c=svgcolors[c]
    if c.startswith('#') and len(c)==4:
        c='#'+c[1:2]+c[1:2]+c[2:3]+c[2:3]+c[3:]+c[3:]
    elif c.startswith('rgb('):
        # remove the rgb(...) stuff
        tmp = c.strip()[4:-1]
        numbers = [number.strip() for number in tmp.split(',')]
        converted_numbers = []
        if len(numbers) == 3:
            for num in numbers:
                if num.endswith(r'%'):
                    converted_numbers.append( int(int(num[0:-1])*255/100))
                else:
                    converted_numbers.append(int(num))
            return tuple(converted_numbers)
        else:    
            return (0,0,0)
        
    r=int(c[1:3],16)
    g=int(c[3:5],16)
    b=int(c[5:],16)
    return (r,g,b)
def formatColoria(a):
    """int array to #rrggbb"""
    return '#%02x%02x%02x' % (a[0],a[1],a[2])
def formatColorfa(a):
    """float array to #rrggbb"""
    return '#%02x%02x%02x' % (int(round(a[0]*255)),int(round(a[1]*255)),int(round(a[2]*255)))
def formatColor3i(r,g,b):
    """3 ints to #rrggbb"""
    return '#%02x%02x%02x' % (r,g,b)
def formatColor3f(r,g,b):
    """3 floats to #rrggbb"""
    return '#%02x%02x%02x' % (int(round(r*255)),int(round(g*255)),int(round(b*255)))

_SVGNS    = 'xmlns="http://www.w3.org/2000/svg"'

if __name__ == '__main__':
    """ simple test 
    If we decide to use this converter, 
    We need to define a full test set on many examples
    Think How to compare the pdf results ?
    """
    if len(sys.argv) == 2:
        if os.path.isfile(sys.argv[1]):
            print convert_code(open(sys.argv[1]).read())
        else:
            print 'input file not found!'
    else:
        print 'usage: svg2tikz <svgfile>'

    
