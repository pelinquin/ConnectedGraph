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

// This is used only for testing javascript on client side
// Look at test_server.py for testing on server side

function clear_all() {
  nodeLink = [];
  nodeBox = [];
}

var tests = [ 'test_add_node',
	      'test_add_connector',
	      'test_editor',
	      'test_clear',
	      'test_add_del',
	      'test_add_del1',
	      'test_flip',
	      ];

function test_add_node() {
  add_node('n1','Goal','lab1',100,100);
  assertEquals('n1(0)lab1\n',print_nodes());
}

function test_add_connector() {
  add_node('n2','Goal','lab2',120,120); 
  add_connector('n1','n2');
  assertEquals('n1(1)lab1:#n1 #n2\nn2(1)lab2:#n1 #n2\n',print_nodes());
}

function test_editor() {
  assertEquals('n1(lab1):Goal\nn2(lab2):Goal\nn1->n2',get_editor());
} 

function test_clear() {
  del_node('n1');
  del_node('n2');
  assertEquals('',print_nodes() + get_editor());
}

function test_add_del() {
  add_node('n1','Goal','lab1',120,120); 
  add_node('n2','Goal','lab2',120,120); 
  add_connector('n1','n2');
  del_node('n1');
  assertEquals('n2(lab2):Goal',get_editor());
  del_node('n2');
}

function test_add_del1() {
  add_node('n1','Goal','lab1',120,120); 
  add_node('n2','Goal','lab2',120,120); 
  add_connector('n1','n2');
  del_link('n1','n2');
  assertEquals('n1(lab1):Goal\nn2(lab2):Goal',get_editor());
  del_node('n2');
  del_node('n1');
}

function test_flip() {
  add_node('n1','Goal','lab1',10,10); 
  add_node('n2','Requirement','lab2',10,10); 
  add_connector('n1','n2');
  flip_link('n1','n2');
  assertEquals('n1(lab1):Goal\nn2(lab2):Requirement\nn2->n1',get_editor());
  del_node('n1');
  del_node('n2');
}

///////////////////////////// glue ////////////////////

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

function get_root_url () { 
  return (get_base_url().replace(/\/[^\/]*$/,''));
}


function test_server() {
  call_python('run_server');
}

function update_tool() {
  call_python('update_tool');
}

function call_python(f) {
  add_entry('* '+f);
  var ai = new ajax_get(true,get_url() + '/'+f, function(res) {
			  var tab = res.split('\n');
			  for (var n=0; n<tab.length; n++) {
			    add_entry(tab[n]);
			  }
			});
  ai.doGet();
}

function run_tests() {
  good = 0;
  bad = 0;
  var startTime = (new Date()).getTime();
  add_entry('* Client side tests:');
  for (var x = 0; x < tests.length; x++) {
    add_entry('Test: \''+ tests[x] + '\'');
    eval(tests[x] + '()');
  }
  var endTime = (new Date()).getTime();
  add_entry('Tests passed: ' + good + ' Tests failed: ' + bad + ' Total time: ' + (endTime - startTime) + ' ms');
  test_server();

  var ai = new ajax_get(true,get_url() + '/json', function(res) {
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
}

function reload() {
  document.location.href = get_base_url()+'/ui.py/edit';
}
