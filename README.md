Connected Graph
===============

'Connected Graph' is an Open-source Web application for Requirements Engineering

Features
--------

* Full SVG nested diagrams for Requirements Engineering.
* A transparent Git database for persistence and version control
* Include Ace (http://ace.ajax.org) for editing
* Editing on the graph, on text or within the url.
* Export to LaTeX (tikz) and PDF
* WSGI nested application

Show me a demo
--------------

* look at a minimal diagram:
  http://193.84.73.209/formose/ui.py?hello
* enter edit mode:
  http://193.84.73.209/formose/ui.py/edit?A->B

Where is the repository?
------------------------

* Source Code, Issue Tracker, Wiki and Download:

    https://github.com/pelinquin/ConnectedGraph

How to contribute?
------------------

* Clone the project:

Run:

     git clone git://github.com/pelinquin/ConnectedGraph.git
     git submodule update --init

Which Browser is currently supported?
-------------------------------------
Firefox, Chrome, Safari, Opera, (not IE)  
see browser_support.pdf for details

How to install the tool on yout own server?
-------------------------------------------

You need:
    apache2  
    libapache2-mod-python 
    libapache2-mod-wsgi
    git-core
    yui-compressor (if someone knows a Python equivalent without JVM !)
    texlive 
    texlive-latex-extra 
    texlive-math-extra 
    texlive-fonts-extra 
    tex-gyre texlive-metapost

Optinnally:
    graphviz 
    doxigen
    trac

If you need to attach OpenOffice.org documents, you need
   openoffice > v3

* Run the install script
    sudo ./install.sh

* Run your browser on your local web app; for instance: 
    'firefox http://localhost/formose/cg.py'

Development:
------------
I just switch from mod_python publisher to mod_wsgi.
As I did not found the right Python framework for my needs, 
So I wrote wsgi middlewares from scratch.
This way I have control on each nested layer while allowing reusing of middleware

Current middleware are:
svg_app: define an svg application with user authentication
collab: manage a collaborative editor (ace)
update: manage application update with Github
graph: manage SVG diagram parsing and rendering
wsgi_cg: the wsgi application for ConnectedGraph

As each middleware may have some javascript code, the application runs with a set of javascript modules that must be called in fixed order.
I did not succed well to make middleware order call independent nor a way to avoid javascript multi declaration
mid1(mid2(mid3(app))) should behave like mid3(mid2(mid2(app)))
Help on this is wellcome

Contact: 
--------

pelinquin@gmail.com