/*
SVG Connector Script Library

Available under the MIT License:

Copyright (c) 2009, Doug Schepers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

/* Modified by L. Fournier Copyright (c) 2011, Rockwellcollins

Available under the GNUv3 License:

The initial Doug Schepers's library has been :
- simplified because we do not currently need the 'port' concept
- extented because we need 'AND' or 'OR' connectors
*/

const svgns   = 'http://www.w3.org/2000/svg';
const xlinkns = 'http://www.w3.org/1999/xlink';
const xhtmlns = 'http://www.w3.org/1999/xhtml';

/* Globals !*/
var nodeArray = [];

if (typeof($)=='undefined') { 
  function $(id) { return document.getElementById(id.replace(/^#/,'')); } 
}

/*
* initialize
*/

function is_gecko() {
  var str = navigator.userAgent;
  //alert (str);

  // Webkit
  //Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.651.0 Chrome/10.0.651.0 Safari/534.17
  if (str.match('AppleWebKit')) { return true; }

  // Opera
  if (str.match('Presto')) { return true; }

  // FF4
  //Mozilla/5.0 (Windows NT 5.1; rv:2.0b11pre) Gecko/20110201 Firefox/4.0b11pre
  var gecko = str.replace(/^Mozilla.*rv:|\).*$/g, '' ) || ( /^rv\:|\).*$/g, '' );
  if (gecko.substring(0,3) == '2.0') { return true; } 

  return false;
}

window.onload = function () {
  if (!is_gecko()) alert ('This is tested on Firefox4 and Chromium !'); 
  //alert (screen.width + ' ' + screen.height);
  //$('.area').addEventListener("onfocus",enterFocus,false);  

  if (false) { // LAB!
    if (navigator.geolocation) {  
      //var geolocation = Components.classes["@mozilla.org/geolocation;1"].getService(Components.interfaces.nsIDOMGeoGeolocation);  
      //navigator.geolocation.getCurrentPosition(function(position) {  
      //do_something(position.coords.latitude, position.coords.longitude);  
      //}); 
      var timeoutVal = 10 * 1000 * 1000;
      navigator.geolocation.watchPosition(showPositionOnMap, errorMessage,
					  { enableHighAccuracy: true, timeout: timeoutVal, maximumAge: 0 });
    } else {  
      alert('Geolocation services are not supported by your browser.');  
    }  
  }

};
 
function showPositionOnMap(position) {
  //var geoCoords = new GLatLng(position.coords.latitude, position.coords.longitude);
  //map.addOverlay(new GMarker(geoCoords));
  alert (position.coords.latitude + ' ' + position.coords.longitude);
}

function errorMessage() {
  alert ('KO');
}

function do_something() {
  alert ('OK');
}

function enterFocus(evt) {
  alert ('focus');
}

function enterNode(evt) {
  var nod = evt.target;
  var nod0 = nod;
  while (nod.parentNode.id != '.nodes') { nod = nod.parentNode; } 
  if (nod.hasAttribute('href')) { 
    var href = nod.getAttribute('href');
    var rev = $('.rev').firstChild.nodeValue;
    if (nod0.parentNode.id == 'attachid') { 
      var param = 'gid=' + href + '&rev=' + rev;
      window.open(get_base_url() + '/load_pdf?' + param, 'neutral', 'chrome,scrollbars=yes');
    } else {
      var param = '?@' + href + ':' + rev;
      document.location.replace(get_url() + param);
    } 
  }
}

function typeTextBG(evt) {
  if (evt.type == 'keypress') {
    var charCode = 0;
    if (evt.charCode) { charCode = evt.charCode; }
    else { charCode = evt.keyCode; }
    //alert (charCode);
    if (charCode == 115) { // 's'
      save_all (evt);
    } else if (charCode == 97) { // 'a'
      mode (evt);
    }
  }
}

function init_graph(noedit) { 
  //alert (screen.width + ' ' + screen.height); 1067x853
  var tab = $('.nodes').childNodes;
  for ( var i = 0; i < tab.length; i++ ) {
    if (tab[i].id) {
      new Node( tab[i].id );
      //alert (tab[i].id);
    }
  }
  //for ( var id in nodeArray ) { alert (nodeArray[id].id); }
  var xc = document.documentElement.getElementsByTagName('connector');
  for ( var i = 0, iLen = xc.length; iLen > i; i++ ) {
    var c = new Connector(xc[i]);
    c.init();
    c.draw();
  }

  //if ($('_connect').getAttribute('state') == 'off') {
  //  noedit = null;
  //  alert ('ici');
  //}

  if (noedit == null) {
    var drag = new DragDrop();
    drag.init( $('.nodes') );
    // attach document drop
    var dropbox = $('.nodes');
    //var dropbox = $('.base');
    dropbox.addEventListener("dragenter", dragenter, false);
    dropbox.addEventListener("dragover", dragover, false);
    dropbox.addEventListener("drop", drop, false);
  } else {
    $('.nodes').addEventListener("click", enterNode, false);
  }
};

/*
* output current layout - NOT USED
*/
document.onkeydown = function (evt) {
  var keyCode = null;
  if( evt == null ) {
    keyCode = window.evt.keyCode;
  } else {
    keyCode = evt.keyCode;
  }
  if ( 49 == keyCode ) { // '1'
    var o = 'Window:'+ window.innerWidth + ':' + window.innerHeight + '\n';
    for ( var id in nodeArray ) {
      var ea = nodeArray[id];
      o += id + ' (x: '+parseInt(ea.x)+ ', y: ' + parseInt(ea.y) + ' ' + ' tx: '+parseInt(ea.tx)+ ', ty: ' + parseInt( ea.ty) + ')\n';
    }
    //alert(o);
  }
};

function Node( id ) {
  this.id           = null;
  this.el           = null;
  this.role         = null;
  this.title        = null;
  this.connectors   = [];
  this.x            = 0;
  this.y            = 0;
  this.tx           = 0;
  this.ty           = 0;
  return this.init( id );
};

Node.prototype.init = function( id ) {
  var node = nodeArray[id];
  if ( !node ) {
    this.el = $(id);
    this.id = id;
    var brut = this.el.lastChild;
    var b = this.el.lastChild.getBBox();
    
    if (this.el.lastChild.nodeName != 'text') {
	alert (this.el.lastChild.nodeName);
    }
    //alert (id + ' ' + b.x + ' ' + b.y);

    var centroid = GetCentroid(this.el);
    this.x = centroid.x;
    this.y = centroid.y;

    var ctm = this.el.getCTM();
    this.tx = parseInt( ctm.e );
    this.ty = parseInt( ctm.f );

    // better make scrollbar than adjusting diagram size to window
    //if (this.tx > window.innerWidth) { this.tx = window.innerWidth - 50; }
    //if (this.ty > window.innerHeight) { this.ty = window.innerHeight - 50; }
    //this.el.setAttribute('transform', 'translate(' + this.tx + ',' + this.ty + ')');
    
    nodeArray[id] = this; 
    node = this;    
    this.role = this.el.getAttribute('role');  
    this.name = this.el.getAttribute('title');  

    var border = 8;
    var g = document.createElementNS(svgns, 'g');

    var shape = '';
    if (this.role == 'AGENT') {
      shape = document.createElementNS(svgns, "path");
      shape.setAttribute('fill', 'url(#.grad)');
      shape.setAttribute('filter', 'url(#.shadow)');
      shape.setAttribute('stroke', 'gray');
      var f = 8;
      var x = b.x - border;
      var y = b.y - border;
      var w = b.width + 2*border;
      var h = b.height + 2*border;
      var d = 'M'+(x+f)+','+y + 
	'l' + (w-2*f) + ',0' + 
	'l' + f +',' + (h/2) + 
	'l' + (-f) + ',' + (h/2)  + 
	'l' + (2*f-w) +',0' + 
	'l' + (-f) + ',' + (-h/2) + 'z';
      shape.setAttribute('d', d);
    } else if (this.role == 'GOAL') {
      shape = document.createElementNS(svgns, "path");
      shape.setAttribute('fill', 'url(#.grad)');
      shape.setAttribute('filter', 'url(#.shadow)');
      shape.setAttribute('stroke', 'gray');
      var x = b.x - border;
      var y = b.y - border;
      var w = b.width + 2*border;
      var h = b.height + 2*border;
      var f = 4;
      var d = 'M' + (x+2*f) + ',' + y +
	'l' + 2*w/3 + ',2' + 
	'l' + w/3 + ',-2' + 
	'l' + (-f-2) + ',' + 2*h/3 +
	'l' + (-f-2) + ',' + h/3 + 
	'l' + (-3*w/5) +',2' + 
	'l' + (-2*w/5) +',-2' + 
	'l' + (f+2) + ',' + -4*h/7 + 'z';
      shape.setAttribute('d', d); 
    } else if (this.role == 'CLASS') {
      var tab = brut.childNodes;
      var res = [];
      for (var i = 0; i < tab.length; i++) {
	if (tab[i].hasAttribute('sep')) {
	  res.push(20*i);
	}
      }
      shape = document.createElementNS(svgns, "path");
      shape.setAttribute('fill', 'url(#.grad)');
      shape.setAttribute('filter', 'url(#.shadow)');
      shape.setAttribute('stroke', 'gray');
      var x = b.x - border; var y = b.y - border;
      var w = b.width + 2*border; var h = b.height + 2*border;
      var d = 'M'+x+','+y + 'l'+w+',0' + 'l0,'+ h + 'l'+ (-w) +',0' + 'z';
      for (var i = 0; i < res.length; i++) {
	d += ' M'+x+','+(y+7+res[i]) + 'l'+w+',0'
      }
      shape.setAttribute('d', d); 
    } else if (this.role == 'ASSOCIATION') {
      shape = document.createElementNS(svgns, "path");
      shape.setAttribute('fill', 'url(#.grad)');
      shape.setAttribute('filter', 'url(#.shadow)');
      shape.setAttribute('stroke', 'gray');
      var x = b.x - border;
      var y = b.y - border;
      var w = b.width + 2*border;
      var h = b.height + 2*border;
      var d = 'M' + x + ',' + y + 
	'm' + w/2 + ',0' + 
	'l' + w/2 + ',' + h/2 + 
	'l'+ (-w/2) + ',' + h/2 + 
	'l'+ (-w/2) +',' + (-h/2) + 'z';
      shape.setAttribute('d', d);
    } else if (this.role == 'ENTITY') {
      shape = document.createElementNS(svgns, "path");
      shape.setAttribute('fill', 'url(#.grad)');
      shape.setAttribute('filter', 'url(#.shadow)');
      shape.setAttribute('stroke', 'gray');
      var x = b.x - border;
      var y = b.y - border;
      var w = b.width + 2*border;
      var h = b.height + 2*border;
      d = 'M'+x+','+y + 'l'+w+',0' + 'l0,'+ h + 'l'+ (-w)+',0' + 'z';
      shape.setAttribute('d', d);
    } else if (this.role == 'REQUIREMENT') {
      shape = document.createElementNS(svgns, "rect");
      shape.setAttribute('fill', 'url(#.grad)');
      shape.setAttribute('filter', 'url(#.shadow)');
      shape.setAttribute('rx', '4' );
      shape.setAttribute('stroke', 'gray' );
      shape.setAttribute('width', b.width + 2*border);
      shape.setAttribute('height', b.height + 2*border);
      shape.setAttribute('x', b.x - border );
      shape.setAttribute('y', b.y - border);      
      shape.setAttribute('stroke-width', '3');
      shape.setAttribute('transform', 'skewX(-10)'); 
    } else if (this.role == 'EXPECTATION') {
      shape = document.createElementNS(svgns, "rect");
      shape.setAttribute('fill', 'url(#.grady)');
      shape.setAttribute('filter', 'url(#.shadow)');
      shape.setAttribute('rx', '4' );
      shape.setAttribute('stroke', 'gray' );
      shape.setAttribute('width', b.width + 2*border);
      shape.setAttribute('height', b.height + 2*border);
      shape.setAttribute('x', b.x - border );
      shape.setAttribute('y', b.y - border);      
      shape.setAttribute('stroke-width', '3');
      shape.setAttribute('transform', 'skewX(-10)'); 
    } else if (this.role == 'OBSTACLE') {
      shape = document.createElementNS(svgns, "rect");
      shape.setAttribute('fill', 'url(#.grad)');
      shape.setAttribute('filter', 'url(#.shadow)');
      shape.setAttribute('rx', '4' );
      shape.setAttribute('stroke', 'gray' );
      shape.setAttribute('width', b.width + 2*border);
      shape.setAttribute('height', b.height + 2*border);
      shape.setAttribute('x', b.x - border );
      shape.setAttribute('y', b.y - border);
      shape.setAttribute('stroke-width', '1');
      shape.setAttribute('transform', 'skewX(10)');
      shape.setAttribute('rx', '2' );
    } else {
      shape = document.createElementNS(svgns, "path");
      shape.setAttribute('fill', 'url(#.grad)');
      shape.setAttribute('filter', 'url(#.shadow)');
      shape.setAttribute('stroke', 'gray');
      var x = b.x - border;
      var y = b.y - border;
      var w = b.width + 2*border;
      var h = b.height + 2*border;
      //var d = 'M'+x+','+y + 'l'+w+',0' + 'l0,'+ h + 'l'+ (-w)+',0' + 'z';
      var d = 'M' + x + ',' + y +
	'l' + 2*w/3 + ',2' + 
	'l' + w/3 + ',-2' + 
	'l' + '2,' + 2*h/3 +
	'l' + '-2,' + h/3 + 
	'l' + (-3*w/5) +',2' + 
	'l' + (-2*w/5) +',-2' + 
	'l' + '2,' + -4*h/7 + 'z';
      shape.setAttribute('d', d);
    }
    g.appendChild(shape);
    if (this.role != null) {
      if (this.role != 'CLASS') {
	var txt = document.createElementNS(svgns, 'text');
	var content = document.createTextNode(this.role);
	if (this.role == 'OBSTACLE') {
	  txt.setAttribute('x', "-6");
	} 
	txt.setAttribute('y', "-14");
	txt.setAttribute('fill', 'gray');
	txt.setAttribute('style', 'font-family:Arial;font-size:3pt;');
	//txt.setAttribute('font-size','60pt'); does not work on FF
	txt.appendChild(content);
	g.appendChild(txt);
      }
      var txt1 = document.createElementNS(svgns, 'text');
      var content1 = document.createTextNode(this.name);
      txt1.setAttribute('x', b.width-(this.name.length*5));
      txt1.setAttribute('y', b.height-8);
      txt1.setAttribute('fill', 'white');
      txt1.setAttribute('style', 'font-family:Arial;font-size:5pt;font-weight:bold;');
      txt1.appendChild(content1);
      g.appendChild(txt1);
    }
    // Attachment
    if (this.el.hasAttribute('attach')) {
      g.appendChild(attach_icon(b.width));
    } 
    this.el.insertBefore( g ,this.el.firstChild);
    var g1 = document.createElementNS(svgns, 'g');
    g1.setAttribute('display', 'none');
    var fo = document.createElementNS(svgns, 'foreignObject');

    var xa = b.x + b.width/2 - 100;
    var ya = b.y + b.height/2 - 50;
    var wa = 200;
    var ha = 100;
    //var xa = b.x - 2*border;
    //var ya = b.y - 2*border;
    //var wa = b.width + 4*border;
    //var ha = b.height + 4*border;
    
    fo.setAttribute('width', wa);
    fo.setAttribute('height', ha);
    fo.setAttribute('x', xa);
    fo.setAttribute('y', ya);
    var ta = document.createElementNS(xhtmlns, 'textarea');
    ta.setAttribute('style','background-color: lightyellow; padding:1px 1px 1px 1px; border:1px solid #ccc');
    ta.setAttribute('onblur', 'blur_node(this);');
    ta.setAttribute('onfocus', 'focus_node(this);');
    ta.setAttribute('focusable', 'true');
    ta.setAttribute('tabindex', '1'); // !!! why
    //ta.setAttribute('onclick', 'alert(\'ici\');this.focus();this.select();'); 
    ta.setAttribute('spellcheck','false');
    //ta.setAttribute('autofocus', 'true');
    ta.setAttribute('style','resize:none; border:1px solid #ccc;width:' + (wa-2)+ 'px;height:' + (ha-3)+ 'px'); 
    ta.value = this.el.getAttribute( 'label');
    
    fo.appendChild(ta);
    g1.appendChild(fo);
    if (this.role != null) {
      var txt = document.createElementNS(svgns, 'text');
      var content = document.createTextNode(this.role);
      txt.appendChild(content);
      txt.setAttribute('fill', 'gray');
      txt.setAttribute('x', xa);
      txt.setAttribute('y', ya);
      txt.setAttribute('style', 'font-family:Arial;font-size:5pt;');
      g1.appendChild(txt);
    }
    this.el.appendChild(g1);
  }
  return node;
};

function attach_icon(w) {
  var tt = document.createElementNS(svgns, 'g');
  tt.setAttribute('transform', 'translate(' + (w+12) + ',-20) scale(0.32)');
  tt.setAttribute('class', 'attach');
  tt.setAttribute('id', 'attachid');
  var tt2 = document.createElementNS(svgns, 'rect');
  tt2.setAttribute('width', '42');
  tt2.setAttribute('fill', 'none');
  tt2.setAttribute('height','47');
  tt.appendChild(tt2);
  var tt1 = document.createElementNS(svgns, 'path');
  tt1.setAttribute('stroke-linecap', 'round');
  tt1.setAttribute('fill', 'none');
  tt1.setAttribute('stroke','#6bc62e');
  tt1.setAttribute('stroke-width','3');
  tt1.setAttribute('d',get_attach());
  tt.appendChild(tt1);
  var tt3 = document.createElementNS(svgns, 'title');
  tt3.appendChild(document.createTextNode('attached PDF document'));
  tt.appendChild(tt3);
  return tt;
} 

function save_attach() {
  var el = $('fileElem');
  if (el) {
    el.click();
  }
}

function new_attach(files,gid,nod) {
  for (var i = 0; i < files.length; i++) {
    var file = files[i];
    if (typeof gid == 'undefined') {
      gid = $('.gid').firstChild.nodeValue;
    }
    var fD = new FormData();
    fD.append('gid', gid);
    fD.append('user', $('.user').firstChild.nodeValue);
    fD.append('ip', $('.ip').firstChild.nodeValue);
    fD.append('g', file);
    fD.append('typ', file.type);    
    var xhr = new XMLHttpRequest();
    xhr.upload.addEventListener("progress", uploadProgress, false);
    xhr.addEventListener("load", uploadComplete, false);
    xhr.addEventListener("error", uploadFailed, false);
    xhr.addEventListener("abort", uploadCanceled, false);
    xhr.open('POST', get_base_url() + '/new_attach');
    xhr.send(fD);
    var b = nod.firstChild.nextSibling.getBBox();
    nod.firstChild.appendChild(attach_icon(b.width));
  }
}

function uploadProgress(evt) {
  if (evt.lengthComputable) {
    var percentComplete = Math.round(evt.loaded * 100 / evt.total);
    $('bar').parentNode.setAttribute('display','inline');
    $('prg').firstChild.nodeValue = percentComplete.toString() + '%';
    $('bar').setAttribute('width',percentComplete);
  } else {
    $('prg').firstChild.nodeValue = 'unable to compute';
  }
}

function uploadComplete(evt) {
  $('prg').firstChild.nodeValue = '100%';
  $('bar').setAttribute('width',100);
  setTimeout("clearbar()",1000); 
  //alert(evt.target.responseText);
}

function clearbar() {
  $('bar').parentNode.setAttribute('display','none');
}

function uploadFailed(evt) {
  alert("There was an error attempting to upload the file.");
}

function uploadCanceled(evt) {
  alert("The upload has been canceled by the user or the browser dropped the connection.");
}

function get_attach() {
  return 'm21.615,8.81l-11.837,19.94l-0.349,2.68l0.582,2.67l1.28,1.746l5.122,3.14l2.79,0.35l2.095,-0.46l1.746,-1.047l1.746,-2.095l11.990,-20.838l0.698,-2.91l-0.465,-2.444l-1.28,-2.095l-1.746,-0.931l-1.979,-0.349l-1.629,0.349l-1.513,0.582l-1.746,1.28l-1.047,1.746l-9.08,16.065l-0.698,2.44l0.465,1.98l0.931,1.047l1.746,0.349l1.629,-0.814l1.164,-1.164l1.28,-1.63l4.656,-7.79l0.46,-0.81';
}

function GetCentroid(el) {
  var centroid = document.documentElement.createSVGPoint();
  var bbox = el.getBBox();
  centroid.x = bbox.x + (bbox.width/2);
  centroid.y = bbox.y + (bbox.height/2);
  return centroid;
};

function Connector( el ) {
  this.el     = el;
  this.path   = null;
  this.circle = null;
  this.n1     = null;
  this.n2     = [];
  this.b1     = null;
  this.b2     = [];
  this.type   = null;
};

Connector.prototype.init = function() {
  var n1id = this.el.getAttribute('n1').replace('#','');
  this.n1 = nodeArray[n1id];
  this.n1.connectors.push( this );
  this.b1 = $(n1id).lastChild.previousSibling.getBBox();
  //this.b1 = $(n1id).lastChild.getBBox();
  //alert (this.b1.width);
  var n2ids = this.el.getAttribute('n2').replace('#','');
  var ll = n2ids.split(':');
  for (var i=0; i<ll.length; i++) {
    var c2 = nodeArray[ll[i]];
    c2.connectors.push( this );
    this.n2.push( c2 );
    this.b2.push( $(ll[i]).lastChild.previousSibling.getBBox());
  }
  if (this.el.hasAttribute('type')) {
    this.type = this.el.getAttribute('type')
  }
};

Connector.prototype.draw = function() {
  var x1 = this.n1.x + this.n1.tx;
  var y1 = this.n1.y + this.n1.ty;
  var h1 = 10 + this.b1.height/2;
  var l1 = 10 + this.b1.width/2; 
  //alert (window.focusNode);
  if (window.focusNode != null) {
    if (window.focusNode.parentNode.id == this.n1.id) {
      h1 = 50; l1 = 100;
    }
  }

  var x2 = 0;
  var y2 = 0;
  var n = this.n2.length;
  for (var i=0; i<n; i++) {
    x2 += this.n2[i].x + this.n2[i].tx;
    y2 += this.n2[i].y + this.n2[i].ty;
  }
  x2 = x2/n;
  y2 = y2/n;

  if (x1 == x2) {
    if (y1<y2) {
      y1 += h1;
    } else {
      y1 -= h1;
    }
  } else if (y1 == y2) {
    if (x1<x2) {
      x1 += l1;
    } else {
      x1 -= l1;
    }
  } else {
    var Q = x1-x2;
    var R = y1-y2;
    var P = Q/R;
    if (Math.abs(P) < l1/h1) {
      if (R<0) {
	y1 += h1; x1 += h1*P;
      } else {
	y1 -= h1; x1 -= h1*P;
      }
    } else {
      if (Q<0) {
	x1 += l1; y1 += l1/P;
      } else {
	x1 -= l1; y1 -= l1/P;
      }
    }
  }
  // this is not exactly the center because (x1,y1) is modified and not yet (x2,y2)
  // but the result seems to be nice
  x2 = (x1+x2)/2; y2 = (y1+y2)/2;

  var d = '';
  if ( !this.path ) {
    this.path = document.createElementNS(svgns, 'path');
    this.path.setAttribute('fill', 'none');
    this.path.setAttribute('stroke', 'gray');
    this.path.setAttribute('stroke-width', '2');
    if (this.type == 'conflict') {
      this.path.setAttribute('marker-mid', 'url(#.conflict)');
    } else if (this.type) {
      this.path.setAttribute('marker-start', 'url(#.simple_start)'); 
      this.path.setAttribute('marker-end', 'url(#.simple_end)');
    } else {
      this.path.setAttribute('marker-end', 'url(#.arrow)');
    }
    this.el.parentNode.appendChild(this.path);
    if (n>1) {
      this.circle = document.createElementNS(svgns, 'circle');
      this.circle.setAttribute('fill', 'url(#.gradyellow)');
      //this.circle.setAttribute( 'fill', 'black');
      this.circle.setAttribute('r', '6' );
      this.circle.setAttribute('stroke', 'gray');
      this.circle.setAttribute('stroke-width', '1');
      this.el.parentNode.appendChild( this.circle );
    }
  } 
  for (var i=0; i<this.n2.length; i++) {
    var x3 = this.n2[i].x + this.n2[i].tx;
    var y3 = this.n2[i].y + this.n2[i].ty;
    var h2 = 10 + this.b2[i].height/2;
    var l2 = 10 + this.b2[i].width/2;
    if (window.focusNode != null) {
      if (window.focusNode.parentNode.id == this.n2[i].id) {
	h2 = 50; l2 = 100;
      }
    }
    if (x3 == x2) {
      if (y3<y2) {
	y3 += h2;
      } else {
	y3 -= h2;
      }
    } else if (y3 == y2) {
      if (x3<x2) {
	x3 += l2;
      } else {
	x3 -= l2;
      }
    } else {
      var Q = x3-x2;
      var R = y3-y2;
      var P = Q/R;
      if (Math.abs(P) < l2/h2) {
	if (R<0) {
	  y3 += h2; x3 += h2*P;
	} else {
	  y3 -= h2; x3 -= h2*P;
	}
      } else {
	if (Q<0) {
	  x3 += l2; y3 += l2/P;
	} else {
	  x3 -= l2; y3 -= l2/P;
	}
      }
    }
    d += 'M' + x3 + ',' + y3 + 'L' + x2 + ',' + y2;  
  }
  d += ' ' + x1 + ',' + y1;  
  this.path.setAttribute( 'd', d );
  if (n>1) {
    this.circle.setAttribute( 'cx', x2);
    this.circle.setAttribute( 'cy', y2);
  }
};

function GetCentroid(el) {
  // note: this isn't really a centroid!
  var centroid = document.documentElement.createSVGPoint();
  var bbox = el.getBBox();
  centroid.x = bbox.x + (bbox.width/2);
  centroid.y = bbox.y + (bbox.height/2);
  return centroid;
};

/*
* drag & drop functions
*/
function DragDrop () {
  this.dragEl       = null;
  this.targetEl     = null;
  this.m            = null;
  this.p            = null;
  this.offset       = null;
  this.tx           = null;
  this.ty           = null;
  this.d            = false;
};

DragDrop.prototype.init = function( draggable ) {
  var dragdrop = this;
  //draggable.addEventListener("click", enterNode, false);
  draggable.addEventListener('mousedown', function( event ){ dragdrop.grab( event ); }, false);
  document.documentElement.addEventListener('mousemove', function( event ){ dragdrop.drag( event ); }, false);
  document.documentElement.addEventListener('mouseup', function( event ){ dragdrop.drop( event ); }, false);
  this.p = document.documentElement.createSVGPoint();
  this.offset = document.documentElement.createSVGPoint();
  window.focusNode = null;
};

function update_connectors(node) {
  //alert (node.id);
  var co = nodeArray[node.id].connectors;
  for ( var i = 0; co.length > i; i++ ) {
    co[i].draw();
  }
}

DragDrop.prototype.grab = function( evt ) {
  if (!evt) var evt = window.event;
  var nod = evt.target; 
  var nod0 = nod;
  while (nod.parentNode.id != '.nodes') { nod = nod.parentNode; } 
  var fo = nod.lastChild;
  if (evt.shiftKey) {
    if (window.focusNode) {
      alert ('update');
      update_g();
    }
    if (fo.getAttribute('display') == 'none') {
      fo.setAttribute('display','inline');
      window.focusNode = fo;
      update_connectors(nod);
      var ta = fo.firstChild.firstChild;
      ta.select();
      ta.focus();
      //document.activeElement = ta;
      //alert (document.activeElement);
      //alert (ta.selectionStart);
      //var range = ta.createRange();
      //range.collapse(true);
      //range.moveEnd('character', 0);
      //range.moveStart('character', 0);
      //range.select();
    } else {
      alert ('off');
      window.focusNode = null;
      fo.setAttribute('display','none');
      update_connectors(nod);
    }
  }
  if (evt.detail == 2) { // enterNode from edit
    if (fo.getAttribute('display') != 'inline') {
      if (nod.hasAttribute('href')) {
	if (nod0.parentNode.id == 'attachid') { 
	  var rev = $('.rev').firstChild.nodeValue;
	  var pa = 'gid=' + nod.getAttribute('href') +'&rev='+ $('.rev').firstChild.nodeValue;
	  window.open(get_base_url() + '/load_pdf?' + pa, 'neutral', 'chrome,scrollbars=yes');
	} else {
	  save_and_reload (get_url(),gid(),get_layout(),$('.area').value,nod.getAttribute('href'));
	}
      } else {
	//save_session(); // a tester !
	new_graph (nod);
      }
      this.dragEl = null;
    }
  } else {
    this.dragEl = nod; 
  }
  if( this.dragEl ) {
    //alert ('AA:'+this.dragEl.id);
    this.dragEl.parentNode.appendChild( this.dragEl );
    this.dragEl.setAttribute( 'pointer-events', 'none');
    this.m = document.documentElement.getScreenCTM();
    this.p.x = evt.clientX;
    this.p.y = evt.clientY;
    this.p = this.p.matrixTransform( this.m.inverse() );
    var ctm = this.dragEl.getCTM();
    this.offset.x = this.p.x - parseInt( ctm.e );
    this.offset.y = this.p.y - parseInt( ctm.f );
  }
};

DragDrop.prototype.drag = function( event ) {
  if( this.dragEl ) {
    this.d = true;
    var node = nodeArray[ this.dragEl.id ];
    this.m = document.documentElement.getScreenCTM();
    this.p.x = event.clientX;
    this.p.y = event.clientY;
    this.p = this.p.matrixTransform( this.m.inverse() );
    this.p.x -= this.offset.x;
    this.p.y -= this.offset.y;
    this.tx = this.p.x;
    this.ty = this.p.y;
    this.dragEl.setAttribute('transform', 'translate(' + this.tx + ',' + this.ty + ')');
    var node = nodeArray[ this.dragEl.id ];
    if (node) { 
      node.tx = this.p.x;
      node.ty = this.p.y;
      for ( var i = 0; node.connectors.length > i; i++ ) {
	node.connectors[i].draw();
      }
    }
  }
};

DragDrop.prototype.drop = function() {
  if (this.dragEl) {
    if (this.d) {
      change_title(true);
      if ($('.canvas').getAttribute('unsaved') == 'no') {
	$('.canvas').setAttribute('unsaved','layout');
      }
      this.d = false;
    }
    this.dragEl.setAttribute('pointer-events', 'all');
    this.dragEl = null;
  }
};
//////////////////

function DragDrop1 () {
  this.dragEl       = null;
  this.targetEl     = null;
  this.m            = null;
  this.p            = null;
  this.offset       = null;
  this.tx           = null;
  this.ty           = null;
};

DragDrop1.prototype.init = function( draggable ) {
  var dragdrop = this;
  //draggable.addEventListener("click", enterNode, false);
  draggable.addEventListener('mousedown', function( event ){ dragdrop.grab( event ); }, false);
  document.documentElement.addEventListener('mousemove', function( event ){ dragdrop.drag( event ); }, false);
  document.documentElement.addEventListener('mouseup', function( event ){ dragdrop.drop( event ); }, false);
  this.p = document.documentElement.createSVGPoint();
  this.offset = document.documentElement.createSVGPoint();
  window.focusNode = null;
};

DragDrop1.prototype.grab = function( evt ) {
  var nod = evt.target; 
  while (nod.parentNode.id != '.nodes') { nod = nod.parentNode; } 
  this.dragEl = nod;  
  if( this.dragEl ) {
    //alert (this.dragEl.id);
    //this.dragEl.parentNode.appendChild( this.dragEl );
    this.dragEl.setAttribute( 'pointer-events', 'none');
    //this.m = document.documentElement.getScreenCTM();
    //this.p.x = evt.clientX;
    //this.p.y = evt.clientY;
    //this.p = this.p.matrixTransform( this.m.inverse() );
    var ctm = this.dragEl.getCTM();
    //this.offset.x = this.p.x - parseInt( ctm.e );
    //this.offset.y = this.p.y - parseInt( ctm.f );
  }
};

DragDrop1.prototype.drag = function( event ) {
  if( this.dragEl ) {
    var node = nodeArray[ this.dragEl.id ];
    //this.m = document.documentElement.getScreenCTM();
    //this.p.x = event.clientX;
    //this.p.y = event.clientY;
    //this.p = this.p.matrixTransform( this.m.inverse() );
    //this.p.x -= this.offset.x;
    //this.p.y -= this.offset.y;
    //this.tx = this.p.x;
    //this.ty = this.p.y;
    //this.dragEl.setAttribute('transform', 'translate(' + this.tx + ',' + this.ty + ')');
  }
};

DragDrop1.prototype.drop = function( evt ) {
  if (this.dragEl) {
    alert ('drop');
    var nod = evt.target; 
    if (nod.nodeName != 'svg') {
      while (nod.parentNode.id != '.nodes') { nod = nod.parentNode; } 
      this.dragEl.setAttribute('pointer-events', 'all');
      //alert (this.dragEl.id + '|' + nod.id);
    }
  }
  this.dragEl = null;
};


/////////////////
function get_layout() {
  var lout = '';
  for ( var id in nodeArray ) {
    var eNode = nodeArray[id];
    lout += id + ':' + eNode.tx + ':' + eNode.ty + ' ';
  }
  return (lout);
}

function short_content(content) {
  if (content.length >= 35) {
    return (content.substring(0,33) + '...');
  }
  return (content);
  //xml.sax.saxutils.escape(sh) + '&#160;'.join(['' for x in xrange(35-len(content))])
}

function user_ip() {
  return '&user='+ $('.user').firstChild.nodeValue + '&ip='+ $('.ip').firstChild.nodeValue;
}

function gid() {
  return $('.gid').firstChild.nodeValue;
}

/*
* Ajax functions
*/
function new_graph (nod) {
  var fD = new FormData();
  fD.append('parent', gid());
  fD.append('name', nod.id);
  fD.append('user', $('.user').firstChild.nodeValue);
  fD.append('ip', $('.ip').firstChild.nodeValue);
  fD.append('g', get_layout() + '\n' + $('.area').value);
  var ai = new post(true,get_base_url() + '/new_graph', fD, function(res) {
		      document.location.replace(get_url() + '?@' + res);
		    });
  ai.doPost();
}

function save_up (evt) {
  var node = $('.parent');
  if (node.hasAttribute('href')) { 
    save_and_reload (get_url(),gid(),get_layout(),$('.area').value,node.getAttribute('href'));
  }
}

function go_up (evt) {
  var node = $('.parent');
  if (node.hasAttribute('href')) { 
    var fhref = '@' + node.getAttribute('href') + ':' + $('.rev').firstChild.nodeValue.substring(0,15);
    //alert (fhref);
    document.location.replace(get_url() + '?' + fhref);
  }
}

function load_item (e) {
  if (e.target.nodeName == 'tspan') {
    var node = e.target;
    if (!node.hasAttribute('gid')) {
      node = node.parentNode;
    }
    document.location.replace(get_url() + '/edit?@' + node.getAttribute('gid'));
  } 
}

function record_tag () {
    param = '&tag=' + escape($('.tag').value) + '&rev=' + $('.rev').firstChild.nodeValue;
    var aj = new ajax_get(true,get_base_url() + '/save_tag?gid=' + user_ip() + param, function(res) {
	    var val = $('.tag').value;
	    $('.tag').value = '';
	    if (res) {
		alert (res);
	    } else {
		alert ('\' ' + val + '\' tag created on revision:\n' + $('.rev').firstChild.nodeValue);
	    }
	});
    aj.doGet();
    
}

function save_all (e) {
  if (e.target.nodeName == 'tspan') {
    document.location.replace(get_url() + '?' + e.target.getAttribute('rev'));
  } else if (e.target.nodeName == 'input') {
  } else {
    if ($('.canvas').getAttribute('unsaved') == 'all') {
      save_content ();
    } else if ($('.canvas').getAttribute('unsaved') == 'layout') {
      save_layout ();
    }
    $('.canvas').setAttribute('unsaved','no');
    change_title(false);
  }
}

function save_layout () {
  var fD = new FormData();
  fD.append('gid', gid());
  fD.append('user', $('.user').firstChild.nodeValue);
  fD.append('ip', $('.ip').firstChild.nodeValue);
  fD.append('lout', get_layout());
  var ai = new post(true,get_base_url() + '/save_layout',fD, function(res) {
		      $('.rev').firstChild.nodeValue = res;
		    });
  ai.doPost();
};

function save_content () {
  var fD = new FormData();
  fD.append('gid', gid());
  fD.append('user', $('.user').firstChild.nodeValue);
  fD.append('ip', $('.ip').firstChild.nodeValue);
  fD.append('lout', get_layout());
  fD.append('content', $('.area').value);
  var ai = new post(true,get_base_url() + '/save_content',fD,function(res) {
		      $('.rev').firstChild.nodeValue = res;
		    });
  ai.doPost();
};

function save_and_reload (url,gid,lout,content,href) {
  var fD = new FormData();
  fD.append('gid', gid);
  fD.append('user', $('.user').firstChild.nodeValue);
  fD.append('ip', $('.ip').firstChild.nodeValue);
  fD.append('lout', lout); 
  fD.append('content', content);
  var ai = new post(true,get_base_url() + '/save_content?',fD,function(res) {
		      document.location.replace(url + '?@' + href);
		    });
  ai.doPost();
};

function get_url () { 
  var s = new String(document.location);
  var url = s;
  url = url.replace(/\?.*$/,'');
  //alert (url);
  return (url);
};

function get_base_url () { 
  var url = get_url().replace(/\/[^\/]*$/,'');
  //alert (url);
  return (url);
};

function save_session () { 
  var mode = 'txt'
  if ($('.textarea').getAttribute('display') == 'none') { mode = 'graph'; } 
  var user = $('.user').firstChild.nodeValue;
  var s = new String(document.location);
  var aj = new ajax_get(true,get_base_url() + '/save_session?mode='+ mode + '&user=' + user, function(res){});
  aj.doGet(); 
};

function ajax_get(txt,url, cb) {
  var req = new XMLHttpRequest();
  req.onreadystatechange = processRequest;  
  function processRequest () {
    if (req.readyState == 4) {
      if (req.status == 200 || req.status == 0) {
	if (cb) {
	  if (txt) {
	    cb(req.responseText);
	  } else {
	    cb(req.responseXML);
	  }
	}
      } else {
	alert('Error Get status:'+ req.status);
      }
    }
  }
  this.doGet = function() {
    req.open('GET', url);
    req.send(null);
  }
};

function post(txt,url,data,cb) {
  var req = new XMLHttpRequest();
  req.onreadystatechange = processRequest;
  function processRequest () {
    if (req.readyState == 4) {
      if (req.status == 200) {
	if (cb) {
	  if (txt) {
	    cb(req.responseText);
	  } else {
	    cb(req.responseXML);
	  }
	}
      } else {
	alert('Error Post status:'+ req.status);
      }
    }
  }
  this.doPost = function() {
    req.open('POST', url,true);
    req.send(data);
  }  
};

//////

function mode (e) {
  var a = $('.wmode'); var b = $('.rmode'); var aa = $('.canvas'); var bb = $('.textarea');
  if (aa.getAttribute('display') == 'none') {
    a.setAttribute('display','inline'); b.setAttribute('display','none');
    aa.setAttribute('display','inline'); bb.setAttribute('display','none');
    if ($('.canvas').getAttribute('updated') == 'no') {
      update_graph();
      $('.canvas').setAttribute('updated','yes');
    } else {
      if ($('.canvas').getAttribute('jsdone') == 'no') {
	//nodeArray = [];
	init_graph();
	$('.canvas').setAttribute('jsdone','yes');
      }
    }
  } else {
    a.setAttribute('display','none'); b.setAttribute('display','inline');
    aa.setAttribute('display','none'); bb.setAttribute('display','inline');
  }
  save_session();
};

function change_title(way) {
  var old = $('.title').firstChild.nodeValue;
  if (way) {
    if (old.substring(0,1) != '*') {
      $('.title').firstChild.nodeValue = '*'+old;
    }
  } else {
    if (old.substring(0,1) == '*') {
      $('.title').firstChild.nodeValue = old.substring(1);
    }
  }
}

function change_textarea() {
  change_title(true);
  $('.canvas').setAttribute('updated','no');
  $('.canvas').setAttribute('unsaved','all');
};

function update_graph() {
  $('.content').firstChild.nodeValue = short_content($('.area').value); 
  var fD = new FormData();
  fD.append('gid', gid());
  fD.append('content', $('.area').value);
  var ai = new post(false,get_base_url() + '/update_graph',fD,function(res) {
		      var place = $('.canvas');
		      //alert((new XMLSerializer()).serializeToString(res));
		      place.replaceChild(cl_xml(res),place.firstChild);
		      nodeArray = [];
		      init_graph();
		    });
  ai.doPost(); 
}

function cl_xml(d){
  return document.importNode(d.documentElement.cloneNode(true),true);
}

function update_url(e,edit) {
  var target = '';
  if (e.target.id == '.rev') {
    target = $('.rev').firstChild.nodeValue;
  } else if (e.target.id == '.gid'){
    target = '@' + gid();
  } else if (e.target.id == '.content'){
    target = $('.area').value.replace(/#/g,'$');
    target = target.replace(/\n/g,'\\n');
  } 
  if (edit) {
    document.location.replace(get_url() + '?' + target);
  } else {
    $('linkstring').parentNode.setAttribute('display','inline');
    $('linkstring').value = get_url() + '?' + target;
    $('linkstring').select();$('linkstring').focus();
    e.stopPropagation();
  }
}

function closelink() {
  $('linkstring').parentNode.setAttribute('display','none');
}

function typeText(e) {
  if (e.type == 'keypress') {
    if (e.charCode) { var charCode = e.charCode; }
    else { var charCode = e.keyCode; }
    if (charCode == 46) {
      window.txt = ''; 
      stopTyping(e); 
    } else if (charCode == 8) { //backspace key
      window.txt = window.txt.substring(0,window.txt.length-1);
    } else if (charCode == 10 || charCode == 13) { //return key
      stopTyping(e); 
    } else if (charCode > 31 && charCode != 127 && charCode < 65535) {
      window.txt += String.fromCharCode(charCode);
    }
  }
  //window.tg.firstChild.nodeValue = window.txt;
  e.preventDefault();
}

function initTyping(e) {
  if (!window.typeinit) {
    window.txt = window.tg.firstChild.nodeValue;
    window.src = window.tg.firstChild.nodeValue;
    document.documentElement.addEventListener('keypress',typeText,false);
    document.documentElement.addEventListener('click',stopTyping,false);  
    window.typeinit = true;
  }
  e.stopPropagation();
}


function stopTyping(e) {
  document.documentElement.removeEventListener('keypress',typeText,false);
  document.documentElement.removeEventListener('click',stopTyping,false);
  if (window.src != window.txt) {
    if (window.typeinit) { 
      alert ('stop');
    }
  }
  window.typeinit = false;
}

function blur_node(ele) {
  if (window.focusNode) { 
    update_g();
  }
}

function focus_node(ele) {
  //window.focusNode = ele; 
  //ele.parentNode.setAttribute('display','inline');
  //alert ('focus');
}

function edit_node_old(e,mode) {
  if (typeof window.typeinit == 'undefined') window.typeinit = false;
  if (mode) {
    window.typeinit = false;
  } else {
    if (e.target.nodeName == 'text') {
      if (!window.typeinit) {
	window.tg = e.target;
	initTyping(e);
      }
    }
  } 
}


function update_g() {
  window.focusNode.setAttribute('display','none');
  var old_area = $('.area').value;
  $('.content').firstChild.nodeValue = short_content($('.area').value); 
  var fD = new FormData();
  fD.append('name', window.focusNode.parentNode.id);
  fD.append('label', window.focusNode.firstChild.firstChild.value);
  fD.append('content', $('.area').value);
  var ai = new post(true,get_base_url() + '/update_g',fD,function(res) {
		      if (res != old_area) {
			$('.canvas').setAttribute('unsaved','all');
			change_title(true);
			$('.area').value = res;
			update_graph();
		      }
		    });
  ai.doPost();
  window.focusNode = null;  
}

function add_node(e) {
  var node = e.target.parentNode;
  while(!node.hasAttribute('id')) {
    node = node.parentNode;
  }
  var typ = node.id;
  var cl = node.getAttribute('cl');
  var nn = typ;
  var i = 0;
  while($('.area').value.match(nn)) {
    i += 1;
    nn = typ+i;
  }
  $('.area').value += '\n' + nn + ':' + cl;
  update_graph();
  $('.canvas').setAttribute('unsaved','all');
  change_title(true);
}


function check() {
  $('myform').submit();
}

function login() {
  $('.form').setAttribute('display','inline');
  $('pw2').setAttribute('style','display:none');
  $('.status').firstChild.nodeValue = '';
}

function logout() {
  var aj = new ajax_get(true,get_base_url() + '/save_session', function(res){
			  document.location.replace(content.document.location);
			});
  aj.doGet(); 
}

function create() {
  $('.form').setAttribute('display','inline');
  $('pw2').setAttribute('style','display:inline');
  $('.status').firstChild.nodeValue='';
}

function to_connect(e) { 
  if ($('_connect').getAttribute('state') == 'on') {
    $('_connect').setAttribute('state','off');
  } else {
    $('_connect').setAttribute('state','on');
  }
  alert ($('_connect').getAttribute('state'));
}

function load_github() { 
  document.location.replace('https://github.com/pelinquin/ConnectedGraph');
}

function load_github_dl() { 
  document.location.replace('https://github.com/pelinquin/ConnectedGraph/tarball/master');
}

function dragenter(e) {
  e.stopPropagation();
  e.preventDefault();
}

function dragover(e) {
  e.stopPropagation();
  e.preventDefault();
} 

function drop(e) {
  nod = e.target;
  while (nod.parentNode.id != '.nodes') { nod = nod.parentNode; }
  if (nod.hasAttribute('href')) { 
    var href = nod.getAttribute('href'); 
    new_attach(e.dataTransfer.files,href,nod);
    //var b = nod.firstChild.nextSibling.getBBox();
    //nod.firstChild.appendChild(attach_icon(b.width));
  } else {
    alert ('drop on an non leaf node!');
  }
  e.stopPropagation();
  e.preventDefault();
}

function select_tag() {
  var tab = $('tagList').childNodes;
  if ($('.tag').value) {
    alert ($('.tag').value);
  }
  for ( var i = 0; i < tab.length; i++ ) {
    if (tab[i].hasAttribute('seleted')) {
      alert ('yes');
    }
  }
}

function export_code(pdf) {
    code = (new XMLSerializer()).serializeToString($('.canvas'));
    //alert (code);
    var fD = new FormData();
    fD.append('code',code);
    //var xhr = new XMLHttpRequest();
    //xhr.open('POST',get_base_url() + '/save_code');
    //xhr.send(fD);
    param = '';
    if (pdf) {
	param = '?pdf=1';
    }
    var ai = new post(true,get_base_url() + '/save_code', fD, function(res) {
	    //alert (res);
	    window.open(get_base_url() + '/load_code'+param, 'neutral', 'chrome,scrollbars=yes');
	});
    ai.doPost();
}

// end
