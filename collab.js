//----------------------------------------------------------------------------
// ©  Copyright 2011 Rockwell Collins, Inc 
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

// Use the compressed version

//---------- constants ----------

const READ_PERIOD_MS = 1000;
const WRITE_DELAY_MS = 1000;
const SLEEP_COUNTER = 20;
const KEEP_ALIVE_COUNTER = 30;

//---------- Utilities ----------
    
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

//---------- Globals ----------
var editor   = null; // Pointer to ACE editor
var saved_doc = '';  // Old editor content
var sleepCount = SLEEP_COUNTER; 

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
};

addLoadEvent ( function () {  
	if ($('.editor').nodeName == 'div') {
	    init_editor(true);
	} else {
	    init_editor(false);
	}
	if ($('.save')) {
	    document.documentElement.addEventListener('mousemove', bp_event, false);
	    document.documentElement.addEventListener('keydown', bp_event, false);
	    read_doc(0);
	}
    });
    
function init_editor(is_ace) {
  if (is_ace) {
      $('.editor').parentNode.setAttribute('display','none');
    editor = ace.edit('.editor'); 
    editor.setTheme('ace/theme/twilight');
    var pMode = require('ace/mode/python').Mode;
    editor.getSession().setMode(new pMode());
    //editor.getSession().doc.on('change', change_editor);
    $('.editor').parentNode.setAttribute('display','inline');
  } 
  $('.editor').addEventListener('keyup', change_editor, false);
  saved_doc = get_editor(); 
}

function change_editor(evt) {
  /////
  //alert ('change');
  //$('.debug').firstChild.nodeValue = $('.editor').firstChild.nodeValue;
  //TODO; link editor content with current diagram!
  //show_menu();
  //Parsing on client side
  update();
  //alert (evt.data.lines);
  //parse_editor(get_editor());
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

function bp_event (evt) {
  sleepCount = SLEEP_COUNTER;
}

//---------- New Document ----------

function gurl (f) {
  var s = new String(document.location);
  return (s.replace(/\?.*$/,'').replace(/\/[^\/]*$/,f));
}

function new_doc() {
    //alert (gurl('/new_doc'));
    var ai = new ajax_get(true,gurl('/new_doc'), function(res) {
	    document.location.href = gurl('/edit?id='+res);
	    //window.open(url);
	});
    ai.doGet();
}

function change_name(first) {
  var inp = $('.name').nextSibling;
  if (first) {
    inp.firstChild.firstChild.value = $('.name').firstChild.nodeValue;
    inp.setAttribute('display','inline');
  } else {
    $('.name').firstChild.nodeValue = inp.firstChild.firstChild.value;
    inp.setAttribute('display','none');
    update();
  }
}
	
function open_doc(e) {
  if (!e.target.hasAttribute('class')) {
    //document.location.href = get_base_url()+ '/edit?id='+e.target.firstChild.nodeValue;
    window.open(get_base_url()+ '/edit?id='+e.target.firstChild.firstChild.nodeValue);
  }
}

function ajax_url (f) {
  var s = new String(document.location);
  return (s.replace(/edit/,f));
}

function save_doc() {
    //$('.debug').firstChild.nodeValue = document.documentElement.getAttribute('sid');
    var lout = '{';
    var sep = '';
    //for (var n in nodeLink) {
    //var tt = $(n).getCTM();
    //lout += sep + '"' + n + '":(' + tt.e + ',' + tt.f+')';
    //sep = ',';
    //}
    var fD = new FormData();
    fD.append('content', get_editor());
    fD.append('lout', lout + '}');
    fD.append('title', $('.name').firstChild.nodeValue);
    var ai = new ajax_post(true,ajax_url('save_doc'), fD,function(res) {
	    $('.save').firstChild.nodeValue = res;
	});
    ai.doPost();
}

//---------- Server Synchronization ----------

function read_doc(n) {
  // This function call the server periodically 
  //$('.debug').firstChild.nodeValue = document.documentElement.getAttribute('sid') + ' ' + n;
  $('.debug').firstChild.nodeValue = 'debug: ' + sleepCount+ '|'+n;
  if (sleepCount>0) {
    sleepCount--;
    //alert (get_base_url() + '/read_doc?'+get_env());
    var args = '&sid=' + $('.editor').getAttribute('sid') + '&clear_timeout='+(4+KEEP_ALIVE_COUNTER*READ_PERIOD_MS/1000);
    //alert (ajax_url('load_patch')+args);
    var ai = new ajax_get(true,ajax_url('load_patch')+args, function(res) {
    	    if (res != '') {
		//$('.debug').firstChild.nodeValue = res; // debug
		apply_patch(res); 
    		saved_doc = get_editor();
	    }
    	});
    ai.doGet();
    var ai1 = new ajax_get(true,gurl('/get_shared'), function(res) {
	    var msg = '';
	    if (res !== '') {
		msg += 'Shared with:'+res;
	    } 
	    //$('.debug').firstChild.nodeValue = msg;
	});
    if (n>2) {
	//ai1.doGet();
    }
  } else {
      n++;
      if (n > KEEP_ALIVE_COUNTER) {
	  sleepCount = 1;
	  n = 0;
      }
  }
  setTimeout('read_doc('+n+')', READ_PERIOD_MS);
}

function apply_patch(patches_txt) {
  var dmp = new diff_match_patch();
  var patches = dmp.patch_fromText(patches_txt);
  var res = dmp.patch_apply(patches,get_editor());
  if (!res[1]) {
    alert ('error patch_apply!');
  }
  set_editor(res[0]);
}

function get_diff_patch() {
  var dmp = new diff_match_patch();
  var txt = get_editor();
  var patch_list = dmp.patch_make(saved_doc,txt);
  saved_doc = txt;
  return (dmp.patch_toText(patch_list));
}

function save_patch() {
  // update page title to "unsaved" 
    $('.title').firstChild.nodeValue = '* ';//+stat();
  if ($('.save')) { $('.save').firstChild.nodeValue = 'Save'; }
  if ($('.save')) { 
      // This function call the server on change event of editor content 
      var fD = new FormData();
      fD.append('patch', get_diff_patch());
      fD.append('sid', $('.editor').getAttribute('sid'));
      var ai = new ajax_post(true,ajax_url('save_patch'), fD,function(res) {
	  });
      ai.doPost();
  }   
}

function update(real) {
    if (typeof(this.local_update) == 'undefined') { this.local_update = false;}
    if (typeof(this.timer_update) == 'undefined') { this.timer_update = null;}
    if (typeof(real) == 'undefined') {
	if (this.local_update) { // re-arm timer
	    clearTimeout(this.timer_update);
	}
	this.local_update = true;
	this.timer_update = setTimeout('update(true)', WRITE_DELAY_MS);
    } else {
	save_patch();
	this.local_update = false;
    }
}
// end
