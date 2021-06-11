<h1>N-Predict</h1>
<h2>Spotify EEG Based Recommendations</h2>

<h2>What is this ?</h2>

This project simply makes music suggestions according to the level of liking of the music listened to with a headset that analyzes the brain waves of the user through the spotify platform, and makes more accurate recommendations <br />
*For now : this version used with potentiometer instead of  EEG device part* <br />

<h2>How it works?</h2>

![](https://github.com/MythB/Spotify-EEG-Based-Recommendations/blob/main/Media/flowchart.png)
<h2>Prerequisites</h2>

<a href="https://www.python.org/downloads/windows/">Python3</a> <br />
<a href="https://spotify.com/">Spotify</a> account <br />
Arduino Uno with <a href="https://github.com/firmata/arduino/blob/master/examples/StandardFirmata/StandardFirmata.ino">StandarFirmata</a> installed <br />

<h2>Usage</h2>

**1**. Download repo. <br />
**2**. pip install requirements.txt <br />
**3**. Go <a href="https://developer.spotify.com/documentation/general/guides/app-settings/">here.</a> Follow the instructions and register your Spotify application. <br />
IMPORTANT ! * Your Redirect URIs must be ```http://localhost:8888/```.* <br />
**4**. Open ```personaldata.py``` and set your ```client_id``` ```client_secret``` and ```arduino port```. <br />
**5**. Run ```eegmusic.py``` or simply double click ```RUN.bat``` . <br />
**6**. Login and accept permission. Thats it ! <br />


<h2>Example Window</h2>

![](https://github.com/MythB/Spotify-EEG-Based-Recommendations/blob/main/Media/examplewindow.png)

<h2>License</h2>

[MIT License](https://github.com/MythB/BombSquad-Mods/blob/master/LICENSE)
