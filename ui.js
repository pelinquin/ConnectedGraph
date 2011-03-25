//----------------------------------------------------------------------------
// �  Copyright 2011 Rockwell Collins, Inc 
//    This file is part of Formose.
//
//    Formose is free software: you can redistribute it and/or modify
//    it under the terms of the GNU General Public License as published by
//    the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.
//
//    Formose is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU General Public License for more details.
//
//    You should have received a copy of the GNU General Public License
//    along with Formose.  If not, see <http://www.gnu.org/licenses/>.
//----------------------------------------------------------------------------

// Use the compressed version: cgmin.js

const svgns   = 'http://www.w3.org/2000/svg';

// Utilities
if (typeof($)=='undefined') { 
  function $(id) { return document.getElementById(id.replace(/^#/,'')); } 
}

function is_browser_compatible() {
  var str = navigator.userAgent; //alert (str);
  // Webkit
  //Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.651.0 Chrome/10.0.651.0 Safari/534.17
  if (str.match('AppleWebKit')) { return true; }
  // Opera
  if (str.match('Presto')) { return true; }
  // FF4
  //Mozilla/5.0 (Windows NT 5.1; rv:2.0b11pre) Gecko/20110201 Firefox/4.0b11pre
  var gecko = str.replace(/^Mozilla.*rv:|\).*$/g, '' ) || ( /^rv\:|\).*$/g, '' );
  var s = gecko.substring(0,3);
  if ((s=='1.9') || (s=='2.0') || (s=='2.2')) { return true; } 
  return false;
}

function ajax_get(txt,url,cb) {
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
}

function ajax_post(txt,url,data,cb) {
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
}

// Globals
var DD       = null; // DragAndDrop object
var nodeLink = [];   // Hash key:nodes id, value:array of connectors
var nodeBox  = [];   // hash key:nodes, value: node bouding box

window.onload = function () {   
  // Test how to modify CSS properties
  $('debug').style.setProperty('display','none','');
  //alert (document.documentElement.style);
  // Select mode (edit or readonly)
  if (document.documentElement.getAttribute('editable') == 'yes') {
    DD = new dragDrop();
  } else {
      $('.current').setAttribute('opacity','0');
      // TODO; unset this property: g.connectors path:hover, .border:hover { opacity:0.3;}
  }
  // Check browser
  if (!is_browser_compatible()) alert ('Browser not supported !');
  init_menu();
  init_editor();
  init_draw();
  $('.title').firstChild.nodeValue = stat();
  //alert (print_nodes()); // debug
}

function stat() {
  return ($('.nodes').childNodes.length + ' nodes ' + $('.connectors').childNodes.length + ' links')
}

function init_editor() {
  // TODO, Patch Ace Code to avoid CSS warnings on box-sizing and appearance
  var editor = ace.edit('editor'); 
  editor.setTheme('ace/theme/twilight');
  var pMode = require('ace/mode/python').Mode;
  editor.getSession().setMode(new pMode());
  editor.getSession().on('change', change_editor);
}

function init_menu() {
  var b = $('.menu').getBBox();
  nodeBox['.menu'] = b;
  $('.menu').setAttribute('display','none');
  var rect = $('.menu').firstChild;
  var m = 3;
  rect.setAttribute('x',b.x-m);
  rect.setAttribute('y',b.y-m);
  rect.setAttribute('width',b.width+2*m);
  rect.setAttribute('height',b.height+2*m); 
  $('.menu').addEventListener('mousedown', function(evt) {onmenu(evt);}, false);
  // Need an object for getBBox
  var po = document.createElementNS(svgns, 'rect');
  po.id = '.pointer';
  document.documentElement.appendChild(po);
}

function init_draw() {
  var typ = false;
  var t = $('.nodes').childNodes;
  for ( var n = 0; n < t.length; n++ ) {
    if (t[n].nodeName[0] != '#') {
      init_draw_node(t[n]);
    }
  }
  var tco = $('.connectors').childNodes;
  for ( var c=0; c<tco.length; c++ ) {
    if (tco[c].nodeName[0] != '#') {
      var n1 = tco[c].getAttribute('n1').replace('#','');
      var n2 = tco[c].getAttribute('n2').replace('#','');
      Connector(tco[c],n1,n2);
    }
  }
}

function init_draw_node(nod) {
  // TODO; manage node types
  var t = nod.getAttribute('typ').toUpperCase();
  nodeLink[nod.id] = [];
  var b = nod.getBBox();
  nodeBox[nod.id] = b;
  var m = 5; // margin
  if (t == 'GOAL') {
    form = 'path';
  } else {
    form = 'rect';
  }
  var txt = document.createElementNS(svgns,'text');
  txt.setAttribute('x','0');
  txt.setAttribute('y','-13');
  txt.setAttribute('class', 'tiny');
  txt.appendChild(document.createTextNode(t));
  var tid = document.createElementNS(svgns,'text');
  tid.setAttribute('x',b.width+2);
  tid.setAttribute('y','-13');
  tid.setAttribute('fill', 'white');
  tid.setAttribute('text-anchor','end');
  tid.setAttribute('class', 'tiny');
  tid.appendChild(document.createTextNode(nod.id.toUpperCase()));
  var title = document.createElementNS(svgns,'title');
  title.appendChild(document.createTextNode('The title!'));
  var bord = document.createElementNS(svgns,form);
  bord.setAttribute('stroke','red');
  bord.setAttribute('opacity','0');
  bord.setAttribute('stroke-width','15');
  bord.setAttribute('class','border');
  var shape = document.createElementNS(svgns,form);
  shape.setAttribute('stroke-width','1');
  shape.setAttribute('fill','url(#.grad)');
  shape.setAttribute('filter','url(#.shadow)');
  shape.setAttribute('stroke','gray');
  if (t == 'GOAL') {
    var d = 'M'+(b.x-m)+','+(b.y-m)+'l'+(b.width+2*m)+',0l0,'+(b.height+2*m)+'l-'+(b.width+2*m)+',0z';
    bord.setAttribute('d',d);
    shape.setAttribute('d',d);
  } else {
    var x = b.x-m; var y = b.y-m; var w = b.width + 2*m; var h = b.height + 2*m;
    bord.setAttribute('rx', '4');	
    bord.setAttribute('width',w);
    bord.setAttribute('height',h);
    bord.setAttribute('x',x);
    bord.setAttribute('y',y);  
    bord.setAttribute('transform', 'skewX(-10)'); 
    shape.setAttribute('rx', '4');
    shape.setAttribute('width',w);
    shape.setAttribute('height',h);
    shape.setAttribute('x',x);
    shape.setAttribute('y',y);      
    shape.setAttribute('transform', 'skewX(-10)'); 
  }
  nod.insertBefore(bord,nod.firstChild);
  nod.insertBefore(shape,nod.lastChild);
  nod.appendChild(txt);
  nod.appendChild(tid);
  nod.appendChild(title);
}

function change_editor() {
  //TODO; link editor content with current diagram!
  //Parsing on client side
}

function add_node(n,label,x,y) {
  var txt = document.createElementNS(svgns, 'text');
  txt.appendChild(document.createTextNode(label));
  var g = document.createElementNS(svgns, 'g');
  g.setAttribute('id', n);
  g.setAttribute('typ', 'goal'); //tmp
  g.setAttribute('transform','translate(' + x + ',' + y + ')');
  g.appendChild(txt);
  $('.nodes').appendChild(g);
  init_draw_node(g);
}

function add_connector(n1,n2) {
  var co = document.createElementNS(svgns, 'g');
  co.setAttribute('n1', '#'+n1);
  co.setAttribute('n2', '#'+n2);
  $('.connectors').appendChild(co);
  Connector(co,n1,n2); 
}

function print_nodes() {
  var msg = '';
  for ( var i in nodeLink) {
    var tab = nodeLink[i];
    msg += i + '('+tab.length + ')' + $(i).firstChild.nextSibling.nextSibling.firstChild.nodeValue; 
    for ( var j=0; j<tab.length; j++ ) {
      msg += ':'+tab[j].getAttribute('n1')+ ' ' + tab[j].getAttribute('n2'); 
    }
    msg += '\n';
  }
  return (msg);
}

function del_connector(c) {
  //alert (print_nodes() + '\n' + c.getAttribute('n1')+ ' ' +c.getAttribute('n2'));
  for (var e in nodeLink) {
    var index = nodeLink[e].indexOf(c);
    if (index != -1) {
      nodeLink[e].splice(index,1);
    }
  }
  c.parentNode.removeChild(c);
  //alert ('APRES\n' + print_nodes());
}

function del_node(n) {
  var t = nodeLink[n];
  //alert (t.length);
  for (var i=0; i<t.length;i++) {
    //alert(t[i]);
    del_connector(t[i]);
  }
  var nod = $(n);
  nod.parentNode.removeChild(nod);
  //alert (print_nodes());
  //nodeLink[n] = [];
}

function Connector(el,n1,n2) {
  nodeLink[n1].push(el);
  nodeLink[n2].push(el);
  el.appendChild(create_selection_path());
  el.appendChild(create_visible_path());
  draw_path(el,n1,n2);
}

function create_selection_path() {
  var p = document.createElementNS(svgns, 'path');
  p.setAttribute('fill','none');
  p.setAttribute('stroke-width','8');
  p.setAttribute('stroke-linecap','round');
  p.setAttribute('marker-end','none');
  p.setAttribute('stroke','red');
  p.setAttribute('opacity','0');
  return (p);
}

function create_visible_path() {
  var p = document.createElementNS(svgns, 'path');
  p.setAttribute('fill','none');
  p.setAttribute('marker-end','url(#.arrow)');
  p.setAttribute('stroke-width','1.8');
  p.setAttribute('stroke-linecap','round');
  p.setAttribute('stroke','gray');
  return (p);
}

function draw_path(el,n1,n2) {
  // Optimization: only one node transformation should be computed!
  var childs = el.childNodes;
  var d = trunk_path_curve(nodeBox[n1],nodeBox[n2],$(n1).getCTM(),$(n2).getCTM());
  for (var n=0; n<childs.length; n++) {
    if (childs[n].nodeName == 'path') {
      childs[n].setAttribute( 'd', d ); 
    } 
  }
}

function trunk_path_line(b1,b2,t1,t2) {
  var x1 = t1.e + b1.x + b1.width/2;
  var y1 = t1.f + b1.y + b1.height/2;
  var x2 = t2.e + b2.x + b2.width/2;
  var y2 = t2.f + b2.y + b2.height/2;
  var h1 = 1 + b1.height/2;
  var l1 = 1 + b1.width/2; 
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
  var h2 = 1 + b2.height/2;
  var l2 = 1 + b2.width/2;
  if (x2 == x1) {
    if (y2<y1) {
      y2 += h2;
    } else {
      y2 -= h2;
    }
  } else if (y2 == y1) {
    if (x2<x1) {
      x2 += l2;
    } else {
      x2 -= l2;
    }
  } else {
    var Q = x2-x1;
    var R = y2-y1;
    var P = Q/R;
    if (Math.abs(P) < l2/h2) {
      if (R<0) {
	y2 += h2; x2 += h2*P;
      } else {
	y2 -= h2; x2 -= h2*P;
      }
    } else {
      if (Q<0) {
	x2 += l2; y2 += l2/P;
      } else {
	x2 -= l2; y2 -= l2/P;
      }
    }
  }
  return ('M'+x2+','+y2+'L'+x1+','+y1);
}

function trunk_path_curve_simple(b,t,e) {
  var m = document.documentElement.createSVGMatrix()
  m.e = e.clientX; m.f = e.clientY;
  return (trunk_path_curve($('.pointer').getBBox(),b,m,t));
}

function trunk_path_curve(b1,b2,t1,t2) {
  var margin = 6;
  var x1 = t1.e + b1.x + b1.width/2;
  var y1 = t1.f + b1.y + b1.height/2;
  var x2 = t2.e + b2.x + b2.width/2;
  var y2 = t2.f + b2.y + b2.height/2;
  var h1 = margin + b1.height/2;
  var l1 = margin + b1.width/2; 
  var h2 = margin + b2.height/2;
  var l2 = margin + b2.width/2;
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
	y1 += h1; 
	x1 += h1*P;
      } else {
	y1 -= h1; 
	x1 -= h1*P;
      }
    } else {
      if (Q<0) {
	x1 += l1; 
	y1 += l1/P;
      } else {
	x1 -= l1; 
	y1 -= l1/P;
      }
    }
  }
  if (x2 == x1) {
    if (y2<y1) {
      y2 += h2;
    } else {
      y2 -= h2;
    }
  } else if (y2 == y1) {
    if (x2<x1) {
      x2 += l2;
    } else {
      x2 -= l2;
    }
  } else {
    var Q = x2-x1;
    var R = y2-y1;
    var P = Q/R;
    if (Math.abs(P) < l2/h2) {
      if (R<0) {
	y2 += h2; 
	x2 += h2*P;
      } else {
	y2 -= h2; 
	x2 -= h2*P;
      }
    } else {
      if (Q<0) {
	x2 += l2; 
	y2 += l2/P;
      } else {
	x2 -= l2; 
	y2 -= l2/P;
      }
    }
  }
  // Bezier Control points
  var mx = (x1+x2)/2;
  var my = (y1+y2)/2;
  var mx1 = (x1+mx)/2;
  var mx2 = (x2+mx)/2;
  var my1 = (y1+my)/2;
  var my2 = (y2+my)/2;
  var cx1 = x1;
  var cy1 = y1;
  var cx2 = x2;
  var cy2 = y2;
  if (x1 == x2) {
    cy1 = my; cx1 = mx1;
  } else if (y1 == y2) {
    cx1 = mx; cy1 = my1;
  } else {
    var Q = x1-x2;
    var R = y1-y2;
    var P = Q/R;
    if (Math.abs(P) < l1/h1) {
      cy1 = my; cx1 = mx1;
    } else {
      cx1 = mx; cy1 = my1;
    }
  }
  if (x2 == x1) {
    cy2 = my; cx2 = mx2;
  } else if (y2 == y1) {
    cx2 = mx; cy2 = my2;
  } else {
    var Q = x2-x1;
    var R = y2-y1;
    var P = Q/R;
    if (Math.abs(P) < l2/h2) {
      cy2 = my; cx2 = mx2;
    } else {
      cx2 = mx; cy2 = my2;
    }
  }
  return ('M'+x2+','+y2+'C'+cx2+','+cy2+' '+cx1+','+cy1+' '+x1+','+y1);
}

function draw_connectors_from(el) {
  var tab = nodeLink[el];
  for (var e=0; e<tab.length; e++) {
    var n1 = tab[e].getAttribute('n1').replace('#','');
    var n2 = tab[e].getAttribute('n2').replace('#','');
    draw_path(tab[e],n1,n2)
  }
}

function test_if_connector_exist(n1,n2) {
  if (n1 == n2) {
    //alert (n1);
    return false;
  }
  var tco = $('.connectors').childNodes;
  for ( var c=0; c<tco.length; c++ ) {
    if (tco[c].nodeName[0] != '#') {
      var nc1 = tco[c].getAttribute('n1').replace('#','');
      var nc2 = tco[c].getAttribute('n2').replace('#','');
      if (((nc1 == n1) && (nc2 == n2))||((nc1 == n2) && (nc2 == n1))) {
	//alert (n1+' '+n2+' '+nc1+' '+nc2);
	return false;
      }
    }
  }
  return true;
}

function find_id() {
  var max = 0;
  for (var x in nodeLink) {
    if (res = x.match(/\.n(\d+)/)) {
      var k = parseInt(x.substring(2));
      if (k > max) {
	max = k;
      }
    }
  }
  return '.n'+(max+1)
}

function onmenu(e) {
  if (e.target.nodeName == 'tspan') {
    var val = e.target.firstChild.nodeValue;
    if (val == 'Ace') {
      if ($('.editor').getAttribute('display') == 'none') {
	$('.editor').setAttribute('display','inline');
      } else {
	$('.editor').setAttribute('display','none');
      }
    } else {
      var newid = find_id();
      add_node(newid,'my '+val,e.clientX,e.clientY);
      if (DD.border) {
	finalise_connector(DD.border,newid);
	DD.border = false;
      }
      DD.delay = false;
      $('.title').firstChild.nodeValue = '* '+stat();
    }
    $('.menu').setAttribute('display','none');
  }
}

function finalise_connector(nod,n1) {
  var n2 = nod.getAttribute('n2').replace('#','');
  nod.firstChild.setAttribute('stroke','gray');
  var p = create_selection_path();
  p.setAttribute('d',nod.firstChild.getAttribute('d'));
  nod.insertBefore(p,nod.firstChild);
  nod.setAttribute('n1','#'+n1);
  nodeLink[n2].push(nod);
  nodeLink[n1].push(nod);
  draw_path(nod,n1,n2);
  $('.title').firstChild.nodeValue = '* '+stat();
}

function dragDrop () {
  this.el = null;
  this.node = null;
  this.connector = null;
  this.border = false;
  this.delay = false;
  this.fromNode = null;
  this.margin = 15;
  this.p = document.documentElement.createSVGPoint();
  this.o = document.documentElement.createSVGPoint();
  document.documentElement.addEventListener('mousedown', function(evt) {DD.down(evt);}, false);
  document.documentElement.addEventListener('mouseup',   function(evt) {DD.up(evt);},   false);
  document.documentElement.addEventListener('mousemove', function(evt) {DD.move(evt);}, false);
  document.documentElement.addEventListener('keydown',  function(evt) {DD.key(evt);}, false);
}

dragDrop.prototype.down = function(e) {
  var nod = e.target;
  // remove drag event propagation:
  //if (e.button == 2) { e.stopPropagation(); e.preventDefault(); }
  if (this.connector) {
    this.connector.firstChild.nextSibling.setAttribute('opacity','1');
    this.connector.firstChild.nextSibling.setAttribute('stroke','gray');
  }
  if (nod.nodeName == 'svg') {
    $('.menu').setAttribute('display','none');
    if (this.border) {
      this.border.parentNode.removeChild(this.border);
      this.border = null;
    } else {
      this.node = null; 
      $('.current').setAttribute('display','none');
      if (e.button == 0) {
 	$('.menu').setAttribute('display','inline');
	var offset = e.clientY - nodeBox['.menu'].y;
	$('.menu').setAttribute('transform','translate(' + e.clientX + ',' + offset + ')');
      } 
    }
  } else {
    while (nod.parentNode.id != '.nodes' && nod.parentNode.id != '.connectors' && nod.parentNode.nodeName != 'svg') { 
      if (nod.hasAttribute('class')) {
	if (nod.getAttribute('class') == 'border') {
	  this.border = document.createElementNS(svgns, 'g');
	  var p = create_visible_path()
	  p.setAttribute('pointer-events','none');
	  p.setAttribute('stroke','red'); 
	  this.border.appendChild(p);
	}
      }
      nod = nod.parentNode;
    }
    if (nod.parentNode.id == '.connectors') { 
      $('.menu').setAttribute('display','none');
      nod.firstChild.nextSibling.setAttribute('opacity','.6');
      nod.firstChild.nextSibling.setAttribute('stroke','red');
      $('.current').setAttribute('display','none');
      this.node = null;
      this.connector = nod;
    }
    if (nod.parentNode.id == '.nodes') { 
      $('.menu').setAttribute('display','none');
      this.el = nod;
      var tr = nod.getCTM();
      if (this.border) {
	this.fromNode = nod;
	this.border.setAttribute('n1','');
	this.border.setAttribute('n2','#'+nod.id);
	$('.connectors').appendChild(this.border);
      } else {
	this.p.x = tr.e; 
	this.p.y = tr.f;
	this.o.x = e.clientX; this.o.y = e.clientY;
	this.c = $('.current').firstChild;
	var b = nodeBox[nod.id];
	this.c.setAttribute('width',b.width+2*this.margin);
	this.c.setAttribute('height',b.height+2*this.margin);
	this.c.setAttribute('x',b.x + this.p.x - this.margin);
	this.c.setAttribute('y',b.y + this.p.y - this.margin);
	this.c.parentNode.setAttribute('display','inline');
	this.node = this.el;
      }
      //$('debug').firstChild.nodeValue = 'msg'; 
    }
  }
};

dragDrop.prototype.move = function(e) {
  if (this.el) {
    if (this.border) {
      var d = trunk_path_curve_simple(nodeBox[this.el.id],this.fromNode.getCTM(),e);
      this.border.firstChild.setAttribute('d',d);
      document.documentElement.setAttribute('cursor','default');
    } else {
      var x = e.clientX + this.p.x - this.o.x;
      var y = e.clientY + this.p.y - this.o.y;
      this.el.setAttribute('transform','translate(' + x + ',' + y + ')'); 
      this.c.setAttribute('x',nodeBox[this.el.id].x + x - this.margin);
      this.c.setAttribute('y',nodeBox[this.el.id].y + y - this.margin);
      draw_connectors_from(this.el.id);
    }
  }
};

dragDrop.prototype.up = function(e) {
  this.el=null;
  if (this.border) {
    var found = false;
    var nod = e.target;
    if (nod.nodeName == 'svg') {
      this.delay = true;
      $('.menu').setAttribute('display','inline');
      var offset = e.clientY - nodeBox['.menu'].y;
      $('.menu').setAttribute('transform','translate(' + e.clientX + ',' + offset + ')');
    } else {
      while (nod.parentNode.id != '.nodes' && nod.parentNode.nodeName != 'svg') { 
        nod = nod.parentNode;
      }
      if (nod.parentNode.id == '.nodes') { 
	var n2 = this.border.getAttribute('n2').replace('#','');
	if (test_if_connector_exist(n2,nod.id)) {
	  found = true;
	  finalise_connector(this.border,nod.id);
	} else {
	  //alert ('Connector already exists!');
	}
      }
    }
    if (!found && !this.delay) {
      this.border.parentNode.removeChild(this.border);
    }
    if (!this.delay) {
      this.border = null;
    }
  } 
};

dragDrop.prototype.key = function(e) {
  if (e.type == 'keydown') {
    if (e.charCode) { var charCode = e.charCode; }
    else { var charCode = e.keyCode; }
    if (charCode == 46){ //del key
      if (this.connector) {
	del_connector(this.connector);
      } else {
	del_node(this.node.id);
	this.c.parentNode.setAttribute('display','none');
      }
      $('.title').firstChild.nodeValue = '* '+stat();
    } else if (charCode == 10 || charCode == 13) { //return key
    } else if (charCode > 31 && charCode != 127 && charCode < 65535) {} //TODO
  }
  //e.preventDefault(); if requested!
}

// end