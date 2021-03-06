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

// Use the compressed version: uimin.js


//---------- Globals ----------
var DD       = null; // DragAndDrop object
var nodeLink = [];   // Hash key:nodes id, value:array of connectors
var nodeBox  = [];   // Hash key:nodes, value: node bouding box
var editor   = null; // Pointer to ACE editor
var log = '';

//---------- Init ----------

if (typeof(addLoadEvent)=='undefined') { 
    function addLoadEvent(func) { 
	var oldonload = window.onload; 
	if (typeof window.onload != 'function') { 
	    window.onload = func; 
	} else { 
	    window.onload = function() { 
		if (oldonload) { 
		    oldonload(); 
		} 
		func(); 
	    } 
	} 
    } 
}

addLoadEvent (function init_graph () {  
	if (document.documentElement.getAttribute('editable') == 'yes') {
	    DD = new dragDrop();
	    init_menu();
	    init_other();
	}
	init_draw();
    });

function stat() {
  return ($('.nodes').childNodes.length + ' nodes ' + $('.connectors').childNodes.length + ' links')
}

function isIn(val, li) {
  for(var i=0; i < li.length; i++) { if((li[i] == val)) { return true; }}
  return false;  
}

function init_editor(is_ace) {
  // TODO, Patch Ace Code to avoid CSS warnings on box-sizing and appearance
  // Webkit needs position fixed for editor
  if (is_webkit()) {
    $('.editor').style.setProperty('position','fixed','');
  }
  if (is_ace) {
    editor = ace.edit('.editor'); 
    editor.setTheme('ace/theme/twilight');
    var pMode = require('ace/mode/python').Mode;
    editor.getSession().setMode(new pMode());
    //editor.getSession().doc.on('change', change_editor);
  } 
  $('.editor').addEventListener('keyup', change_editor, false);
  saved_doc = get_editor();
}

function init_other() {
  $('.area').firstChild.addEventListener('change', function(evt) {DD.change(evt);}, false);
  $('.area').parentNode.setAttribute('visibility', 'hidden');
  // Need an object for getBBox
  var po = document.createElementNS(svgns, 'rect');
  po.id = '.pointer';
  document.documentElement.appendChild(po);
}

function init_menu() {
  var rect = $('.menu').firstChild;
  var tab = $('.menu').childNodes;
  var ypos = 0;
  for ( var i=0; i<tab.length; i++ ) {
    if (tab[i].nodeName == 'text') {
      tab[i].setAttribute('y',ypos);
      ypos += 12;
    }
  }
  var b0 = $('.menu').getBBox();
  nodeBox['.menu'] = b0;
  var m = 5;
  rect.setAttribute('x',b0.x-m);
  rect.setAttribute('y',b0.y-m);
  rect.setAttribute('width',b0.width+2*m);
  rect.setAttribute('height',b0.height+2*m); 
  ypos = 0;
  var typ = '';
  var offset = null;
  for ( var i=0; i<tab.length; i++ ) {
    if (tab[i].nodeName == 'text') {
      typ = tab[i].firstChild.nodeValue;
      offset = tab[i].getBBox().width;
    }
    if (tab[i].nodeName == 'g') {
      var txt = document.createElementNS(svgns,'text');
      txt.setAttribute('x','10');
      txt.setAttribute('y','0');
      txt.appendChild(document.createTextNode(typ));
      tab[i].appendChild(txt); 
      var b = txt.getBBox();
      tab[i].insertBefore(get_shape(typ.toUpperCase(),b),tab[i].firstChild);
      tab[i].setAttribute('transform','translate('+offset+','+ypos+')');
      tab[i].setAttribute('display','none');
      ypos += 12;
    }
  }
  $('.menu').setAttribute('display','none');
  $('.menu').addEventListener('mousedown', function(evt) {onmenu(evt);}, false);
}

function get_init_shape(t,up) {
  if (isIn(t,['ASSOCIATION','AGENT','PROPERTY','EVENT'])) {
    form = 'path';
  } else if (isIn(t,['REQUIREMENT','CLASS','GOAL','ENTITY','OBSTACLE','EXPECTATION'])){
    form = 'rect';
  } else {
    //form = 'ellipse';
    form = 'rect';
  }
  var fig = document.createElementNS(svgns,form);
  if (up) {
    fig.setAttribute('fill','url(#.grad)');
    fig.setAttribute('stroke','gray'); 
    if (t=='REQUIREMENT') {
      fig.setAttribute('stroke-width','2');
    } else {
      fig.setAttribute('stroke-width','1');
    }
  } else {
    fig.setAttribute('stroke','yellow');
    fig.setAttribute('opacity','0');
    fig.setAttribute('stroke-width','15');
    fig.setAttribute('class','border');
  }
  if (t=='REQUIREMENT' || t=='GOAL') {
    fig.setAttribute('rx', '4');
    fig.setAttribute('transform', 'skewX(-10)'); 
  } else if (t == 'ENTITY'|| t=='EXPECTATION' || t=='CLASS' ) {
    fig.setAttribute('rx', '1');
  } else if (t=='OBSTACLE') {
    fig.setAttribute('transform', 'skewX(10)'); 
  }
  return (fig);
}

function resize_shape(t,b,shape) {
  var m = 5; 
  if (isIn(t,['ASSOCIATION','AGENT','PROPERTY','EVENT'])) {
    var d = 'M';
    m = 10;
    if (t == 'AGENT') {
      var f = 8;
      var x = b.x - m;
      var y = b.y - m;
      var w = b.width + 2*m;
      var h = b.height + 2*m;
      d += (x+f)+','+y + 
	'l' + (w-2*f) + ',0' + 
	'l' + f +',' + (h/2) + 
	'l' + (-f) + ',' + (h/2)  + 
	'l' + (2*f-w) +',0' + 
	'l' + (-f) + ',' + (-h/2) + 'z';
      // simple rectangle for debugging
      //d += (b.x-m)+','+(b.y-m)+'l'+(b.width+2*m)+',0l0,'+(b.height+2*m)+'l-'+(b.width+2*m)+',0z'; 
    } else {
      d += (b.x-m)+','+(b.y+b.height/2)+'l'+(b.width/2+m)+','+(b.height/2+m)+'l'+(b.width/2+m)+','+(-b.height/2-m)+ 'l'+(-b.width/2-m)+','+(-b.height/2-m)+'z';
    }
    shape.setAttribute('d',d);
  } else if (isIn(t,['REQUIREMENT','CLASS','GOAL','ENTITY','OBSTACLE','EXPECTATION'])){
    var x = b.x-m; var y = b.y-m; var w = b.width + 2*m; var h = b.height + 2*m;
    shape.setAttribute('x',x); 
    shape.setAttribute('y',y); 
    shape.setAttribute('width',w); 
    shape.setAttribute('height',h); 
  } else {
    //var cx = b.x+b.width/2; var cy = b.y+b.height/2; var rx = b.width/2 + m; var ry = b.height/2 + m;
    //shape.setAttribute('cx',cx); 
    //shape.setAttribute('cy',cy); 
    //shape.setAttribute('rx',rx); 
    //shape.setAttribute('ry',ry); 
    var x = b.x-m; var y = b.y-m; var w = b.width + 2*m; var h = b.height + 2*m;
    shape.setAttribute('x',x); 
    shape.setAttribute('y',y); 
    shape.setAttribute('width',w); 
    shape.setAttribute('height',h); 
  }
}

function get_shape(t,b) {
  var shape = get_init_shape(t,true)
  resize_shape(t,b,shape);
  return (shape);
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
      Connector(tco[c],tco[c].getAttribute('n1').replace('#',''),tco[c].getAttribute('n2').replace('#',''));
    }
  }
}

function init_draw_node(nod) {
  var t = nod.getAttribute('type').toUpperCase();
  nodeLink[nod.id] = [];
  var b = nod.getBBox();
  nodeBox[nod.id] = b;
  var txt = document.createElementNS(svgns,'text');
  txt.setAttribute('x','0');
  txt.setAttribute('y','-13');
  txt.setAttribute('class', 'tiny');
  txt.appendChild(document.createTextNode(t));
  var tid = document.createElementNS(svgns,'text');
  tid.setAttribute('y','-13');
  tid.setAttribute('fill', 'white');
  tid.setAttribute('text-anchor','end');
  tid.setAttribute('class', 'tiny');
  tid.appendChild(document.createTextNode(nod.id.toUpperCase()));
  var sep = document.createElementNS(svgns,'path'); 
  sep.setAttribute('stroke','gray');
  var sep1 = document.createElementNS(svgns,'path'); 
  sep1.setAttribute('stroke','gray');
  if (t == 'CLASS') { 
      set_node_header(nod.firstChild.firstChild,b.width/2);
      set_separators(nod.firstChild.childNodes.length,sep,sep1,b.width);
  } else {
      sep.setAttribute('stroke-width',0);
      sep1.setAttribute('stroke-width',0);
  }
  var title = document.createElementNS(svgns,'title');
  title.appendChild(document.createTextNode(nod.id.toUpperCase()+':'+t));
  var bord = get_init_shape(t,false);
  var shape = get_init_shape(t,true)
  //shape.setAttribute('filter','url(#.shadow)'); // pb with Safari
  shape.setAttribute('stroke','gray');
  nod.insertBefore(bord,nod.firstChild);
  nod.insertBefore(shape,nod.lastChild);
  nod.appendChild(txt);
  nod.appendChild(tid);
  nod.appendChild(title);
  nod.appendChild(sep);
  nod.appendChild(sep1);
  tid.setAttribute('x',b.width);
  resize_shape(t,b,bord);
  resize_shape(t,b,shape);
}

function set_separators(n,sep1,sep2,w) {
  if (n == 1) {
    sep1.setAttribute('stroke-width',0);
    sep2.setAttribute('stroke-width',0);
  } else if (n == 2) {
    sep1.setAttribute('stroke-width',1);
    sep2.setAttribute('stroke-width',0);
	set_separator_length(sep1,3,w);
  } else {
    sep1.setAttribute('stroke-width',1);
    sep2.setAttribute('stroke-width',1);
    set_separator_length(sep1,3,w);
    set_separator_length(sep2,18,w);
  }
}

function set_separator_length(sep,y,w) {
  sep.setAttribute('d','M-5,'+y+'l'+(w+10)+',0');
}

function set_node_header(nod,x) {
  nod.setAttribute('x',x); 
  nod.setAttribute('text-anchor','middle');
  nod.setAttribute('font-weight','bold');
}

function change_node_content(n,label) {
  $('.current').setAttribute('display','none');
  var t = $(n).getAttribute('type').toUpperCase();
  var nod = $(n).firstChild.nextSibling.nextSibling;
  var old = concat_node_text(nod,'|');
  set_node_text(nod,label);
  var new_label = concat_node_text(nod,'|');
  var b = nod.getBBox();
  nodeBox[n] = b;
  var bord = $(n).firstChild;
  var shape = $(n).firstChild.nextSibling;
  $(n).childNodes[4].setAttribute('x',b.width);
  if (t == 'CLASS') { 
      set_node_header(nod.firstChild,b.width/2);
      set_separators(nod.childNodes.length,$(n).childNodes[6],$(n).childNodes[7],b.width)
  }
  resize_shape(t,b,bord);
  resize_shape(t,b,shape);
  draw_connectors_from(n);
  // Change editor
  var v = get_editor();
  var re = new RegExp(RegExp.quote(n)+'\\s*\\('+RegExp.quote(old)+'\\)');
  set_editor(v.replace(re,n+'('+new_label+')'));
  //alert ('APRES\n' + print_nodes());
}

function set_editor(str) {
  if (editor) {
    //editor.getSession().getDocument().setValue(str);
    //editor.getSession().setValue(str);
    //editor.detach();
    editor.getSession().doc.setValue(str);
  } else {
    $('.editor').value = str;
  }
  //editor.insert("Something cool");
}

function get_editor() { 
  if (editor) {
    return editor.getSession().getValue();
  } else {
    return $('.editor').value;
  }
}

function signin() {
  $('.loginpage').setAttribute('display','inline');
}

function editor_add(txt) {
  var sep = '';
  var old = get_editor();
  if (old != '') {
    sep = '\n';
  }
  set_editor(old + sep + txt); 
  update();
}

function editor_change_connector(n1,n2,new_nod,way) {
  var re = new RegExp('\\b' + RegExp.quote(n1) +'\\s*\->\\s*' + RegExp.quote(n2) +'\\b');
  if (way) {
    set_editor(get_editor().replace(re,new_nod + '->' + n2));
  } else {
    set_editor(get_editor().replace(re,n1 + '->' + new_nod));
  }
  update();
}

function change_editor(evt) {
  /////
  //alert ('change');
  //$('.debug').firstChild.nodeValue = $('.editor').firstChild.nodeValue;
  //TODO; link editor content with current diagram!
  show_menu();
  //Parsing on client side
  update();
  //alert (evt.data.lines);
  //parse_editor(get_editor());
}

function parse_editor(txt) {
  // Javascript Code Start REGEX from Python
  var __REG_NODES__ = /(?:(\w+)|(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"))+(:\w+)?(@\S{10})?\s*(?:\#[^\n]*(?:\n|$))?/g;
  var __REG_EDGES__ = /(?:(\w+)|(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"))+(:\w+)?(@\S{10})?\s*(?:\#[^\n]*(?:\n|$))?\s*(->|<-|-!-|[\d\.]*-[\d\.]*)\s*(?:(\w+)|(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"))+(:\w+)?(@\S{10})?\s*(?:\#[^\n]*(?:\n|$))?/g;
  // End REGEX
  
  var o = '{';
  var sep = '';
  while (m = __REG_NODES__.exec(txt)) {
    if (m[1] !== '') {
      o += sep + '\'' + m[1] + '\': \'' + m[1] + '\'';
      sep = ', ';
    }
  } 
  o += '}';
  return (o);
  //'A[label]':"{'A': 'label'}",
  //'A B':"{'A': 'A', 'B': 'B'}",
}

function parse_editor1(txt) {
  // Javascript Code Start REGEX from Python
  var __REG_NODES__ = /(\w*)(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"|):?(\w*)(@\S{10}|)(\s*\#[^\n]*\n|)/g;
  var __REG_EDGES__ = /(\w*)(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"|):?(\w*)(@\S{10}|)\s*(->|<-|-!-|[\d\.]*-[\d\.]*)\s*(\w*)(\[(?:\\.|[^\]])+\]|\((?:\\.|[^\)])+\)|\<(?:\\.|[^\->])+\>|\"(?:\\.|[^\"])+\"|):?(\w*)(@\S{10}|)/g;
  // End REGEX
  //alert (txt);
  var o = '[';
  var sep = '';
  while (m = __REG_EDGES__.exec(txt)) {
    var k1='';
    var k2='';
    if ((m[1] || m[2]) && (m[6] || m[7])) {
      var n1 = m[1];
      if (n1 !== '') {
	k1 = n1;
      } else {
	//l1 = re.sub(r'\\','',m[2][1:-1]);
	//if (r.has_key(l1)) { 
	if (false) {
	  //k1 = r[l1]; n2 = m[6];
	  if (n2 !== '') {
	    k2 = n2;
	  } else {
	    //l2 = re.sub(r'\\','',m[7][1:-1]);
	    //if (r.has_key(l2)) {
	    if (false) {
	      //k2 = r[l2];        
	      if (k1 !== k2) {
		//...
	      }
	    }
	  }
	}
      }
    }
    if (m[1] !== '' && m[6] !== '') {
      if (m[5] === '<-') {
	o += sep + '(\'' + m[1] + '\', \'' + m[6] + '\')';
      } else if (m[5] === '-!-') {
	o += sep + '(\'' + m[1] + '\', \'' + m[6] + '\', \'conflict\')';
      } else {
	o += sep + '(\'' + m[6] + '\', \'' + m[1] + '\')';
      }
      sep = ', ';
    }
  } 
  o += ']';
  return (o);
}

function add_node(n,typ,label,x,y) {
  var txt = document.createElementNS(svgns, 'text');
  var ts = document.createElementNS(svgns, 'tspan');
  ts.appendChild(document.createTextNode(label));
  txt.appendChild(ts);
  var g = document.createElementNS(svgns, 'g');
  g.setAttribute('id', n);
  g.setAttribute('type', typ);
  g.setAttribute('transform','translate(' + x + ',' + y + ')');
  g.appendChild(txt);
  $('.nodes').appendChild(g);
  init_draw_node(g);
  editor_add(n+'('+label+'):'+typ);
  //alert (print_nodes()); // debug
}

function add_connector(n1,n2) {
  var co = document.createElementNS(svgns, 'g');
  co.setAttribute('n1', '#'+n1);
  co.setAttribute('n2', '#'+n2);
  $('.connectors').appendChild(co);
  Connector(co,n1,n2); 
  editor_add(n1+'->'+n2);
}

function editor_flip(n1,n2) {
  var re = new RegExp('(?:[\\W\\.]|\^)' + RegExp.quote(n1) +'\\s*\->\\s*' + RegExp.quote(n2) +'\\b');
  set_editor(get_editor().replace(re,'\n'+n2+'->'+n1));
  update();
}

function flip_connector(c) {
  var tmp = c.getAttribute('n1');
  c.setAttribute('n1',c.getAttribute('n2'));
  c.setAttribute('n2',tmp);   
  draw_connector(c);
  editor_flip(c.getAttribute('n2').replace('#',''),c.getAttribute('n1').replace('#',''));
}

function flip_link(n1,n2) {
  var tco = $('.connectors').childNodes;
  for ( var c=0; c<tco.length; c++ ) {
    if (tco[c].nodeName[0] != '#') {
      var nc1 = tco[c].getAttribute('n1').replace('#','');
      var nc2 = tco[c].getAttribute('n2').replace('#','');
      if ((n1 == nc1) && (n2 == nc2)) {
	flip_connector(tco[c]);
      }
    }
  }
}

function del_link(n1,n2) {
  var tco = $('.connectors').childNodes;
  for ( var c=0; c<tco.length; c++ ) {
    if (tco[c].nodeName[0] != '#') {
      var nc1 = tco[c].getAttribute('n1').replace('#','');
      var nc2 = tco[c].getAttribute('n2').replace('#','');
      if ((n1 == nc1) && (n2 == nc2)) {
	del_connector(tco[c]);
      }
    }
  }
}

function pop_connector(c) {
  for (var e in nodeLink) {
    var index = nodeLink[e].indexOf(c);
    if (index != -1) {
      nodeLink[e].splice(index,1);
    }
  }
}
function del_connector(c) {
  //alert ('del connector\n' + c.getAttribute('n1')+ ' ' +c.getAttribute('n2'));
  pop_connector(c);
  c.parentNode.removeChild(c);
  // update editor:
  var n1 = c.getAttribute('n1').replace('#','');
  var n2 = c.getAttribute('n2').replace('#','');
  var re = new RegExp('(?:[\\W\\.]|\^)' + RegExp.quote(n1) +'\\s*\->\\s*' + RegExp.quote(n2) +'\\b');
  set_editor(get_editor().replace(re,''));
  update();
  //alert (print_nodes());
}

function del_node(n) {
  var tab = nodeLink[n];
  while (tab.length != 0) { del_connector(tab[0]); }
  var nod = $(n);
  var t = nod.getAttribute('type');
  nod.parentNode.removeChild(nod);
  delete nodeLink[n];
  var re = new RegExp(RegExp.quote(n) + '\\([^\\)]*\\):'+t+'\\s?');
  set_editor(get_editor().replace(re,''));
  update();
}

function Connector(el,n1,n2) {
  nodeLink[n1].push(el);
  nodeLink[n2].push(el);
  el.appendChild(create_selection_path());
  el.appendChild(create_visible_path());
  // test to add text on the path
  //var t = document.createElementNS(svgns, 'text');
  //var p = document.createElementNS(svgns, 'textPath');
  //p.appendChild(document.createTextNode('Hello this is text'));
  //p.setAttribute('xmlns:xlink',xlinkns); 
  //p.setAttribute('xlink:href','#ZZ');
  //p.setAttribute('stroke','red');
  //t.appendChild(p);
  //el.appendChild(t);
  //el.firstChild.nextSibling.setAttribute('id','ZZ');
  
  // end path selection circles...not used!
  //el.appendChild(create_selection_circle(n1));
  //el.appendChild(create_selection_circle(n2));
  draw_connector(el);
}

function create_selection_circle(n) {
  var c = document.createElementNS(svgns, 'circle');
  c.setAttribute('id','_'+n);
  c.setAttribute('r','10');
  c.setAttribute('fill','none');
  c.setAttribute('stroke-width','10');
  c.setAttribute('stroke','yellow');
  c.setAttribute('opacity','0'); 
  return (c);
}

function create_selection_path() {
  var p = document.createElementNS(svgns, 'path');
  p.setAttribute('fill','none');
  p.setAttribute('stroke-width','8');
  p.setAttribute('stroke-linecap','round');
  p.setAttribute('stroke','yellow');
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
  //p.setAttribute('marker-start', 'url(#.simple_start)'); 
  //p.setAttribute('marker-end', 'url(#.simple_end)');
  p.setAttribute('marker-mid', 'url(#.conflict)');
  return (p);
}

function draw_connector(el) { 
  // Optimization to do: only one node transformation should be computed!
  var n1 = el.getAttribute('n1').replace('#','');
  var n2 = el.getAttribute('n2').replace('#','');
  var childs = el.childNodes;
  var t1 = $(n1).getCTM();
  var t2 = $(n2).getCTM();
  var d = trunk_path_curve(nodeBox[n1],nodeBox[n2],t1,t2);
  for (var n=0; n<childs.length; n++) {
    if (childs[n].nodeName == 'path') {
      childs[n].setAttribute( 'd', d ); 
    } else if (childs[n].nodeName == 'circle') {
      if (childs[n].id == '_'+n1) {
	childs[n].setAttribute( 'cx', t1.e ); 
	childs[n].setAttribute( 'cy', t1.f );
      } else {
	childs[n].setAttribute( 'cx', t2.e ); 
	childs[n].setAttribute( 'cy', t2.f );
      } 
    }
  }
}

function draw_path(el,n1,n2) { 
  // Optimization to do: only one node transformation should be computed!
  var childs = el.childNodes;
  var t1 = $(n1).getCTM();
  var t2 = $(n2).getCTM();
  var d = trunk_path_curve(nodeBox[n1],nodeBox[n2],t1,t2);
  for (var n=0; n<childs.length; n++) {
    if (childs[n].nodeName == 'path') {
      childs[n].setAttribute( 'd', d ); 
    } else if (childs[n].nodeName == 'circle') {
      if (childs[n].id == '_'+n1) {
	childs[n].setAttribute( 'cx', t1.e ); 
	childs[n].setAttribute( 'cy', t1.f );
      } else {
	childs[n].setAttribute( 'cx', t2.e ); 
	childs[n].setAttribute( 'cy', t2.f );
      } 
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
  return (trunk_path_curve(b,$('.pointer').getBBox(),t,m));
}

function trunk_path_curve_reverse(b,t,e) {
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
  return ('M'+parseInt(x1)+','+parseInt(y1)+'C'+parseInt(cx1)+','+parseInt(cy1)+' '+parseInt(cx2)+','+parseInt(cy2)+' '+parseInt(x2)+','+parseInt(y2));
}

function draw_connectors_from(el) {
  var tab = nodeLink[el];
  for (var e=0; e<tab.length; e++) {
    draw_connector(tab[e])
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
    if (res = x.match(/_(\d+)/)) {
      var k = parseInt(x.substring(1));
      if (k > max) {
	max = k;
      }
    }
  }
  return '_'+(max+1)
}

function switch_mode() {
  // Three states mode
  if ($('.editor').parentNode.getAttribute('display') == 'inline') {
    if ($('.nodes').getAttribute('visibility') == 'visible') {
      $('.nodes').setAttribute('visibility','hidden');
      $('.connectors').setAttribute('visibility','hidden');
    } else {
      $('.editor').parentNode.setAttribute('display','none');
      $('.nodes').setAttribute('visibility','visible');
      $('.connectors').setAttribute('visibility','visible');
    }
  } else {
    $('.editor').parentNode.setAttribute('display','inline');
  }
}

function onmenu(e) {
  if (e.target.nodeName == 'text') {
    var val = e.target.firstChild.nodeValue;
    var newid = find_id();
    add_node(newid,val,val,e.clientX,e.clientY);
    if (DD.border) {
      finalize_connector(DD.border,newid,false);
      DD.border = false;
    }
    DD.delay = false;
    //update();
    $('.menu').setAttribute('display','none');
  }
}

function finalize_connector(nod,n2,upd) {
  var n1 = nod.getAttribute('n1').replace('#','');
  nod.firstChild.setAttribute('stroke','gray');
  var p = create_selection_path();
  p.setAttribute('d',nod.firstChild.getAttribute('d'));
  nod.insertBefore(p,nod.firstChild);
  nod.setAttribute('n2','#'+n2);
  nodeLink[n2].push(nod);
  nodeLink[n1].push(nod);
  draw_connector(nod);
  editor_add(n1+'->'+n2);
  if (upd) {
    //update();
  }
}

function set_current(x,y,w,h) {
  obj = $('.current').firstChild;
  obj.setAttribute('width',w);
  obj.setAttribute('height',h);
  obj.setAttribute('x',x);
  obj.setAttribute('y',y);
  obj.parentNode.setAttribute('display','inline');
  return (obj);
}

function show_menu(e) {
  if (typeof(e) == 'undefined') {
    $('.menu').setAttribute('display','none');
  } else {
    //alert ($('.area').parentNode.getAttribute('visibility'));
    if ($('.nodes').getAttribute('visibility') == 'visible') {
      $('.menu').setAttribute('display','inline');
      var offset = e.clientY - nodeBox['.menu'].y;
      $('.menu').setAttribute('transform','translate(' + (e.clientX + 5) + ',' + offset + ')');
    }
  }
}

function dragDrop () {
  this.el = null;
  this.node = null;
  this.edit = null;
  this.editing = false;
  this.connector = null;
  this.border = false;
  this.delay = false;
  this.fromNode = null;
  this.margin = 15;
  this.charCode = null;
  this.changeconnector = null;
  this.p = document.documentElement.createSVGPoint();
  this.o = document.documentElement.createSVGPoint();
  document.documentElement.addEventListener('mousedown', function(evt) {DD.down(evt);}, false);
  document.documentElement.addEventListener('mouseup',   function(evt) {DD.up(evt);},   false);
  document.documentElement.addEventListener('mousemove', function(evt) {DD.move(evt);}, false);
  document.documentElement.addEventListener('keydown',   function(evt) {DD.key(evt);}, false);
}

dragDrop.prototype.background = function(e) {
  show_menu();
  if (this.border) {
    this.border.parentNode.removeChild(this.border);
    this.border = null;
  } else {
    //if ((e.button == 0)&&(!this.edit)) {
    if (e.button == 0) {
      if (!this.editing) {
	show_menu(e);
      }
    }
  }
}

dragDrop.prototype.down = function(e) {
  var nod = e.target;
  //$('.debug').firstChild.nodeValue = nod.nodeName + '|' + nod.id;
  if (this.editing) {
    if ($('.area').parentNode.getAttribute('visibility') == 'hidden') {
      this.editing = false;
    }
  }
  if (this.connector) {
    this.connector.firstChild.nextSibling.setAttribute('opacity','1');
    this.connector.firstChild.nextSibling.setAttribute('stroke','gray');
  }
  if ($('.msg')) {
    if ($('.msg').hasChildNodes()) {
      $('.msg').removeChild($('.msg').firstChild);
    }
  }
  if (nod.nodeName == 'svg' || nod.parentNode.id != '.area') { 
    if (this.edit) {
      $('.area').parentNode.setAttribute('visibility','hidden');
    }
  }
  if (this.node) {
    this.node = null;
    $('.current').setAttribute('display','none');
  }
  //
  if (nod.nodeName == 'svg' || nod.id == '.editor') {
    this.background(e); 
  } else {
    if (nod.hasAttribute('class') && (nod.getAttribute('class') == 'border')) {
      this.border = document.createElementNS(svgns, 'g');
      var p = create_visible_path()
      p.setAttribute('pointer-events','none');
      p.setAttribute('stroke','yellow'); 
      this.border.appendChild(p);
    } 
    while (nod.parentNode.id != '.nodes' && nod.parentNode.id != '.connectors' && nod.parentNode.id != '.editor' && nod.parentNode.nodeName != 'svg') { 
      nod = nod.parentNode;
    }
    if (nod.parentNode.nodeName == 'svg') {
      show_menu();
    } else if (nod.parentNode.id == '.editor') { 
	this.background(e); 
    } else if (nod.parentNode.id == '.connectors') { 
      e.preventDefault(); // stop Drag&drop event propagation 
      show_menu();
      nod.firstChild.nextSibling.setAttribute('opacity','.6');
      nod.firstChild.nextSibling.setAttribute('stroke','red');
      this.connector = nod;
      var p = /^M(\d+),(\d+).* (\d+),(\d+)$/.exec(nod.firstChild.getAttribute('d'));
      var d1 = (p[1]-e.clientX)*(p[1]-e.clientX)+(p[2]-e.clientY)*(p[2]-e.clientY)
      var d2 = (p[3]-e.clientX)*(p[3]-e.clientX)+(p[4]-e.clientY)*(p[4]-e.clientY)
      if (d1<100) {
	this.changeconnector=nod.getAttribute('n2').replace('#','');	
	this.changeconnectordir = true;
      } else if (d2<100) {
	this.changeconnector=nod.getAttribute('n1').replace('#','');
	this.changeconnectordir = false;
      }
      if (e.detail == 2) { 
	flip_connector(nod);
	//show_connectormenu(e);
      }
    } else if (nod.parentNode.id == '.nodes') { 
      e.preventDefault(); // stop Drag&drop event propagation 
      show_menu();
      this.el = nod;
      var tr = nod.getCTM();
      if (this.border) {
	this.fromNode = nod;
	this.border.setAttribute('n1','#'+nod.id);
	this.border.setAttribute('n2','');
	$('.connectors').appendChild(this.border);
      } else {
	var b = nodeBox[nod.id];
	this.p.x = tr.e; 
	this.p.y = tr.f;
	var x = b.x + this.p.x - this.margin;
	var y = b.y + this.p.y - this.margin;
	this.node = this.el;
	if (e.detail == 2) { 
	  this.el = null;
	  this.edit = nod;
	  this.editing = true;
	  set_area(nod.firstChild.nextSibling.nextSibling,x,y,b.width,b.height); 
	} else {
	  this.o.x = e.clientX; this.o.y = e.clientY;
	  this.c = set_current(x,y,b.width+2*this.margin,b.height+2*this.margin);
	}
      } 
    } else {
      alert ('svg pb!');
    }
  }
};

function set_node_text(nod,label) {
  while (nod.hasChildNodes()) { nod.removeChild(nod.firstChild); }
  var t = label.split('\n');
  var first = true;
  for ( var c=0; c<t.length; c++ ) {
    if (first) {
      var n1 = document.createElementNS(svgns,'tspan');
      n1.appendChild(document.createTextNode(t[c]));
      nod.appendChild(n1);
      first = false;
    } else {
      var n1 = document.createElementNS(svgns,'tspan');
      n1.setAttribute('x', 0);
      n1.setAttribute('dy', '1.2em');
      n1.appendChild(document.createTextNode(t[c]));
      nod.appendChild(n1);
    }
  }
}

function concat_node_text(nod,sep) {
  var txt = '';
  var sep1 = '';
  var t0 = nod.childNodes;
  for ( var c=0; c<t0.length; c++ ) {
    if (t0[c].nodeName != '#text') {
      var t1 = t0[c].childNodes;
      for ( var j=0; j<t1.length; j++ ) {
	txt += sep1+t1[j].nodeValue;
	sep1 = sep;
      }
    }
  }
  return (txt);
}

function set_area(nod,x,y,w,h) {
  if (w<30) {w=30;}
  if (h<20) {h=20;}
  var area = $('.area');
  area.setAttribute('width',w+35);
  area.setAttribute('height',h+35);
  area.parentNode.setAttribute('transform','translate('+x+','+y+')');
  area.firstChild.setAttribute('style','resize:none; border:1px solid #ccc;width:'+(w+30)+'px;height:'+(h+30)+'px');
  area.firstChild.value = concat_node_text(nod,'\n');
  //alert (area.firstChild.value);
  area.parentNode.setAttribute('display','inline');
  area.parentNode.setAttribute('visibility','visible');
}

dragDrop.prototype.change = function(e) {
  if (this.edit) {
    change_node_content(this.edit.id,$('.area').firstChild.value);
    //this.edit = null;
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
  if (this.changeconnector) {
    var d = '';
    if (this.changeconnectordir) {
      d = trunk_path_curve_reverse(nodeBox[this.changeconnector],$(this.changeconnector).getCTM(),e);
    } else {
      d = trunk_path_curve_simple(nodeBox[this.changeconnector],$(this.changeconnector).getCTM(),e);
    }
    this.connector.firstChild.nextSibling.setAttribute('d',d);
  }
};

dragDrop.prototype.up = function(e) {
  // TODO: factorize nod searching  
  var nod = e.target;
  this.el=null;
  if (nod.nodeName != 'input' && nod.id != '.name') { 
    if ($('.name')) {
      $('.name').nextSibling.setAttribute('display','none'); 
    }
  }
  var found = false;
  if (this.changeconnector) {
    var found = false;
    if (nod.nodeName !== 'svg' && nod.id !== '.editor') {
      while (nod.parentNode.id != '.nodes' && nod.parentNode.id != '.editor' && nod.parentNode.nodeName != 'svg') {
	nod = nod.parentNode;
      }
      if (nod.parentNode.id == '.nodes') {
	if (test_if_connector_exist(nod.id,this.changeconnector)) {
	  found = true;
	  var n1 = this.connector.getAttribute('n1').replace('#','');
	  var n2 = this.connector.getAttribute('n2').replace('#','');
	  editor_change_connector(n1,n2,nod.id,this.changeconnectordir);
	  pop_connector(this.connector);
	  if (this.changeconnectordir) {
	    this.connector.setAttribute('n1','#'+nod.id);
	  } else {
	    this.connector.setAttribute('n2','#'+nod.id);
	  }
	  draw_connector(this.connector);
	  nodeLink[this.changeconnector].push(this.connector);
	  nodeLink[nod.id].push(this.connector);
	  //alert (print_nodes());
	}
      }
    }
    if (!found) {
      draw_connector(this.connector);
    }
    this.changeconnector = null;    
  } else if (this.border) {
    if (nod.nodeName == 'svg' || nod.id == '.editor') {
      this.delay = true;
      show_menu(e);
    } else {
      while (nod.parentNode.id != '.nodes' && nod.parentNode.id != '.editor' && nod.parentNode.nodeName != 'svg') { 
        nod = nod.parentNode;
      }
      if (nod.parentNode.id == '.editor') { 
	  this.delay = true;
	  show_menu(e);
      } else if (nod.parentNode.id == '.nodes') { 
	var n1 = this.border.getAttribute('n1').replace('#','');
	if (test_if_connector_exist(n1,nod.id)) {
	  found = true;
	  finalize_connector(this.border,nod.id,true);
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
    //alert (charCode);
    this.charCode = charCode;
    if (charCode == 46){ //del key
      if (this.connector) {
	del_connector(this.connector);
	this.connector = null;
      } else if (this.node) {
	del_node(this.node.id);
	this.c.parentNode.setAttribute('display','none');
      }
      //update();
    } else if (charCode == 112) { // F1 key
      switch_mode();
    } else if (charCode == 10 || charCode == 13) { //return key
    } else if (charCode > 31 && charCode != 127 && charCode < 65535) {} //TODO
  }
  //e.preventDefault(); if requested!
};

//---------- Authentication ----------

function create_account(obj) {
  $('pw2').setAttribute('style','display:inline');
  $('pw2').setAttribute('onchange','submit();');
  $('pw').removeAttribute('onchange');
  $('msg').setAttribute('display','inline');
  obj.setAttribute('display','none');
}

function check() {
  $('myform').submit();
}

function logout() {
  var aj = new ajax_get(true,get_base_url() + '/save_session', function(res){
			  document.location.replace(content.document.location);
			});
  aj.doGet(); 
}


//---------- Server Synchronization ----------

function fork(flag) {
  document.location.href = 'https://github.com/pelinquin/ConnectedGraph';
}

function help() {
  alert ('Help window soon!\n see https://github.com/pelinquin/ConnectedGraph');
}

// This should move to test_ui.js

function print_nodes() {
  var msg = '';
  for ( var i in nodeLink) {
    var tab = nodeLink[i];
    msg += i + '('+tab.length + ')' + concat_node_text($(i).firstChild.nextSibling.nextSibling,'|');
    for ( var j=0; j<tab.length; j++ ) {
      msg += ':'+tab[j].getAttribute('n1')+ ' ' + tab[j].getAttribute('n2'); 
    }
    msg += '\n';
  }
  return (msg);
}

//---------- Utility function ----------
// Unballanced '(' in regex make the javascript beautifuller crasy !
RegExp.quote = function(str) { 
  return str.replace(/([.?*+^$[\]\\(){}-])/g, "\\$1"); 
};

// end
