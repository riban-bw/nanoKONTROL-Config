# nanoKONTROL-Config
Configuration tool for Korg nanoKONTROL written in Python.

This tool provides a graphical user interface allowing configuration of Korg nanoKONTROL1 and nanoKONTROL1 devices. Functionality is broadly similar to Korg's own configuration tool. This tool is cross platform and open source.

MIDI connection is via JACK hence a working JACK service must be running before starting the application.

# Usage
After starting the application, select the MIDI ports to which the nanoKONTROL is connected using the drop-down lists near the top, labelled "MIDI input" and "MIDI output". Click the button labelled "nanoKONTROL2" to detect the device. The label should change to "nanoKONTROL2" or "nanoKONTROL2" depending on the device detected. Click the "Get Scene" button to retrieve a scene from the device. Click on a button, slider or knob on the image and adjust its parameters using the editor on the right hand side.

Click the "Send Scene" button to upload to the nanoKONTROL.

Click the "Write Scene" button to save the scene to the nanoKONTROL's internal persistent memory.

# Dependancies

The application is written in Python3 and tested on GNU/Linux. It should run on any platform that can meet the following dependancies:

- jack
- tkinter
- PIL
- PIL Image

On a DEBIAN based system the following may install the required Python modules:

`apt install python3-jack-client python3-tk python3-pil python3-pil-imagetk`
