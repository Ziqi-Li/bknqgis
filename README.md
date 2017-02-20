# bknqgis
An interactive map maker in QGIS


Gallary
------------
Check this out: http://www.ziqi-li.info/bknqgis.html   
Or this County-Level Voting Map Example: http://www.ziqi-li.info/vote.html   
![QGIS](img/QGIS.tiff)
![BK](img/Bk.tiff)

UI
------------
Basic Settings:
![Basic](img/Basic_UI.tiff)   
Advanced Settings:
![BK](img/Advanced.tiff)

Installation
------------
This plugin is built upon Bokeh and GeoPandas, please make sure you have those two packages or you could install by using `pip` or `easy_install`. If you have multiple Pythons on your machine, please make sure you install those two packages to the Python QGIS uses.

```
pip install bokeh
pip install geopandas
```
Then download the repo and put into the QGIS plugin folder.
**Linux:**
```
/share/qgis/python/plugins
or
/$HOME/.qgis/python/plugins
```
**Mac:**
```
/Contents/MacOS/share/qgis/python/plugins
or
/Users/$USERNAME/.qgis/python/plugins
```
**Windows:**
```
C:\Program Files\QGIS\python\plugins
or
C:\Documents and Settings\$USERNAME\.qgis\python\plugins
```
