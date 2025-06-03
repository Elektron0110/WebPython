cd Site
pyinstaller -w -F Broker.py
pyinstaller -w -F Site.py --add-data templates:templates --add-data static:static
pyinstaller -w -F main.py -n=WinEd
cd ..\
cls