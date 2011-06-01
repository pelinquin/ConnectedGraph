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

const svgns   = 'http://www.w3.org/2000/svg';
const xlinkns = 'http://www.w3.org/1999/xlink';

if (typeof($)=='undefined') { 
    function $(id) { return document.getElementById(id.replace(/^#/,'')); } 
};

if (typeof(addLoadEvent)=='undefined') { 
    function addLoadEvent(func) { 
	var oldonload = window.onload; 
	if (typeof window.onload != 'function') { 
	    window.onload = func; 
	} else { 
	    window.onload = function() { 
		if (oldonload) { oldonload(); } 
		func(); 
	    } 
	} 
    } 
};

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

function signin() { 
    $('.loginpage').setAttribute('display','inline'); 
}

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
