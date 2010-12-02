#!/bin/sh
# Install the web application 

# need:
# apache2
# mod_python
# git
# yui-compressor

# clean temporary files
rm -f "*.~" "*.pyc"

# compress js file
yui-compressor cg.js > cgmin.js

# Run tests. All test cases should pass
chmod +x ./cg_test.py
./cg_test.py

# copy the config file (edit directories for your own system) 
sudo cp formose.conf /etc/apache2/conf.d/

# Restart Apache
sudo /etc/init.d/apache2 restart 

echo "install done"