cd Site
pyinstaller -w -F Site\Broker.py
pyinstaller -w -F Site\Site.py --add-data templates:templates --add-data static:static
pyinstaller -w -F Site\main.py -n=WinEd
cd ..\
cls