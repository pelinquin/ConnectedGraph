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

// Use the compressed version: uimin.js

var good = 0;
var bad = 0;

function assertEquals(msg, expected, actual) {
  if (typeof actual == 'undefined') {
    actual = expected;
    expected = msg;
    msg = 'Expected: \'' + expected + '\' Computed: \'' + actual + '\'';
  }
  if (expected === actual) {
      add_entry('OK','ok');
      good++;
  } else {
      add_entry('Fail! '+msg,'fail');
      bad++;
  }
}


//---------- Init ----------

addLoadEvent (function init_graph () {  
	var ai = new ajax_get(true,document.location + '/json', function(res) {
		add_entry('Test JSON connectors');
		var tab = eval('('+res+')');
		var n = 0;
		for(var k in tab){
		    n += 1;
		    assertEquals(tab[k],parse_editor(k));
		}
		add_entry(n + ' tests cases ');
	    });
	ai.doGet();	
    });


function add_entry(content,cas) {
    var entry = document.createElementNS(svgns, 'tspan');
    if (cas == undefined) {
	entry.setAttribute('x',0);
	entry.setAttribute('dy',18);
    } else {
	entry.setAttribute('x',150);
	if (cas=='ok') {
	    entry.setAttribute('fill','green');
	} else {
	    entry.setAttribute('fill','red');
	}
    }
    entry.appendChild(document.createTextNode(content));
    $('.results').appendChild(entry); 
}
