const svgns="http://www.w3.org/2000/svg";const xlinkns="http://www.w3.org/1999/xlink";const xhtmlns="http://www.w3.org/1999/xhtml";var nodeArray=[];if(typeof($)=="undefined"){function $(a){return document.getElementById(a.replace(/^#/,""))}}function is_gecko(){var a=navigator.userAgent;if(a.match("AppleWebKit")){return true}var b=a.replace(/^Mozilla.*rv:|\).*$/g,"")||(/^rv\:|\).*$/g,"");if(b.substring(0,3)=="2.0"){return true}return false}window.onload=function(){if(!is_gecko()){alert("This is tested on Firefox4 and Chromium !")}if(false){if(navigator.geolocation){var a=10*1000*1000;navigator.geolocation.watchPosition(showPositionOnMap,errorMessage,{enableHighAccuracy:true,timeout:a,maximumAge:0})}else{alert("Geolocation services are not supported by your browser.")}}};function showPositionOnMap(a){alert(a.coords.latitude+" "+a.coords.longitude)}function errorMessage(){alert("KO")}function do_something(){alert("OK")}function enterFocus(a){alert("focus")}function enterNode(c){var a=c.target;var e=a;while(a.parentNode.id!=".nodes"){a=a.parentNode}if(a.hasAttribute("href")){var d=a.getAttribute("href");var b=$(".rev").firstChild.nodeValue;if(e.parentNode.id=="attachid"){var f="gid="+d+"&rev="+b;window.open(get_base_url()+"/load_pdf?"+f,"neutral","chrome,scrollbars=yes")}else{var f="?@"+d+":"+b;document.location.replace(get_url()+f)}}}function typeTextBG(b){if(b.type=="keypress"){var a=0;if(b.charCode){a=b.charCode}else{a=b.keyCode}if(a==115){save_all(b)}else{if(a==97){mode(b)}}}}function init_graph(d){var g=$(".nodes").childNodes;for(var e=0;e<g.length;e++){if(g[e].id){new Node(g[e].id)}}var h=document.documentElement.getElementsByTagName("connector");for(var e=0,b=h.length;b>e;e++){var j=new Connector(h[e]);j.init();j.draw()}if(d==null){var f=new DragDrop();f.init($(".nodes"));var a=$(".nodes");a.addEventListener("dragenter",dragenter,false);a.addEventListener("dragover",dragover,false);a.addEventListener("drop",drop,false)}else{$(".nodes").addEventListener("click",enterNode,false)}}document.onkeydown=function(a){var c=null;if(a==null){c=window.evt.keyCode}else{c=a.keyCode}if(49==c){var d="Window:"+window.innerWidth+":"+window.innerHeight+"\n";for(var e in nodeArray){var b=nodeArray[e];d+=e+" (x: "+parseInt(b.x)+", y: "+parseInt(b.y)+"  tx: "+parseInt(b.tx)+", ty: "+parseInt(b.ty)+")\n"}}};function Node(a){this.id=null;this.el=null;this.role=null;this.title=null;this.connectors=[];this.x=0;this.y=0;this.tx=0;this.ty=0;return this.init(a)}Node.prototype.init=function(z){var A=nodeArray[z];if(!A){this.el=$(z);this.id=z;var c=this.el.lastChild;var J=this.el.lastChild.getBBox();var u=GetCentroid(this.el);this.x=u.x;this.y=u.y;var K=this.el.getCTM();this.tx=parseInt(K.e);this.ty=parseInt(K.f);nodeArray[z]=this;A=this;this.role=this.el.getAttribute("role");this.name=this.el.getAttribute("title");var B=8;var G=document.createElementNS(svgns,"g");var e="";if(this.role=="AGENT"){e=document.createElementNS(svgns,"path");e.setAttribute("fill","url(#.grad)");e.setAttribute("filter","url(#.shadow)");e.setAttribute("stroke","gray");var H=8;var s=J.x-B;var q=J.y-B;var t=J.width+2*B;var F=J.height+2*B;var I="M"+(s+H)+","+q+"l"+(t-2*H)+",0l"+H+","+(F/2)+"l"+(-H)+","+(F/2)+"l"+(2*H-t)+",0l"+(-H)+","+(-F/2)+"z";e.setAttribute("d",I)}else{if(this.role=="GOAL"){e=document.createElementNS(svgns,"path");e.setAttribute("fill","url(#.grad)");e.setAttribute("filter","url(#.shadow)");e.setAttribute("stroke","gray");var s=J.x-B;var q=J.y-B;var t=J.width+2*B;var F=J.height+2*B;var H=4;var I="M"+(s+2*H)+","+q+"l"+2*t/3+",2l"+t/3+",-2l"+(-H-2)+","+2*F/3+"l"+(-H-2)+","+F/3+"l"+(-3*t/5)+",2l"+(-2*t/5)+",-2l"+(H+2)+","+-4*F/7+"z";e.setAttribute("d",I)}else{if(this.role=="CLASS"){var k=c.childNodes;var L=[];for(var D=0;D<k.length;D++){if(k[D].hasAttribute("sep")){L.push(20*D)}}e=document.createElementNS(svgns,"path");e.setAttribute("fill","url(#.grad)");e.setAttribute("filter","url(#.shadow)");e.setAttribute("stroke","gray");var s=J.x-B;var q=J.y-B;var t=J.width+2*B;var F=J.height+2*B;var I="M"+s+","+q+"l"+t+",0l0,"+F+"l"+(-t)+",0z";for(var D=0;D<L.length;D++){I+=" M"+s+","+(q+7+L[D])+"l"+t+",0"}e.setAttribute("d",I)}else{if(this.role=="ASSOCIATION"){e=document.createElementNS(svgns,"path");e.setAttribute("fill","url(#.grad)");e.setAttribute("filter","url(#.shadow)");e.setAttribute("stroke","gray");var s=J.x-B;var q=J.y-B;var t=J.width+2*B;var F=J.height+2*B;var I="M"+s+","+q+"m"+t/2+",0l"+t/2+","+F/2+"l"+(-t/2)+","+F/2+"l"+(-t/2)+","+(-F/2)+"z";e.setAttribute("d",I)}else{if(this.role=="ENTITY"){e=document.createElementNS(svgns,"path");e.setAttribute("fill","url(#.grad)");e.setAttribute("filter","url(#.shadow)");e.setAttribute("stroke","gray");var s=J.x-B;var q=J.y-B;var t=J.width+2*B;var F=J.height+2*B;I="M"+s+","+q+"l"+t+",0l0,"+F+"l"+(-t)+",0z";e.setAttribute("d",I)}else{if(this.role=="REQUIREMENT"){e=document.createElementNS(svgns,"rect");e.setAttribute("fill","url(#.grad)");e.setAttribute("filter","url(#.shadow)");e.setAttribute("rx","4");e.setAttribute("stroke","gray");e.setAttribute("width",J.width+2*B);e.setAttribute("height",J.height+2*B);e.setAttribute("x",J.x-B);e.setAttribute("y",J.y-B);e.setAttribute("stroke-width","3");e.setAttribute("transform","skewX(-10)")}else{if(this.role=="EXPECTATION"){e=document.createElementNS(svgns,"rect");e.setAttribute("fill","url(#.grady)");e.setAttribute("filter","url(#.shadow)");e.setAttribute("rx","4");e.setAttribute("stroke","gray");e.setAttribute("width",J.width+2*B);e.setAttribute("height",J.height+2*B);e.setAttribute("x",J.x-B);e.setAttribute("y",J.y-B);e.setAttribute("stroke-width","3");e.setAttribute("transform","skewX(-10)")}else{if(this.role=="OBSTACLE"){e=document.createElementNS(svgns,"rect");e.setAttribute("fill","url(#.grad)");e.setAttribute("filter","url(#.shadow)");e.setAttribute("rx","4");e.setAttribute("stroke","gray");e.setAttribute("width",J.width+2*B);e.setAttribute("height",J.height+2*B);e.setAttribute("x",J.x-B);e.setAttribute("y",J.y-B);e.setAttribute("stroke-width","1");e.setAttribute("transform","skewX(10)");e.setAttribute("rx","2")}else{e=document.createElementNS(svgns,"path");e.setAttribute("fill","url(#.grad)");e.setAttribute("filter","url(#.shadow)");e.setAttribute("stroke","gray");var s=J.x-B;var q=J.y-B;var t=J.width+2*B;var F=J.height+2*B;var I="M"+s+","+q+"l"+2*t/3+",2l"+t/3+",-2l2,"+2*F/3+"l-2,"+F/3+"l"+(-3*t/5)+",2l"+(-2*t/5)+",-2l2,"+-4*F/7+"z";e.setAttribute("d",I)}}}}}}}}G.appendChild(e);if(this.role!=null){if(this.role!="CLASS"){var v=document.createElementNS(svgns,"text");var C=document.createTextNode(this.role);if(this.role=="OBSTACLE"){v.setAttribute("x","-6")}v.setAttribute("y","-14");v.setAttribute("fill","gray");v.setAttribute("style","font-family:Arial;font-size:3pt;");v.appendChild(C);G.appendChild(v)}var j=document.createElementNS(svgns,"text");var m=document.createTextNode(this.name);j.setAttribute("x",J.width-(this.name.length*5));j.setAttribute("y",J.height-8);j.setAttribute("fill","white");j.setAttribute("style","font-family:Arial;font-size:5pt;font-weight:bold;");j.appendChild(m);G.appendChild(j)}if(this.el.hasAttribute("attach")){G.appendChild(attach_icon(J.width))}this.el.insertBefore(G,this.el.firstChild);var a=document.createElementNS(svgns,"g");a.setAttribute("display","none");var o=document.createElementNS(svgns,"foreignObject");var E=J.x+J.width/2-100;var l=J.y+J.height/2-50;var r=200;var n=100;o.setAttribute("width",r);o.setAttribute("height",n);o.setAttribute("x",E);o.setAttribute("y",l);var p=document.createElementNS(xhtmlns,"textarea");p.setAttribute("style","background-color: lightyellow; padding:1px 1px 1px 1px; border:1px solid #ccc");p.setAttribute("onblur","blur_node(this);");p.setAttribute("onfocus","focus_node(this);");p.setAttribute("focusable","true");p.setAttribute("tabindex","1");p.setAttribute("spellcheck","false");p.setAttribute("style","resize:none; border:1px solid #ccc;width:"+(r-2)+"px;height:"+(n-3)+"px");p.value=this.el.getAttribute("label");o.appendChild(p);a.appendChild(o);if(this.role!=null){var v=document.createElementNS(svgns,"text");var C=document.createTextNode(this.role);v.appendChild(C);v.setAttribute("fill","gray");v.setAttribute("x",E);v.setAttribute("y",l);v.setAttribute("style","font-family:Arial;font-size:5pt;");a.appendChild(v)}this.el.appendChild(a)}return A};function attach_icon(a){var e=document.createElementNS(svgns,"g");e.setAttribute("transform","translate("+(a+12)+",-20) scale(0.32)");e.setAttribute("class","attach");e.setAttribute("id","attachid");var c=document.createElementNS(svgns,"rect");c.setAttribute("width","42");c.setAttribute("fill","none");c.setAttribute("height","47");e.appendChild(c);var d=document.createElementNS(svgns,"path");d.setAttribute("stroke-linecap","round");d.setAttribute("fill","none");d.setAttribute("stroke","#6bc62e");d.setAttribute("stroke-width","3");d.setAttribute("d",get_attach());e.appendChild(d);var b=document.createElementNS(svgns,"title");b.appendChild(document.createTextNode("attached PDF document"));e.appendChild(b);return e}function attach(){var a="&gid="+$(".gid").firstChild.nodeValue;window.open(get_base_url()+"/load_pdf?"+user_ip()+a,"neutral","chrome,scrollbars=yes")}function save_attach(){var a=$("fileElem");if(a){a.click()}}function new_attach(a,e,k){for(var d=0;d<a.length;d++){var c=a[d];var f="AaB03x";var g=escape(c.getAsBinary());var h=binary_post(f,g);var b="";if(e){b="&gid="+e+"&typ="+c.type}else{b="&gid="+$(".gid").firstChild.nodeValue+"&typ="+c.type}var j=new ajax_post(true,get_base_url()+"/new_attach?"+user_ip()+b,h,f,function(l){var i=k.firstChild.nextSibling.getBBox();k.firstChild.appendChild(attach_icon(i.width))});j.doPost()}}function get_attach(){return"m21.615,8.81l-11.837,19.94l-0.349,2.68l0.582,2.67l1.28,1.746l5.122,3.14l2.79,0.35l2.095,-0.46l1.746,-1.047l1.746,-2.095l11.990,-20.838l0.698,-2.91l-0.465,-2.444l-1.28,-2.095l-1.746,-0.931l-1.979,-0.349l-1.629,0.349l-1.513,0.582l-1.746,1.28l-1.047,1.746l-9.08,16.065l-0.698,2.44l0.465,1.98l0.931,1.047l1.746,0.349l1.629,-0.814l1.164,-1.164l1.28,-1.63l4.656,-7.79l0.46,-0.81"}function GetCentroid(b){var a=document.documentElement.createSVGPoint();var c=b.getBBox();a.x=c.x+(c.width/2);a.y=c.y+(c.height/2);return a}function Connector(a){this.el=a;this.path=null;this.circle=null;this.n1=null;this.n2=[];this.b1=null;this.b2=[];this.type=null}Connector.prototype.init=function(){var a=this.el.getAttribute("n1").replace("#","");this.n1=nodeArray[a];this.n1.connectors.push(this);this.b1=$(a).lastChild.previousSibling.getBBox();var e=this.el.getAttribute("n2").replace("#","");var d=e.split(":");for(var c=0;c<d.length;c++){var b=nodeArray[d[c]];b.connectors.push(this);this.n2.push(b);this.b2.push($(d[c]).lastChild.previousSibling.getBBox())}if(this.el.hasAttribute("type")){this.type=this.el.getAttribute("type")}};Connector.prototype.draw=function(){var c=this.n1.x+this.n1.tx;var s=this.n1.y+this.n1.ty;var q=10+this.b1.height/2;var g=10+this.b1.width/2;if(window.focusNode!=null){if(window.focusNode.parentNode.id==this.n1.id){q=50;g=100}}var b=0;var r=0;var e=this.n2.length;for(var j=0;j<e;j++){b+=this.n2[j].x+this.n2[j].tx;r+=this.n2[j].y+this.n2[j].ty}b=b/e;r=r/e;if(c==b){if(s<r){s+=q}else{s-=q}}else{if(s==r){if(c<b){c+=g}else{c-=g}}else{var k=c-b;var h=s-r;var l=k/h;if(Math.abs(l)<g/q){if(h<0){s+=q;c+=q*l}else{s-=q;c-=q*l}}else{if(k<0){c+=g;s+=g/l}else{c-=g;s-=g/l}}}}b=(c+b)/2;r=(s+r)/2;var o="";if(!this.path){this.path=document.createElementNS(svgns,"path");this.path.setAttribute("fill","none");this.path.setAttribute("stroke","gray");this.path.setAttribute("stroke-width","2");if(this.type=="conflict"){this.path.setAttribute("marker-mid","url(#.conflict)")}else{if(this.type){this.path.setAttribute("marker-start","url(#.simple_start)");this.path.setAttribute("marker-end","url(#.simple_end)")}else{this.path.setAttribute("marker-end","url(#.arrow)")}}this.el.parentNode.appendChild(this.path);if(e>1){this.circle=document.createElementNS(svgns,"circle");this.circle.setAttribute("fill","url(#.gradyellow)");this.circle.setAttribute("r","6");this.circle.setAttribute("stroke","gray");this.circle.setAttribute("stroke-width","1");this.el.parentNode.appendChild(this.circle)}}for(var j=0;j<this.n2.length;j++){var a=this.n2[j].x+this.n2[j].tx;var p=this.n2[j].y+this.n2[j].ty;var m=10+this.b2[j].height/2;var f=10+this.b2[j].width/2;if(window.focusNode!=null){if(window.focusNode.parentNode.id==this.n2[j].id){m=50;f=100}}if(a==b){if(p<r){p+=m}else{p-=m}}else{if(p==r){if(a<b){a+=f}else{a-=f}}else{var k=a-b;var h=p-r;var l=k/h;if(Math.abs(l)<f/m){if(h<0){p+=m;a+=m*l}else{p-=m;a-=m*l}}else{if(k<0){a+=f;p+=f/l}else{a-=f;p-=f/l}}}}o+="M"+a+","+p+"L"+b+","+r}o+=" "+c+","+s;this.path.setAttribute("d",o);if(e>1){this.circle.setAttribute("cx",b);this.circle.setAttribute("cy",r)}};function GetCentroid(b){var a=document.documentElement.createSVGPoint();var c=b.getBBox();a.x=c.x+(c.width/2);a.y=c.y+(c.height/2);return a}function DragDrop(){this.dragEl=null;this.targetEl=null;this.m=null;this.p=null;this.offset=null;this.tx=null;this.ty=null;this.d=false}DragDrop.prototype.init=function(a){var b=this;a.addEventListener("mousedown",function(c){b.grab(c)},false);document.documentElement.addEventListener("mousemove",function(c){b.drag(c)},false);document.documentElement.addEventListener("mouseup",function(c){b.drop(c)},false);this.p=document.documentElement.createSVGPoint();this.offset=document.documentElement.createSVGPoint();window.focusNode=null};function update_connectors(b){var c=nodeArray[b.id].connectors;for(var a=0;c.length>a;a++){c[a].draw()}}DragDrop.prototype.grab=function(h){if(!h){var h=window.event}var i=h.target;var d=i;while(i.parentNode.id!=".nodes"){i=i.parentNode}var f=i.lastChild;if(h.shiftKey){if(window.focusNode){alert("update");update_g()}if(f.getAttribute("display")=="none"){f.setAttribute("display","inline");window.focusNode=f;update_connectors(i);var b=f.firstChild.firstChild;b.select();b.focus()}else{alert("off");window.focusNode=null;f.setAttribute("display","none");update_connectors(i)}}if(h.detail==2){if(f.getAttribute("display")!="inline"){if(i.hasAttribute("href")){if(d.parentNode.id=="attachid"){var c=$(".rev").firstChild.nodeValue;var g="gid="+i.getAttribute("href")+"&rev="+$(".rev").firstChild.nodeValue;window.open(get_base_url()+"/load_pdf?"+g,"neutral","chrome,scrollbars=yes")}else{var e=get_layout()+"\n"+$(".area").value;save_and_reload(get_url(),$(".gid").firstChild.nodeValue,e,i.getAttribute("href"))}}else{new_graph(i)}this.dragEl=null}}else{this.dragEl=i}if(this.dragEl){this.dragEl.parentNode.appendChild(this.dragEl);this.dragEl.setAttribute("pointer-events","none");this.m=document.documentElement.getScreenCTM();this.p.x=h.clientX;this.p.y=h.clientY;this.p=this.p.matrixTransform(this.m.inverse());var a=this.dragEl.getCTM();this.offset.x=this.p.x-parseInt(a.e);this.offset.y=this.p.y-parseInt(a.f)}};DragDrop.prototype.drag=function(c){if(this.dragEl){this.d=true;var b=nodeArray[this.dragEl.id];this.m=document.documentElement.getScreenCTM();this.p.x=c.clientX;this.p.y=c.clientY;this.p=this.p.matrixTransform(this.m.inverse());this.p.x-=this.offset.x;this.p.y-=this.offset.y;this.tx=this.p.x;this.ty=this.p.y;this.dragEl.setAttribute("transform","translate("+this.tx+","+this.ty+")");var b=nodeArray[this.dragEl.id];if(b){b.tx=this.p.x;b.ty=this.p.y;for(var a=0;b.connectors.length>a;a++){b.connectors[a].draw()}}}};DragDrop.prototype.drop=function(){if(this.dragEl){if(this.d){change_title(true);if($(".canvas").getAttribute("unsaved")=="no"){$(".canvas").setAttribute("unsaved","layout")}this.d=false}this.dragEl.setAttribute("pointer-events","all");this.dragEl=null}};function DragDrop1(){this.dragEl=null;this.targetEl=null;this.m=null;this.p=null;this.offset=null;this.tx=null;this.ty=null}DragDrop1.prototype.init=function(a){var b=this;a.addEventListener("mousedown",function(c){b.grab(c)},false);document.documentElement.addEventListener("mousemove",function(c){b.drag(c)},false);document.documentElement.addEventListener("mouseup",function(c){b.drop(c)},false);this.p=document.documentElement.createSVGPoint();this.offset=document.documentElement.createSVGPoint();window.focusNode=null};DragDrop1.prototype.grab=function(c){var a=c.target;while(a.parentNode.id!=".nodes"){a=a.parentNode}this.dragEl=a;if(this.dragEl){this.dragEl.setAttribute("pointer-events","none");var b=this.dragEl.getCTM()}};DragDrop1.prototype.drag=function(b){if(this.dragEl){var a=nodeArray[this.dragEl.id]}};DragDrop1.prototype.drop=function(b){if(this.dragEl){alert("drop");var a=b.target;if(a.nodeName!="svg"){while(a.parentNode.id!=".nodes"){a=a.parentNode}this.dragEl.setAttribute("pointer-events","all")}}this.dragEl=null};function get_layout(){var b="";for(var c in nodeArray){var a=nodeArray[c];b+=c+":"+a.tx+":"+a.ty+" "}return(b)}function short_content(a){if(a.length>=35){return(a.substring(0,33)+"...")}return(a)}function user_ip(){return"&user="+$(".user").firstChild.nodeValue+"&ip="+$(".ip").firstChild.nodeValue}function new_graph(b){var e="AaB03x";var d=$(".gid").firstChild.nodeValue;var f="name="+b.id+"&parent="+d+user_ip();var c=binary_post(e,get_layout()+"\n"+$(".area").value);var a=new ajax_post(true,get_base_url()+"/new_graph?"+f,c,e,function(g){document.location.replace(get_url()+"?@"+g)});a.doPost()}function save_up(a){var d=$(".parent");if(d.hasAttribute("href")){var c=get_layout()+"\n"+$(".area").value;var b=$(".gid").firstChild.nodeValue;save_and_reload(get_url(),b,c,d.getAttribute("href"))}}function go_up(a){var b=$(".parent");if(b.hasAttribute("href")){var c="@"+b.getAttribute("href")+":"+$(".rev").firstChild.nodeValue.substring(0,15);document.location.replace(get_url()+"?"+c)}}function load_item(b){if(b.target.nodeName=="tspan"){var a=b.target;if(!a.hasAttribute("gid")){a=a.parentNode}document.location.replace(get_url()+"/edit?@"+a.getAttribute("gid"))}}function record_tag(){alert($(".tag").value);$(".tag").value=""}function save_all(a){if(a.target.nodeName=="tspan"){document.location.replace(get_url()+"?"+a.target.getAttribute("rev"))}else{if(a.target.nodeName=="input"){}else{if($(".canvas").getAttribute("unsaved")=="all"){save_content()}else{if($(".canvas").getAttribute("unsaved")=="layout"){save_layout()}}$(".canvas").setAttribute("unsaved","no");change_title(false)}}}function save_layout(){param="lout="+get_layout()+"&gid="+$(".gid").firstChild.nodeValue+user_ip();var a=new ajax_get(true,get_base_url()+"/save_layout?"+param,function(b){$(".rev").firstChild.nodeValue=b});a.doGet()}function save_content(){var e="";var d="AaB03x";var c=$(".gid").firstChild.nodeValue;var b=binary_post(d,get_layout()+"\n"+$(".area").value);var a=new ajax_post(true,get_base_url()+"/save_content?gid="+c+"&msg="+escape(e)+user_ip(),b,d,function(f){$(".rev").firstChild.nodeValue=f});a.doPost()}function save_and_reload(d,e,f,b){var g="AaB03x";var c=binary_post(g,f);var a=new ajax_post(true,get_base_url()+"/save_content?gid="+e+user_ip(),c,g,function(h){document.location.replace(d+"?@"+b)});a.doPost()}function get_url(){var b=new String(document.location);var a=b;a=a.replace(/\?.*$/,"");return(a)}function get_base_url(){var a=get_url().replace(/\/[^\/]*$/,"");return(a)}function save_session(){var c="txt";if($(".textarea").getAttribute("display")=="none"){c="graph"}var a=$(".user").firstChild.nodeValue;var b=new String(document.location);var d=new ajax_get(true,get_base_url()+"/save_session?mode="+c+"&user="+a,function(e){});d.doGet()}function ajax_get(b,d,a){var e=new XMLHttpRequest();e.onreadystatechange=c;function c(){if(e.readyState==4){if(e.status==200||e.status==0){if(a){if(b){a(e.responseText)}else{a(e.responseXML)}}}else{alert("Error Get status:"+e.status)}}}this.doGet=function(){e.open("GET",d);e.send(null)}}function ajax_post(b,d,g,f,a){var e=new XMLHttpRequest();e.onreadystatechange=c;function c(){if(e.readyState==4){if(e.status==200){if(a){if(b){a(e.responseText)}else{a(e.responseXML)}}}else{alert("Error Post status:"+e.status)}}}this.doPost=function(){e.open("POST",d,true);e.setRequestHeader("Content-Type",'multipart/form-data; boundary="'+f+'"');e.setRequestHeader("Content-length",g.length);e.setRequestHeader("Connection","close");e.send(g)}}function mode(g){var d=$(".wmode");var c=$(".rmode");var f=$(".canvas");var h=$(".textarea");if(f.getAttribute("display")=="none"){d.setAttribute("display","inline");c.setAttribute("display","none");f.setAttribute("display","inline");h.setAttribute("display","none");if($(".canvas").getAttribute("updated")=="no"){update_graph();$(".canvas").setAttribute("updated","yes")}else{if($(".canvas").getAttribute("jsdone")=="no"){init_graph();$(".canvas").setAttribute("jsdone","yes")}}}else{d.setAttribute("display","none");c.setAttribute("display","inline");f.setAttribute("display","none");h.setAttribute("display","inline")}save_session()}function change_title(b){var a=$(".title").firstChild.nodeValue;if(b){if(a.substring(0,1)!="*"){$(".title").firstChild.nodeValue="*"+a}}else{if(a.substring(0,1)=="*"){$(".title").firstChild.nodeValue=a.substring(1)}}}function change_textarea(){change_title(true);$(".canvas").setAttribute("updated","no");$(".canvas").setAttribute("unsaved","all")}function binary_post(c,b){var a="--"+c+'\ncontent-disposition: form-data; name="g"; filename="B"\nContent-Type: application/octet-stream\nContent-Transfer-Encoding: binary\r\n\r\n'+b+"\r\n--"+c+"\n";return(a)}function update_graph(){var d="AaB03x";var b=binary_post(d,$(".area").value);var c=$(".gid").firstChild.nodeValue;$(".content").firstChild.nodeValue=short_content($(".area").value);var a=new ajax_post(false,get_base_url()+"/update_graph?gid="+c+user_ip(),b,d,function(f){var e=$(".canvas");e.replaceChild(cl_xml(f),e.firstChild);nodeArray=[];init_graph()});a.doPost()}function cl_xml(a){return document.importNode(a.documentElement.cloneNode(true),true)}function update_url(c,a){var b="";if(c.target.id==".rev"){b=$(".rev").firstChild.nodeValue}else{if(c.target.id==".gid"){b="@"+$(".gid").firstChild.nodeValue}else{if(c.target.id==".content"){b=$(".area").value.replace(/#/g,"$");b=b.replace(/\n/g,"\\n")}else{if(c.target.id==".date"){b=$(".rev").firstChild.nodeValue}}}}if(a){document.location.replace(get_url()+"?"+b)}else{$("linkstring").parentNode.setAttribute("display","inline");$("linkstring").value=get_url()+"?"+b;$("linkstring").select();$("linkstring").focus();c.stopPropagation()}}function closelink(){$("linkstring").parentNode.setAttribute("display","none")}function typeText(b){if(b.type=="keypress"){if(b.charCode){var a=b.charCode}else{var a=b.keyCode}if(a==46){window.txt="";stopTyping(b)}else{if(a==8){window.txt=window.txt.substring(0,window.txt.length-1)}else{if(a==10||a==13){stopTyping(b)}else{if(a>31&&a!=127&&a<65535){window.txt+=String.fromCharCode(a)}}}}}b.preventDefault()}function initTyping(a){if(!window.typeinit){window.txt=window.tg.firstChild.nodeValue;window.src=window.tg.firstChild.nodeValue;document.documentElement.addEventListener("keypress",typeText,false);document.documentElement.addEventListener("click",stopTyping,false);window.typeinit=true}a.stopPropagation()}function stopTyping(a){document.documentElement.removeEventListener("keypress",typeText,false);document.documentElement.removeEventListener("click",stopTyping,false);if(window.src!=window.txt){if(window.typeinit){alert("stop")}}window.typeinit=false}function blur_node(a){if(window.focusNode){update_g()}}function focus_node(a){}function edit_node_old(a,b){if(typeof window.typeinit=="undefined"){window.typeinit=false}if(b){window.typeinit=false}else{if(a.target.nodeName=="text"){if(!window.typeinit){window.tg=a.target;initTyping(a)}}}}function update_g(){window.focusNode.setAttribute("display","none");var e="AaB03x";var b=binary_post(e,$(".area").value);var d=$(".gid").firstChild.nodeValue;$(".content").firstChild.nodeValue=short_content($(".area").value);var c=$(".area").value;var f="name="+window.focusNode.parentNode.id+"&label="+escape(window.focusNode.firstChild.firstChild.value);var a=new ajax_post(true,get_base_url()+"/update_g?"+f,b,e,function(g){if(g!=c){$(".canvas").setAttribute("unsaved","all");change_title(true);$(".area").value=g;update_graph()}});a.doPost();window.focusNode=null}function add_node(f){var d=f.target.parentNode;while(!d.hasAttribute("id")){d=d.parentNode}var c=d.id;var a=d.getAttribute("cl");var g=c;var b=0;while($(".area").value.match(g)){b+=1;g=c+b}$(".area").value+="\n"+g+":"+a;update_graph();$(".canvas").setAttribute("unsaved","all");change_title(true)}function check(){$("myform").submit()}function login(){$(".form").setAttribute("display","inline");$("pw2").setAttribute("style","display:none");$(".status").firstChild.nodeValue=""}function logout(){var a=new ajax_get(true,get_base_url()+"/save_session",function(b){document.location.replace(content.document.location)});a.doGet()}function create(){$(".form").setAttribute("display","inline");$("pw2").setAttribute("style","display:inline");$(".status").firstChild.nodeValue=""}function to_connect(a){if($("_connect").getAttribute("state")=="on"){$("_connect").setAttribute("state","off")}else{$("_connect").setAttribute("state","on")}alert($("_connect").getAttribute("state"))}function load_github(){document.location.replace("https://github.com/pelinquin/ConnectedGraph")}function dragenter(a){a.stopPropagation();a.preventDefault()}function dragover(a){a.stopPropagation();a.preventDefault()}function drop(b){nod=b.target;while(nod.parentNode.id!=".nodes"){nod=nod.parentNode}if(nod.hasAttribute("href")){var a=nod.getAttribute("href");new_attach(b.dataTransfer.files,a,nod)}else{alert("drop on an non leaf node!")}b.stopPropagation();b.preventDefault()};