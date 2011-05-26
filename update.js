
// Use the compressed version

//---------- constants ----------

//---------- Utilities ----------
if (typeof($)=='undefined') { 
  function $(id) { return document.getElementById(id.replace(/^#/,'')); } 
}
    
//function ajax_url (f) {
//  var s = new String(document.location);
//  return (s.replace(/edit/,f));
//}

function update_tool() {
    var ai = new ajax_get(true,gurl('/update_tool'), function(res) {
	    alert (res);
	});
    ai.doGet();
}
