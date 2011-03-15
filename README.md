Connected Graph
===============

'Connected Graph' is an Open-source Web application for Requirements Engineering

Features
--------

* Full SVG nested diagrams for Requirements Engineering.
* A transparent Git database for persistence and version control
* Editing on the graph, on the text or on the url.
* Export to LaTeX (tikz)

Show me a demo
--------------

* look at a minimal diagram:
  http://193.84.73.209/formose/cg.py/view?@hello
* enter edit mode:
  http://193.84.73.209/formose/cg.py/edit?A->B

Where is the repository?
------------------------

* Source Code, Issue Tracker, Wiki and Download:

    https://github.com/pelinquin/ConnectedGraph

How to contribute?
------------------

* Clone the project
    git clone git://github.com/pelinquin/ConnectedGraph.git

Which Browser is currently supported?
-------------------------------------
Firefox, Chrome, Safari, Opera, (not IE)  
see browser_support.pdf for details

How to install the tool on yout own server?
-------------------------------------------

You need:
    apache2  
    libapache2-mod-python
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
'firefox http://pelinquin/formose/cg.py'

Contact: 
--------

pelinquin@gmail.com