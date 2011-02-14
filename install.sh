#!/bin/sh
# Install the web application 

# need:
# apache2
# mod_python
# git
# yui-compressor

echo "clean temporary files"
rm -f "*.~" "*.pyc"

echo "compress js and css files"
yui-compressor cg.js > cgmin.js
yui-compressor cg.css > cgmin.css

echo "turn on constants"
cp cg.py cg_orig.py
cat cg_orig.py | sed -e "s|__BASE__='/tmp'|__BASE__='/db'|" | sed -e "s|__JS__='cg.js'|__JS__='cgmin.js'|" | sed -e "s|__CSS__='cg.css'|__CSS__='cgmin.css'|"> cg.py
diff cg.py cg_orig.py


echo "Run tests. All test cases should pass"
chmod +x ./cg_test.py
./cg_test.py

echo "copy the config file (edit directories for your own system)" 
sudo cp formose.conf /etc/apache2/conf.d/

echo "Restart Apache"
sudo /etc/init.d/apache2 restart 

echo "install done"