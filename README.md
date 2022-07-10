# nanoKONTROL-Config
Configuration tool for Korg nanoKONTROL written in Python.

Supports nanoKONTROL1
![image](https://user-images.githubusercontent.com/3158323/176915252-a606ced7-62b2-42ef-b5da-ecca2c2c3b12.png)

Supports nanoKONTROL2
![image](https://user-images.githubusercontent.com/3158323/176915182-ca7fba06-30f5-4f93-bd36-8c0c3331ee31.png)

This tool provides a graphical user interface allowing configuration of Korg nanoKONTROL1 and nanoKONTROL2 devices. Functionality is broadly similar to Korg's own configuration tool (which I have never seen!). This tool is cross platform and open source.

MIDI connection is via JACK or ALSA (or both) hence a working JACK service and/or ALSA driver must be running before starting the application. It detects new MIDI ports so the device may be connected after starting the application.

# Usage
After starting the application, select the MIDI ports to which the nanoKONTROL is connected using the drop-down lists near the top, labelled "MIDI input" and "MIDI output". This is likely to be "nanoKONTROL" or "nanoKONTROL2" unless the device is connected to another machine and MIDI routed. The picture of the device should change to to indicate the device detected.

Click the ![image](https://user-images.githubusercontent.com/3158323/176854990-1b05b67f-5ee8-4033-aa6b-4a9b08500a56.png) download button to retrieve a scene from the device.

Click on a button, slider or knob on the image and adjust its parameters using the editor on the right hand side.

Click the ![image](https://user-images.githubusercontent.com/3158323/176855266-c99b60f7-1762-4368-a889-5da36618160e.png) upload button to upload to the nanoKONTROL.

Click the ![image](https://user-images.githubusercontent.com/3158323/176855361-4ea75e8b-cff0-47c8-bb37-3cf351f40b1d.png) save button to save the scene to the nanoKONTROL's internal persistent memory.

Click the ![image](https://user-images.githubusercontent.com/3158323/176915479-baf8d65f-2365-489f-a51e-11723717cd29.png) restore button to restore the last downloaded scene. This restores locally in the application. To revert the device to its previous state you must then press the upload button.

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

On Windows 10 I found I could run the application after installing Python modules: Pillow and jack-client and installing and starting JACK. (The application crashes when trying to import jack if the JACK service is not running.)

```
python3 -m pip install --upgrade pip
pip3 install Pillow
pip3 install jack-client
```

Jack can be installed from: https://jackaudio.org/downloads. Configuring with "Dummy" audio driver may get it going quickly, e.g. if a supported soundcard is not installed. Adding "-Xwinmme" to the "Advanced" sub-tab of "Settings" tab in QjackCtrl added USB MIDI device to jack graph. I found this added two inputs and four outputs. The second input worked. Not sure about output (poor quality USB MIDI interface available for this test).

# Credits and Licensing

Released under the [GPL 3.0 software licensing](https://www.gnu.org/licenses/gpl-3.0.en.html). You may use and distribute this software free of charge. It may not be used within a closed source project. There is no liability protection of its use.

[Core code](https://github.com/riban-bw/nanoKONTROL-Config) written by [Brian Walton](http://riban.co.uk)

[Tooltips](https://github.com/PedroHenriques/Tkinter_ToolTips) provided by [Pedro Henriques](http://www.pedrojhenriques.com)

Icons from [freeicons](https://freeicons.io)

![image](https://user-images.githubusercontent.com/3158323/176854990-1b05b67f-5ee8-4033-aa6b-4a9b08500a56.png) ![image](https://user-images.githubusercontent.com/3158323/176855361-4ea75e8b-cff0-47c8-bb37-3cf351f40b1d.png) [ColourCreatype](https://freeicons.io/profile/5790)

![image](https://user-images.githubusercontent.com/3158323/176917301-d15296fb-79ab-421e-9d40-bc22f057394b.png) [MD Badsha Meah](https://freeicons.io/profile/3335)

![image](https://user-images.githubusercontent.com/3158323/176915479-baf8d65f-2365-489f-a51e-11723717cd29.png) [Anu Rocks](https://freeicons.io/profile/730)

![image](https://user-images.githubusercontent.com/3158323/178100762-9c3db76a-64b7-431c-8df6-ba40e2395564.png) [Reda](https://freeicons.io/profile/6156)
