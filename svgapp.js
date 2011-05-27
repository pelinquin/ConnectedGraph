const svgns   = 'http://www.w3.org/2000/svg';
const xlinkns = 'http://www.w3.org/1999/xlink';
if (typeof($)=='undefined') { 
    function $(id) { return document.getElementById(id.replace(/^#/,'')); } 
                };
                                                    
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
