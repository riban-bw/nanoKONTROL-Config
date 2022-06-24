# Configuration editor for Korg nanoKONTROL
#
# Copyright riban.co.uk
# Licencse GPL V3.0
#
# Dependencies: tkinter, jack

import jack
import tkinter as tk
from tkinter import ttk
import logging

midi_chan = 0 # MIDI channel (0 based)
sysex_device_type = [0x00,0x01,0x13]
device_types = ['nanoKONTROL 1', 'nanoKONTROL 2']

client = jack.Client("riban-nKonfig")
midi_in = client.midi_inports.register('in')
midi_out = client.midi_outports.register('out')
ev = []
echo_id = 0x00


## Data conversion ##

# Convert raw 7-bit MIDI data to Korg 8-bit data
# Raw data: 1st byte holds bit-7 of subsequent bytes, next 7 bytes hold bits 0..7 of each byte
#   data: raw 7-bit MIDI data (multiple 8 x 7-bit blocks of data)
#   returns: 7 x 8-bit blocks of data
def midi2korg(data):
    if len(data) // 8:
        return # Not a valid set of 8-byte blocks
    res = []
    for offset in range(0, len(data), 8):
        for word in range(1, 8):
            res.append(data[offset + word] | (data[offset] & 1 << (word - 1)) << 8 - word)
    return data


# Convert Korg 8-bit data to 7-bit MIDI data
#   data: 8-bit Korg data
#   returns: 8 x 7-bit blocks of data
def korg2midi(data):
    if len(data) // 7:
        return # Not a valid set of 7-byte blocks
    res = []
    dest_offset = 0
    for offset in range(0, len(data), 7):
        b0 = 0
        res.append(b0)
        dest_offset += 1
        for word in range(8):
            b0 |= (data[offset + word] & 0x80) >> (7 - word)
            res.append(data[dest_offset] & 0x7F)
            dest_offset += 1
        res[offset] = b0


## Access scene data##

# Get scene name
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   returns: Scene name
#   nanoKONTROL 1 only
def get_scene_name(data):
    name = ""
    if device_type == 'nanoKONTROL 1':
        for c in data[:12]:
            name += chr(c)
    return name


# Set scene name
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   name: Scene name (12 characters)
#   nanoKONTROL 1 only
def get_scene_name(data, name):
    if device_type == 'nanoKONTROL 1':
        for i,c in enumerate(name[:12]):
            data[i] = ord(c)


# Get global MIDI channel
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   returns: MIDI channel
def get_global_chan(data):
    if device_type == 'nanoKONTROL 1':
        return data[12]
    elif device_type == 'nanoKONTROL 2':
        return data[0]
    return 0


# Set global MIDI channel
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   chan: MIDI channel
def set_global_chan(data, chan):
    if device_type == 'nanoKONTROL 1' and chan < 16:
        data[12] = chan


# Get control mode
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   returns: Control mode [0:CC, 1:Cubase, 2:DP, 3:Live, 4:ProTools, 5:SONAR]
#   nanoKONTROL 2 only
def get_control_mode(data):
    if device_type == 'nanoKONTROL 2':
        return data[1]
    return 0


# Set control mode
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   mode: Control mode [0:CC, 1:Cubase, 2:DP, 3:Live, 4:ProTools, 5:SONAR]
#   nanoKONTROL 2 only
def set_control_mode(data, mode):
    if device_type == 'nanoKONTROL 2' and mode < 6:
        data[1] = mode
    return 0


# Get LED mode
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   returns: LED mode [0:Internal, 1:External]
#   nanoKONTROL 2 only
def get_led_mode(data):
    if device_type == 'nanoKONTROL 2':
        return data[2]
    return 0


# Set LED mode
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   mode: LED mode [0:Internal, 1:External]
#   nanoKONTROL 2 only
def set_led_mode(data, mode):
    if device_type == 'nanoKONTROL 2' and mode < 1:
        data[2] = mode
    return 0


# Get group MIDI channel
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: MIDI channel [0..15 or 16 for global]
def get_group_chan(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[16 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[3 + group * 31]
    return 0


# Set group MIDI channel
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   chan: MIDI channel [0..15 or 16 for global]
def set_group_chan(data, group, chan):
    if group < 0 or group > 7 or chan < 0 or chan > 16:
        return
    if device_type == 'nanoKONTROL 1':
        data[16 + group * 16] = chan
    elif device_type == 'nanoKONTROL 2':
        data[3 + group * 31] = chan


# Get slider assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Assign type [0:Disabled, 1:CC]
def get_slider_type(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[17 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[4 + group * 31]
    return 0


# Set slider assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   type: Assign type [0:Disabled, 1:CC]
def set_slider_type(data, group, type):
    if group < 0 or group > 7 or type < 0 or type > 1:
        return
    if device_type == 'nanoKONTROL 1':
        data[17 + group * 16] = type
    elif device_type == 'nanoKONTROL 2':
        data[4 + group * 31] = type


# Get slider CC
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: CC assigned to slider [0..127]
def get_slider_cc(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[18 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[6 + group * 31]
    return 0


# Set slider CC
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   cc: CC assigned to slider [0..127]
def set_slider_cc(data, group, cc):
    if group < 0 or group > 7 or cc < 0 or cc > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[18 + group * 16] = cc
    elif device_type == 'nanoKONTROL 2':
        data[6 + group * 31] = cc


# Get slider minimum value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Minimum value [0..127]
def get_slider_min(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[19 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[7 + group * 31]
    return 0


# Set slider minimum value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Minimum value [0..127]
def set_slider_min(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[19 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[7 + group * 31] = value


# Get slider maximum value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Maximum value [0..127]
def get_slider_max(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[20 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[8 + group * 31]
    return 0


# Set slider maximum value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Maximum value [0..127]
def set_slider_max(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[20 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[8 + group * 31] = value


# Get knob assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Type [0:Disabled, 1:CC]
def get_knob_assign_type(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[21 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[10 + group * 31]
    return 0


# Set knob assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Type [0:Disabled, 1:CC]
def set_knob_assign_type(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 1:
        return
    if device_type == 'nanoKONTROL 1':
        data[21 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[10 + group * 31] = value


# Get knob minimum value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Minimum value [0..127]
def get_knob_min(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[23 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[13 + group * 31]
    return 0


# Set knob minimum value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Minimum value [0..127]
def set_knob_min(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[23 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[13 + group * 31] = value


# Get knob maximum value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Maximum value [0..127]
def get_knob_max(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[24 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[14 + group * 31]
    return 0


# Set knob maximum value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Maximum value [0..127]
def set_knob_max(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[24 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[14 + group * 31] = value


# Get A / solo button assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Type [0:Disabled, 1:CC, 2:Note]
def get_button_a_assign_type(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[25 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[16 + group * 31]
    return 0


# Set A / solo button assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Type [0:Disabled, 1:CC, 2:Note]
def set_button_a_assign_type(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 2:
        return
    if device_type == 'nanoKONTROL 1':
        data[25 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[16 + group * 31] = value


# Get A / solo button behaviour
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Behaviour [0:Momentary, 1:Toggle]
def get_button_a_behaviour(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[31 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[17 + group * 31]
    return 0


# Set A / solo button behaviour
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Behaviour [0:Momentary, 1:Toggle]
def set_button_a_behaviour(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 1:
        return
    if device_type == 'nanoKONTROL 1':
        data[31 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[17 + group * 31] = value


# Get A / solo button CC / note
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: CC / note [0..127]
def get_button_a_param(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[26 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[18 + group * 31]
    return 0


# Set A / solo button CC / note
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: CC / note [0..127]
def set_button_a_param(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[26 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[18 + group * 31] = value


# Get A / solo button off value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Off value [0..127]
def get_button_a_off_value(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[27 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[19 + group * 31]
    return 0


# Set A / solo button off value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Off value [0..127]
def set_button_a_off_value(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[27 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[19 + group * 31] = value


# Get A / solo button on value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: on value [0..127]
def get_button_a_on_value(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[28 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[20 + group * 31]
    return 0


# Set A / solo button on value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: On value [0..127]
def set_button_a_on_value(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[28 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[20 + group * 31] = value


# Get A / solo button attack time
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Attack time [0..127]
#   nanoKONTROL 1 only
def get_button_a_attack(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[29 + group * 16]
    return 0


# Set A / solo button attack time
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Attack time [0..127]
#   nanoKONTROL 1 only
def set_button_a_attack(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[29 + group * 16] = value


# Get A / solo button release time
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Release time [0..127]
#   nanoKONTROL 1 only
def get_button_a_release(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[30 + group * 16]
    return 0


# Set A / solo button release time
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Release time [0..127]
#   nanoKONTROL 1 only
def set_button_a_release(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[30 + group * 16] = value


# Get B / mute button assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Type [0:Disabled, 1:CC, 2:Note]
def get_button_b_assign_type(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[32 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[22 + group * 31]
    return 0


# Set B / mute button assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Type [0:Disabled, 1:CC, 2:Note]
def set_button_b_assign_type(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 2:
        return
    if device_type == 'nanoKONTROL 1':
        data[32 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[22 + group * 31] = value


# Get B / mute button behaviour
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Behaviour [0:Momentary, 1:Toggle]
def get_button_b_behaviour(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[38 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[23 + group * 31]
    return 0


# Set B / mute button behaviour
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Behaviour [0:Momentary, 1:Toggle]
def set_button_b_behaviour(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 1:
        return
    if device_type == 'nanoKONTROL 1':
        data[38 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[23 + group * 31] = value


# Get B / mute button CC / note
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: CC / note [0..127]
def get_button_b_param(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[33 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[24 + group * 31]
    return 0


# Set B / mute button CC / note
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: CC / note [0..127]
def set_button_b_param(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[33 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[24 + group * 31] = value


# Get B / mute button off value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Off value [0..127]
def get_button_b_off_value(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[34 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[25 + group * 31]
    return 0


# Set B / mute button off value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Off value [0..127]
def set_button_b_off_value(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[34 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[25 + group * 31] = value


# Get B / mute button on value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: on value [0..127]
def get_button_b_on_value(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[35 + group * 16]
    elif device_type == 'nanoKONTROL 2':
        return data[26 + group * 31]
    return 0


# Set B / mute button on value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: On value [0..127]
def set_button_b_on_value(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[35 + group * 16] = value
    elif device_type == 'nanoKONTROL 2':
        data[26 + group * 31] = value


# Get B / mute button attack time
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Attack time [0..127]
#   nanoKONTROL 1 only
def get_button_b_attack(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[36 + group * 16]
    return 0


# Set B / mute button attack time
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Attack time [0..127]
#   nanoKONTROL 1 only
def set_button_b_attack(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[36 + group * 16] = value


# Get B / mute button release time
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Release time [0..127]
#   nanoKONTROL 1 only
def get_button_b_release(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 1':
        return data[37 + group * 16]
    return 0


# Set B / mute button release time
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Release time [0..127]
#   nanoKONTROL 1 only
def set_button_b_release(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 1':
        data[37 + group * 16] = value


# Get C / rec button assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Type [0:Disabled, 1:CC, 2:Note]
def get_button_c_assign_type(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 2':
        return data[28 + group * 31]
    return 0


# Set C / rec button assign type
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Type [0:Disabled, 1:CC, 2:Note]
def set_button_c_assign_type(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 2:
        return
    if device_type == 'nanoKONTROL 2':
        data[28 + group * 31] = value


# Get C / rec button behaviour
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Behaviour [0:Momentary, 1:Toggle]
def get_button_c_behaviour(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 2':
        return data[29 + group * 31]
    return 0


# Set C / rec button behaviour
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Behaviour [0:Momentary, 1:Toggle]
def set_button_c_behaviour(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 1:
        return
    if device_type == 'nanoKONTROL 2':
        data[30 + group * 16] = value


# Get C / rec button CC / note
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: CC / note [0..127]
def get_button_c_param(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 2':
        return data[30 + group * 31]
    return 0


# Set C / rec button CC / note
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: CC / note [0..127]
def set_button_c_param(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 2':
        data[30 + group * 31] = value


# Get C / rec button off value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: Off value [0..127]
def get_button_c_off_value(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 2':
        return data[31 + group * 31]
    return 0


# Set C / rec button off value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: Off value [0..127]
def set_button_c_off_value(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 2':
        data[31 + group * 31] = value


# Get C / rec button on value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   returns: on value [0..127]
def get_button_c_on_value(data, group):
    if group < 0 or group > 7:
        return 0
    if device_type == 'nanoKONTROL 2':
        return data[32 + group * 31]
    return 0


# Set C / rec button on value
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group index [0..7]
#   value: On value [0..127]
def set_button_c_on_value(data, group, value):
    if group < 0 or group > 7 or value < 0 or value > 127:
        return
    if device_type == 'nanoKONTROL 2':
        data[32 + group * 31] = value


control_map = {
    'nanoKONTROL 1': {
        'param map': {
            'assign':[0, 1],
            'behaviour': [6, 1],
            'cc/note': [1, 127],
            'off': [2, 127],
            'on': [3, 127],
            'attack': [4, 127],
            'decay': [5, 127]
        },
        'group map': {
            'chan': 0,
            'slider': 1,
            'knob': 5,
            'button a': 9,
            'button b': 16
        },
        'transport map': {
            'chan': 0,
            'button 1': 1,
            'button 2': 6,
            'button 3': 11,
            'button 4': 16,
            'button 5': 21,
            'button 6': 26,
        },
        'group 1': 16,
        'group 2': 32,
        'group 3': 48,
        'group 4': 64,
        'group 5': 80,
        'group 6': 96,
        'group 7': 112,
        'group 8': 128,
        'group 9': 128,
        'transport': 224,
    },
    'nanoKONTROL 2': {
        'param map': {
            'assign':[0, 2],
            'behaviour': [1, 1],
            'cc/note': [2, 127],
            'off': [3, 127],
            'on': [4, 127]
        },
        'group map': {
            'chan': 0,
            'slider': 1,
            'knob': 7,
            'button a': 13,
            'solo': 13,
            'button b': 19,
            'mute': 19,
            'button c': 25,
            'rec': 25,
        },
        'transport map': {
            'chan': 0,
            'button 1': 1,
            'button 2': 6,
            'button 3': 11,
            'button 4': 16,
            'button 5': 21,
            'button 6': 26,
        },
        'group 1': 16,
        'group 2': 32,
        'group 3': 48,
        'group 4': 64,
        'group 5': 80,
        'group 6': 96,
        'group 7': 112,
        'group 8': 128,
        'group 9': 128,
        'transport': 224,
    },
    'nanoKONTROL 2': {
        'group offset': 3,
        'group size': 31,
        'group chan': 0,
        'slider assign': 1,
        'slider cc/note': 3,
        'slider min': 4,
        'slider max': 5,
        'knob assign': 7,
        'knob cc/note': 9,
        'knob min': 10,
        'knob max': 11,
        'solo assign': 13,
        'solo behaviour': 14,
        'solo cc/note': 15,
        'solo off': 16,
        'solo on': 17,
        'mute assign': 19,
        'mute behaviour': 20,
        'mute cc/note': 21,
        'mute off': 22,
        'mute on': 23,
        'rec assign': 25,
        'rec behaviour': 26,
        'rec cc/note': 27,
        'rec off': 28,
        'rec on': 29,
        'transport chan': 251,
        'transport assign': 0,
        'transport behaviour': 1,
        'transport cc/note': 2,
        'transport off': 3,
        'transport on': 4,
        'transport prev': 252,
        'transport next': 258,
        'transport cycle': 264,
        'transport set marker': 270,
        'transport prev marker': 276,
        'transport next marker': 282,
        'transport rew': 288,
        'transport ff': 294,
        'transport stop': 300,
        'transport play': 306,
        'transport rec': 312,
        'custom daw assign': 318
    }
}


param_max = {
    'midi_chan': 16,
    'assign': 1,
    'cc/note': 127,
    'min': 127,
    'max': 127,
    'button assign': 2,
    'behaviour': 1
}


# Get control parameter
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group name ['group 1..9', 'transport']
#   control: Control name, e.g. 'button a'
#   param: Control parameter ['assign', 'behaviour', 'cc/note', 'off', 'on']
#   returns: Parameter value or 0 if parameter not available
def get_control_parameter(data, group, control, param):
    try:
        group_offset = control_map[device_type][group]
        if group[:5] == 'group':
            control_offset = control_map[device_type]['group map'][control]
        elif group[:9] == 'transport':
            control_offset = control_map[device_type]['transport map'][control]
        param_offset = control_map[device_type]['param_map'][param][0]
        return data[group_offset + control_offset + param_offset]
    except:
        return 0


# Set control parameter
#   data: Scene data in Korg 8-bit format (V1:256 bytes, V2:339 bytes)
#   group: Group name ['group 1..9', 'transport']
#   control: Control name, e.g. 'button a'
#   param: Control parameter ['assign', 'behaviour', 'cc/note', 'off', 'on']
#   value: Parameter value
#   returns: True on success
def set_control_parameter(data, group, control, param, value):
    try:
        group_offset = control_map[device_type][group]
        if group[:5] == 'group':
            control_offset = control_map[device_type]['group map'][control]
        elif group[:9] == 'transport':
            control_offset = control_map[device_type]['transport map'][control]
        param_offset = control_map[device_type]['param_map'][param][0]
        param_max = control_map[device_type]['param_map'][param][1]
        if value > param_max:
            return False
        data[group_offset + control_offset + param_offset] = value
    except:
        return False
    return True



## JACK ##

@client.set_process_callback
def process(frames):
    global ev
    global midi_chan
    midi_out.clear_buffer()
    if ev:
        midi_out.write_midi_event(0, ev)
        ev = None
    
    # Process incoming messages
    for offset, indata in midi_in.incoming_midi_events():
        if len(indata) == 14 and indata[:2] == [0xF0, 0x7E] and indata[3:5] == [0x06, 0x02, 0x42] and indata[6:8] == sysex_device_type:
            # Device inquiry reply
            midi_chan = indata[2]
            spin_midi_chan.set(midi_chan + 1)
            lbl_info['text'] = "nanoKONTROL v{}.{}".format(indata[13] << 7 + indata[12], indata[11] << 7 + indata[110])
        elif len(indata) == 3:
            cmd = indata[0] & 0xF0
            if cmd == 0x80 or cmd == 0x90 and indata[2] == 0:
                # Note off
                pass
            elif cmd == 0x90:
                # Note on
                pass
            elif cmd == 0xB0:
                # CC
                pass
            elif cmd == 0xE0:
                # Pitch bend
                pass
        elif indata[:10] == [0xF7, 0x42, 0x50, 0x01, midi_chan, echo_id] + sysex_device_type:
            # Search device reply
            pass
        elif len(indata) > 10 and indata[:7] == [0xF0, 0x42, 0x40 | midi_chan] + sysex_device_type + [0x00]:
            # Command list
            if indata[7:10] == [0x5F, 0x23, 0x00]:
                # Load data ACK
                pass
            elif indata[7:10] == [0x5F, 0x24, 0x00]:
                # Load data NAK
                pass
            elif indata[7:10] == [0x5F, 0x21, 0x00]:
                # Write completed
                pass
            elif indata[7:10] == [0x5F, 0x22, 0x00]:
                # Write error
                pass
        elif indata[7:10] == [0x40, 0x00, 0x02]:
            # Native mode out
            pass
        elif indata[7:10] == [0x40, 0x00, 0x03]:
            # Native mode in
            pass
        elif indata[7:10] == [0x5F, 0x42, 0x00]:
            # Mode normal
            pass
        elif indata[7:10] == [0x5F, 0x42, 0x01]:
            # Native normal
            pass
        


## MIDI messages sent from software to device ##

# Send Inquiry Message Request
def send_inquiry():
    global ev
    ev = [0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7]


# Send device search request
def send_device_search():
    global ev
    ev = [0xF0, 0x42, 0x50, 0x00, echo_id, 0xF7]


# Send a command list message
#   data: List containing the message payload
def send_command_list(data):
    global ev
    ev = [0xF0, 0x42, 0x40 | midi_chan] + sysex_device_type + [0x00] + data + [0xF7]


# Request current scene data dump from device
def send_dump_request():
    send_command_list([0x1F, 0x10, 0x00])    


# Request current temporary scene data be saved on device
#   scene: Index of scene to save
def send_scene_write_request(scene):
    if scene < 0 or scene > 3:
        return
    send_command_list([0x1F, 0x11, scene])


# Request native mode in (nanoKONTROL 2)
def send_native_mode():
    send_command_list([0x00, 0x00, 0x00])


# Request native mode out (nanoKONTROL 2)
def send_native_mode():
    send_command_list([0x00, 0x00, 0x01])


# Request mode (nanoKONTROL 2)
def send_query_mode():
    send_command_list([0x1F, 0x12, 0x00])



# Request a scene change
#   scene: Requested scene [0..3]
def send_scene_change_request(scene):
    if(scene >= 0 and scene <= 3):
        send_command_list([0x1F, 0x14, scene, 0xF7])


# Upload a scene to device "current scene"
# Must write scene to save to persistent memory
#   data: Block of scene data
def send_scene_data(data):
    send_command_list([0x7F, 0x7F, 0x02, 0x02, 0x26, 0x40, data])


# Send port detect request
def send_port_detect():
    send_command_list([0x1E, 0x00, echo_id])



# Activate jack client and get available MIDI ports
client.activate()

jack_source_ports = []
jack_dest_ports = []

ports = client.get_ports(is_midi=True, is_output=True)
ports.remove(midi_out)
for port in ports:
    jack_source_ports.append(port.name)

ports = client.get_ports(is_midi=True, is_input=True)
ports.remove(midi_in)
for port in ports:
    jack_dest_ports.append(port.name)


## UI ##

# Handle jack source change
def jack_source_changed(event):
    midi_in.disconnect()
    try:
        midi_in.connect(jack_source.get())
    except Exception as e:
        logging.warning(e)


# Handle jack destination change
def jack_dest_changed(event):
    midi_out.disconnect()
    try:
        midi_out.connect(jack_dest.get())
    except Exception as e:
        logging.warning(e)

# Handle MIDI channel manually changed by user (may also be set by device query)
def midi_chan_changed():
    global midi_chan
    midi_chan = int(midi_chan_txt.get()) - 1


# Handle device type change (initially support nanoKONTROL 1 & 2)
def device_type_changed(event):
    global device_type
    if device_type.get() == 'nanoKONTROL 1':
        sysex_device_type = [0x00, 0x01, 0x04]
    elif device_type.get() == 'nanoKONTROL 2':
        sysex_device_type = [0x00, 0x01, 0x13]


root = tk.Tk()
root.title("riban nanoKONTROL editor")

ttk.Label(root, text="riban nanoKONTROL editor").grid()

btn_query = ttk.Button(root, text="Detect", command=send_inquiry)
btn_query.grid()

lbl_info = ttk.Label(root, text="-")
lbl_info.grid()

device_type = tk.StringVar(value='nanoKONTROL 2')
cmb_device_type = ttk.Combobox(root, textvariable=device_type, state='readonly', values=device_types)
cmb_device_type.bind('<<ComboboxSelected>>', device_type_changed)
cmb_device_type.grid()

midi_chan_txt = tk.StringVar(value=1)
spin_midi_chan = ttk.Spinbox(root, from_=1, to=16, textvariable=midi_chan_txt, state='readonly', command=midi_chan_changed)
spin_midi_chan.grid()

jack_source = tk.StringVar()
cmb_jack_source = ttk.Combobox(root, textvariable=jack_source, state='readonly', values=jack_source_ports)
cmb_jack_source.bind('<<ComboboxSelected>>', jack_source_changed)
cmb_jack_source.grid()

jack_dest = tk.StringVar()
cmb_jack_dest = ttk.Combobox(root, textvariable=jack_dest, state='readonly', values=jack_dest_ports)
cmb_jack_dest.bind('<<ComboboxSelected>>', jack_dest_changed)
cmb_jack_dest.grid()


for group in range(8):
    root.columnconfigure(group * 2 + 2, weight=2)
    lbl = ttk.Label(root, text = "{}".format(group + 1))
    lbl.grid(row=10, column = group * 2 + 1, columnspan=2)
    slider = ttk.Scale(root, orient="horizontal", from_=0, to=127, value=64)
    slider.grid(row = 11, column = group * 2 + 2)
    slider = ttk.Scale(root, orient="vertical", from_=127, to=0, value=100)
    slider.grid(row = 12, column = group * 2 + 2, rowspan=3, sticky='ns')
    btn = ttk.Button(root, text = "S")
    btn.grid(row = 12, column=group * 2 + 1, weight=1)
    btn = ttk.Button(root, text="M")
    btn.grid(row = 13, column=group * 2 + 1, weight=1)
    btn = ttk.Button(root, text="R")
    btn.grid(row = 14, column = group * 2 + 1, weight=1)

root.mainloop()
