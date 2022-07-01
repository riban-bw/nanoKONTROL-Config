# nanoKONTROL-Config
Configuration tool for Korg nanoKONTROL written in Python.

Supports nanoKONTROL1
![image](https://user-images.githubusercontent.com/3158323/176855965-48bac669-10b0-424b-bf8e-8a7d0fce9f3b.png)

Supports nanoKONTROL2
![image](https://user-images.githubusercontent.com/3158323/176855869-e5ef50b7-ebaf-46bb-91e6-16a9c218a28b.png)

This tool provides a graphical user interface allowing configuration of Korg nanoKONTROL1 and nanoKONTROL2 devices. Functionality is broadly similar to Korg's own configuration tool (which I have never seen!). This tool is cross platform and open source.

MIDI connection is via JACK or ALSA (or both) hence a working JACK service and/or ALSA driver must be running before starting the application. It detects new MIDI ports so the device may be connected after starting the application.

# Usage
After starting the application, select the MIDI ports to which the nanoKONTROL is connected using the drop-down lists near the top, labelled "MIDI input" and "MIDI output". This is likely to be "nanoKONTROL" or "nanoKONTROL2" unless the device is connected to another machine and MIDI routed. The picture of the device should change to to indicate the device detected.

Click the ![image](https://user-images.githubusercontent.com/3158323/176854990-1b05b67f-5ee8-4033-aa6b-4a9b08500a56.png) download button to retrieve a scene from the device.

Click on a button, slider or knob on the image and adjust its parameters using the editor on the right hand side.

Click the ![image](https://user-images.githubusercontent.com/3158323/176855266-c99b60f7-1762-4368-a889-5da36618160e.png) upload button to upload to the nanoKONTROL.

Click the ![image](https://user-images.githubusercontent.com/3158323/176855361-4ea75e8b-cff0-47c8-bb37-3cf351f40b1d.png) save button to save the scene to the nanoKONTROL's internal persistent memory.

# Dependancies

The application is written in Python3 and tested on GNU/Linux. It should run on any platform that can meet the following dependancies:

- jack (for JACK MIDI interface)
- alsa-midi (for ALSA MIDI interface)
- tkinter
- PIL
- PIL Image

On a DEBIAN based system the following may install the required Python modules:

`sudo apt install python3-jack-client python3-tk python3-pil python3-pil.imagetk`

To install alsa-midi:

```
sudo apt install python3-pip
sudo pip3 install alsa-midi
```
