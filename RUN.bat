@echo off

TITLE SPOTIFY EEG

::set SPOTIFY_ID=123456789
::set /p SPOTIFY_TOKEN=Enter your spotify token:

ECHO LOADING...

start /min python eegmusic.py

::cmd /k