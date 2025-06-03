cd Third
pyinstaller -w -F Site\Broker.py
pyinstaller -w -F Site\Site.py --add-data Site\templates:templates --add-data Site\static:static
pyinstaller -F Site\main.py -n=WinEd --add-data dist\Broker.exe:Broker.exe --add-data dist\Site.exe:Site.exe
del dist\Broker.exe dist\Site.exe
cd ..\
cls