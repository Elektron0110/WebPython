echo off
cd Third
rem pyinstaller -w -F Site\Broker.py
rem pyinstaller -w -F Site\Site.py --add-data Site\templates:templates --add-data Site\static:static -n="Site v.Win.Ed.4"
rem pyinstaller -F Site\main.py -n=v.WinEd.42 --add-data "dist\Broker.exe:." --add-data "dist\Site.exe:."
rem del dist\Broker.exe dist\Site.exe
pyinstaller -w -F Site\main.py --add-data Site\templates:templates --add-data Site\static:static -n="Site v.Win.Ed.4"
cd ..\