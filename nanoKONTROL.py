# Configuration editor for Korg nanoKONTROL
#
# Copyright: riban ltd (riban.co.uk)
# Licencse: GPL V3.0
# Source: https://github.com/riban-bw/nanoKONTROL-Config
#
# Dependencies: tkinter, jack / alsa, PIL, ImageTk

import struct
from tkinter import messagebox
try:
    import jack
except:
    pass
try:
    import alsa_midi 
except:
    pass
import tkinter as tk
from tkinter import ttk
import logging
from PIL import ImageTk, Image
from threading import Thread
import ToolTips

ev = None # Used to pass MIDI messages for JACK to transmit
echo_id = 0x00 # Used to identify own sysex messages

credits = [
    'Code:',
    'brian@riban.co.uk',
    'Tooltips',
    'http://www.pedrojhenriques.com',
    '',
    'Icons:',
    'https://freeicons.io',
    'profile/5790', # Transfer, Save
    'profile/3335', # Info
    'profile/730' # Restore
]

mmc_commands = [
    'Stop',
    'Play',
    'Deferred Play',
    'Fast Forward',
    'Rewind',
    'Record Strobe',
    'Record Exit',
    'Record Pause',
    'Pause',
    'Eject',
    'Chase',
    'Command Error Reset',
    'MMC Reset'
]

assign_options = [
    'Disabled',
    'CC', 'Note'
]

behaviour_options = [
    'Momentary',
    'Toggle'
]

control_map = {
    'nanoKONTROL1': {
        'param_map': {
            'assign':[0, 2],
            'behaviour': [6, 1],
            'cmd': [1, 127],
            'min': [2, 127],
            'max': [3, 127],
            'attack': [4, 127],
            'decay': [5, 127],
            'mmc_cmd': [2, 12],
            'mmc_id': [3, 127],
            'transport behaviour': [5, 1]
        },
        'group_map': {
            'channel': 0,
            'slider': 1,
            'knob': 5,
            'button_a': 9,
            'button_b': 16,
            'rew': 1,
            'play': 6,
            'ff': 11,
            'cycle': 16,
            'stop': 21,
            'rec': 26,
        },
        'groups': [16, 32, 48, 64, 80, 96, 112, 128, 144],
        'transport': 224,
    },
    'nanoKONTROL2': {
        'param_map': {
            'assign':[0, 2],
            'behaviour': [1, 1],
            'cmd': [2, 127],
            'min': [3, 127],
            'max': [4, 127]
        },
        'group_map': {
            'channel': 0,
            'slider': 1,
            'knob': 7,
            'button_a': 13,
            'solo': 13,
            'button_b': 19,
            'mute': 19,
            'button_c': 25,
            'prime': 25,
            'transport 1': 1,
            'prev_track': 1,
            'transport 2': 7,
            'next_track': 7,
            'transport 3': 13,
            'cycle': 13,
            'transport 4': 19,
            'set_marker': 19,
            'transport 5': 25,
            'prev_marker': 25,
            'transport 6': 31,
            'next_marker': 31,
            'transport 7': 37,
            'rew': 37,
            'transport 8': 43,
            'ff': 43,
            'transport 9': 49,
            'stop': 49,
            'play': 55,
            'rec': 61
        },
        'led_map': {
            'solo': 0x20,
            'mute': 0x30,
            'prime': 0x40,
            'play': 0x29,
            'stop': 0x2A,
            'rew': 0x2B,
            'ff': 0x2C,
            'rec': 0x2D,
            'cycle': 0x2E
        },
        'groups': [3, 34, 65, 96, 127, 158, 189, 220],
        'transport': 251,
        'custom daw assign': 318
    }
}

## Scene class encapsulates a nanoKONTROL scene data structure ##
class scene:
    def __init__(self):
        self.global_midi_chan = 0 # Global MIDI channel (0 based)
        self.device_types = {
            'nanoKONTROL1': {
                'sysex_len': 293,
                'sysex_id': (0x00, 0x01, 0x04, 0x00)
            },
            'nanoKONTROL2': {
                'sysex_len': 388,
                'sysex_id': (0x00, 0x01, 0x13, 0x00)
            }
        }
        self.device_type = None
        self.set_device_type('nanoKONTROL2')


    # Get the (4 byte) sysex segment defining the device type
    #   returns: Device ID as 4 byte list
    def get_sysex_id(self):
        return self.device_types[self.device_type]['sysex_id']


    # Set the device type
    #   type: Device type ['nanoKONTROL1', 'nanoKONTROL2']
    def set_device_type(self, type):
        if type == self.device_type or type not in self.device_types:
            return
        self.device_type = type
        self.reset_data()


    # Reset scene data to default values
    def reset_data(self):
        if self.device_type == 'nanoKONTROL1':
            self.data = [0] * 256
            self.set_scene_name('Scene 0')
        elif self.device_type == 'nanoKONTROL2':
            self.data = [0] * 339
            self.set_control_mode(0)
            self.set_led_mode(0)
        self.set_global_channel(15)
        for group, group_offset in enumerate(control_map[self.device_type]['groups']):
            self.set_group_channel(group_offset, 16)
            if self.device_type == 'nanoKONTROL1':
                for i, control in enumerate(('slider', 'knob', 'button_a', 'button_b')):
                    self.set_control_parameter(group_offset, control, 'assign', 1)
                    self.set_control_parameter(group_offset, control, 'cmd', 0x10 * i + group) #TODO: What is the default CC?
                    self.set_control_parameter(group_offset, control, 'min', 0)
                    self.set_control_parameter(group_offset, control, 'max', 127)
                for i, control in enumerate(('button_a', 'button_b')):
                    self.set_control_parameter(group_offset, control, 'behaviour', 0)
                    self.set_control_parameter(group_offset, control, 'attack', 0) #TODO: What is the default attack value
                    self.set_control_parameter(group_offset, control, 'decay', 0) #TODO: What is the default decay value
            elif self.device_type == 'nanoKONTROL2':
                for i, control in enumerate(('slider', 'knob', 'solo', 'mute', 'prime')):
                    self.set_control_parameter(group_offset, control, 'assign', 1)
                    self.set_control_parameter(group_offset, control, 'cmd', 0x10 * i + group)
                    self.set_control_parameter(group_offset, control, 'min', 0)
                    self.set_control_parameter(group_offset, control, 'max', 127)
                    self.set_control_parameter(group_offset, control, 'behaviour', 0)

        transport_offset = control_map[self.device_type]['transport']
        self.set_group_channel(transport_offset, 16)
        if self.device_type == 'nanoKONTROL1':
            for i, control in enumerate(('stop', 'play', 'cycle', 'ff', 'rew', 'rec')):
                transport_offset = control_map[self.device_type]['transport']
                self.set_control_parameter(transport_offset, control, 'assign', 2)
                self.set_control_parameter(transport_offset, control, 'cmd', i)
                self.set_control_parameter(transport_offset, control, 'mmc_cmd', i)
                self.set_control_parameter(transport_offset, control, 'mmc_id', 0)
                self.set_control_parameter(transport_offset, control, 'behaviour', 0)


        elif self.device_type == 'nanoKONTROL2':
            for i, control in enumerate(('play', 'stop', 'rew', 'ff', 'rec', 'cycle', 'prev_track', 'next_track', 'set_marker', 'prev_marker', 'next_marker')):
                transport_offset = control_map[self.device_type]['transport']
                self.set_control_parameter(transport_offset, control, 'assign', 1)
                if i < 6:
                    self.set_control_parameter(transport_offset, control, 'cmd',  0x29 + i)
                else:
                    self.set_control_parameter(transport_offset, control, 'cmd',  0x34 + i)
                self.set_control_parameter(transport_offset, control, 'min', 0)
                self.set_control_parameter(transport_offset, control, 'max', 127)
                self.set_control_parameter(transport_offset, control, 'behaviour', 0)

            self.set_led_mode(1)

            for i in range(318, 323):
                self.data[i] = 0 #TODO: What are default custom daw values?


    # Get data (payload) in MIDI sysex format
    # Convert Korg 8-bit data to 7-bit MIDI data
    # nanoKONTROL1 has 256 bytes of data which gives 36 blocks of 7 bytes plus 4 extra bytes
    # nanoKONTROL2 has 339 bytes of data which gives 48 blocks of 7 bytes plus 3 extra bytes
    # Each block is converted to 8 MIDI bytes (first byte represents most significant bit of subsequent 7 bytes)
    # Remaining 3 or 4 bytes are sent similarly but not padded to full block of 8, i.e. nanoKONTROL1 MIDI has 36 * 8 + 1 + 4 bytes in payload
    #   data: 8-bit Korg data
    #   returns: List containing sysex data
    def get_midi_data(self):
        sysex = ()
        for offset in range(0, len(self.data), 7):
            block = self.data[offset:offset+7]
            b0 = 0
            for b in range(len(block)):
                b0 |= ((block[b] & 0x80) >> (7 - b))
            sysex += (b0,)
            for word in block:
                sysex += (word & 0x7F,)
        return sysex


    # Set data from MIDI sysex format data
    # Convert raw 7-bit MIDI data to Korg 8-bit data
    # Raw data: 1st byte holds bit-7 of subsequent bytes, next 7 bytes hold bits 0..7 of each byte
    #   data: raw 7-bit MIDI data (multiple 8 x 7-bit blocks of data)
    def set_data(self, data):
        if len(data) != self.device_types[self.device_type]['sysex_len']:
            logging.warning('Received wrong length data dump')
            return
        i = 0
        for offset in range(0, len(data), 8):
            block = data[offset:offset+8]
            for word in range(1, len(block)):
                self.data[i + word - 1] = (block[word] | (block[0] & 1 << (word - 1)))
            i += 7


    # Get scene name
    #   returns: Scene name
    #   nanoKONTROL1 only
    #TODO: What is scene name used for?
    def get_scene_name(self):
        name = ''
        if self.device_type == 'nanoKONTROL1':
            for c in self.data[:12]:
                name += chr(c)
        return name


    # Set scene name
    #   name: Scene name (12 characters)
    #   nanoKONTROL1 only
    def set_scene_name(self, name):
        if self.device_type == 'nanoKONTROL1':
            for i in range(12):
                if i < len(name):
                    self.data[i] = ord(name[i])
                else:
                    self.data[i] = ord(' ')


    # Get global MIDI channel
    #   returns: MIDI channel
    def get_global_channel(self):
        if self.device_type == 'nanoKONTROL1':
            return self.data[12]
        elif self.device_type == 'nanoKONTROL2':
            return self.data[0]
        return 0


    # Set global MIDI channel
    #   chan: MIDI channel
    def set_global_channel(self, chan):
        if chan < 16:
            if self.device_type == 'nanoKONTROL1':
                self.data[12] = chan
            elif self.device_type == 'nanoKONTROL2':
                self.data[0] = chan


    # Get control mode
    #   returns: Control mode [0:CC, 1:Cubase, 2:DP, 3:Live, 4:ProTools, 5:SONAR]
    #   nanoKONTROL2 only
    def get_control_mode(self):
        if self.device_type == 'nanoKONTROL2':
            return self.data[1]
        return 0


    # Set control mode
    #   mode: Control mode [0:CC, 1:Cubase, 2:DP, 3:Live, 4:ProTools, 5:SONAR]
    #   nanoKONTROL2 only
    def set_control_mode(self, mode):
        if self.device_type == 'nanoKONTROL2' and mode < 6:
            self.data[1] = mode
        return 0


    # Get LED mode
    #   returns: LED mode [0:Internal, 1:External]
    #   nanoKONTROL2 only
    def get_led_mode(self):
        if self.device_type == 'nanoKONTROL2':
            return self.data[2]
        return 0


    # Set LED mode
    #   mode: LED mode [0:Internal, 1:External]
    #   nanoKONTROL2 only
    def set_led_mode(self, mode):
        if self.device_type == 'nanoKONTROL2' and mode <= 1:
            self.data[2] = mode
        return 0


    # Get group MIDI channel
    #   group_offset: Offset of the group within dataset
    #   returns: MIDI channel
    def get_group_channel(self, group_offset):
        return self.data[group_offset]


    # Set group MIDI channel
    #   group_offset: Offset of the group within dataset
    #   chan: MIDI channel
    def set_group_channel(self, group_offset, chan):
        self.data[group_offset] = chan


    # Get control parameter
    #   group_offset: Offset of group / transport
    #   control: Control name, e.g. 'button_a'
    #   param: Control parameter ['assign', 'behaviour', 'cmd', 'min', 'max']
    #   returns: Parameter value or 0 if parameter not available
    def get_control_parameter(self, group_offset, control, param):
        try:
            control_offset = control_map[self.device_type]['group_map'][control]
            param_offset = control_map[self.device_type]['param_map'][param][0]
            return self.data[group_offset + control_offset + param_offset]
        except:
            return 0


    # Set control parameter
    #   group_offset: Offset of group / transport
    #   control: Control name, e.g. 'button_a'
    #   param: Control parameter ['assign', 'behaviour', 'cmd', 'min', 'max']
    #   value: Parameter value
    def set_control_parameter(self, group_offset, control, param, value):
        try:
            control_offset = control_map[self.device_type]['group_map'][control]
            param_offset = control_map[self.device_type]['param_map'][param][0]
            param_max = control_map[self.device_type]['param_map'][param][1]
            if value > param_max:
                return False
            self.data[group_offset + control_offset + param_offset] = value
        except:
            return False
        return True


# Send a MIDI message to all connected devices
#   msg: Raw MIDI data as list of integers
def send_midi(msg):
    global ev
    try:
        alsa_client.event_output(alsa_midi.MidiBytesEvent(bytes(msg)), port=alsa_midi_out)
        alsa_client.drain_output()
    except:
        pass # ALSA failed but let's try JACk as well
    ev = msg #TODO: Implement queue for JACK MIDI send


## Device specific MIDI messages - send from application to device ##

# Send Inquiry Message Request
def send_inquiry():
    send_midi([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7])


# Send device search request
def send_device_search():
    send_midi([0xF0, 0x42, 0x50, 0x00, echo_id, 0xF7])


# Send a command list message
#   data: List containing the message payload
def send_command_list(data):
    try:
        send_midi((0xF0, 0x42, 0x40 | scene_data.global_midi_chan) + scene_data.get_sysex_id() + data + (0xF7,))
    except Exception as e:
        logging.warning(e)


# Request current scene data dump from device
def send_dump_request():
    send_command_list((0x1F, 0x10, 0x00))


# Request current temporary scene data be saved on device
#   scene: Index of scene to save [0..3, Default: 0]
#TODO: Handle different scenes on nanoKONTROL1 - maybe use SCENE button on img indcating current scene with LED on img
def send_scene_write_request(scene=0):
    if scene < 0 or scene > 3:
        return
    send_command_list((0x1F, 0x11, scene))


# Request native mode in (nanoKONTROL2)
#TODO: Implement native mode on nanoKONTROL2
def send_native_mode():
    send_command_list((0x00, 0x00, 0x00))


# Request native mode out (nanoKONTROL2)
def send_native_mode():
    send_command_list((0x00, 0x00, 0x01))


# Request mode (nanoKONTROL2)
def send_query_mode():
    send_command_list((0x1F, 0x12, 0x00))


# Request a scene change (nanoKONTROL1)
#   scene: Requested scene [0..3]
def send_scene_change_request(scene):
    if(scene >= 0 and scene <= 3):
        send_command_list((0x1F, 0x14, scene, 0xF7))


# Upload a scene to device 'current scene'
# Must write scene to save to persistent memory
def send_scene_data():
    if scene_data.device_type == 'nanoKONTROL1':
        send_command_list((0x7F, 0x7F, 0x02, 0x02, 0x26, 0x40) + scene_data.get_midi_data())
    elif scene_data.device_type == 'nanoKONTROL2':
        send_command_list((0x7F, 0x7F, 0x02, 0x03, 0x05, 0x40) + scene_data.get_midi_data())


# Send port detect request
def send_port_detect():
    send_command_list((0x1E, 0x00, echo_id))


## UI  Functions ##

# Add and remove ALSA ports to global list of source ports 
def populate_asla_source(event):
    global source_ports
    ports = alsa_client.list_ports(input=True, type=alsa_midi.PortType.ANY)
    temp_ports = {}
    for port in source_ports:
        if source_ports[port][0] == 'jack':
            temp_ports[port] = source_ports[port]
    source_ports = temp_ports
    for port in ports:
        name = port.client_name + ':' + port.name
        source_ports[name] = ['alsa', port]
    update_ports()


# Add and remove ALSA ports to global list of destination ports 
def populate_asla_dest(event):
    global destination_ports
    ports = alsa_client.list_ports(output=True, type=alsa_midi.PortType.ANY)
    temp_ports = {}
    for port in destination_ports:
        if destination_ports[port][0] == 'jack':
            temp_ports[port] = destination_ports[port]
    destination_ports = temp_ports
    for port in ports:
        name = port.client_name + ':' + port.name
        destination_ports[name] = ['alsa', port]
    update_ports()


# Update drop-down lists of MIDI ports
def update_ports():
    values = []
    for port in source_ports:
        values.append(port)
    cmb_jack_source['values'] = values
    values = []
    for port in destination_ports:
        values.append(port)
    cmb_jack_dest['values'] = values


# Handle selection from MIDI source drop-down list
def source_changed(event):
    name = jack_source.get()
    if name not in source_ports:
        return
    try:
        jack_midi_in.disconnect()
    except Exception as e:
        pass
    try:
        ports = alsa_client.list_ports(input=True, type=alsa_midi.PortType.ANY)
        for port in ports:
            try:
                alsa_midi_in.disconnect_from(port)
            except Exception as e:
                pass # Ignore any unconnected ports
    except:
        pass # ALSA may not be enabled

    try:
        if source_ports[name][0] == 'jack':
            jack_midi_in.connect(source_ports[name][1])
        elif source_ports[name][0] == 'alsa':
            alsa_midi_in.connect_from(source_ports[name][1])
    except Exception as e:
        pass
    send_device_search()


# Handle selection from MIDI destination drop-down list
def destination_changed(event):
    name = jack_dest.get()
    if name not in destination_ports:
        return
    try:
        jack_midi_out.disconnect()
    except Exception as e:
        pass
    ports = alsa_client.list_ports(output=True, type=alsa_midi.PortType.ANY)
    try:
        for port in ports:
            try:
                alsa_midi_out.disconnect_to(port)
            except Exception as e:
                pass # Ignore any unconnected ports
    except:
        pass # ALSA may not be enabled

    try:
        if destination_ports[name][0] == 'jack':
            jack_midi_out.connect(destination_ports[name][1])
        elif destination_ports[name][0] == 'alsa':
            alsa_midi_out.connect_to(destination_ports[name][1])
    except Exception as e:
        pass
    send_device_search()


# Populate the control editor and connect to a control to edit
#   ctrl: Name of the control to edit (default: Repopulate with current selection)
#   group: Control group or None (default) for transport controls
def populate_editor(ctrl=None, group=None):
    global editor_midi_channel
    global editor_midi_channel_is_global
    global editor_group_offset
    global editor_assign
    global editor_behaviour
    global editor_cmd
    global editor_min
    global editor_max
    global editor_ctrl
    global editor_mmc_cmd
    global editor_mmc_id
    global editor_group

    if ctrl is not None:
        editor_ctrl = ctrl
        editor_group = group
    if editor_ctrl is None:
        # Must be first time so select first knob
        editor_ctrl = 'knob'
        editor_group = 0
    is_button = editor_ctrl not in ('knob', 'slider')

    if editor_group is None:
        editor_group_offset = control_map[scene_data.device_type]['transport']
        editor_title.set('{}'.format(editor_ctrl.replace('_',' ').upper()))
    elif editor_group < len(control_map[scene_data.device_type]['groups']):
        editor_group_offset = control_map[scene_data.device_type]['groups'][editor_group]
        editor_title.set('{} {}'.format(editor_ctrl.replace('_',' ').upper(), editor_group + 1))

    if is_button:
        rb_editor_note['state'] = tk.NORMAL
        editor_behaviour.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'behaviour'))
        rb_editor_momentary['state'] = tk.NORMAL
        rb_editor_toggle['state'] = tk.NORMAL
        lbl_min['text'] = 'Off'
        lbl_max['text'] = 'On'

    else:
        rb_editor_note['state'] = tk.DISABLED
        rb_editor_momentary['state'] = tk.DISABLED
        rb_editor_toggle['state'] = tk.DISABLED
        lbl_min['text'] = 'Min'
        lbl_max['text'] = 'Max'

    midi_chan = scene_data.get_group_channel(editor_group_offset)
    if midi_chan < 16:
        editor_midi_channel.set(midi_chan + 1)
        editor_midi_channel_is_global.set(0)
    else:
        editor_midi_channel_is_global.set(1)

    if scene_data.device_type == 'nanoKONTROL1' and group is None:
        rb_editor_note['text'] = 'MMC'
        if editor_assign.get() == 2:
            lbl_cmd['text'] = 'MMC Command'
            lbl_min.grid_remove()
        else:
            lbl_cmd['text'] = 'CC'
            lbl_min.grid()
        lbl_max['text'] = 'Device ID'
        spn_cmd.grid_remove()
        spn_min.grid_remove()
        spn_max.grid_remove()
        cmb_mmc_cmd.grid(row=4, column=0, columnspan=2, sticky='ew')
        spn_mmc_id.grid()
    else:
        rb_editor_note['text'] = 'Note'
        if editor_assign.get() == 2:
            lbl_cmd['text'] = 'Note'
        else:
            lbl_cmd['text'] = 'CC'
        lbl_min.grid()
        spn_cmd.grid()
        spn_min.grid()
        spn_max.grid()
        cmb_mmc_cmd.grid_remove()
        spn_mmc_id.grid_remove()


    editor_assign.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'assign'))
    editor_cmd.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'cmd'))
    editor_min.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'min'))
    editor_max.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'max'))
    mmc_cmd_index = scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'mmc_cmd')
    mmc_cmd = mmc_commands[mmc_cmd_index]
    editor_mmc_cmd.set(mmc_cmd)
    editor_mmc_id.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'mmc_id'))
    editor_global_midi_channel.set(scene_data.get_global_channel() + 1)
    if scene_data.device_type == 'nanoKONTROL2':
        editor_global_led_mode.set(scene_data.get_led_mode())
        frame_led_mode.grid()
    else:
        frame_led_mode.grid_remove()


# Handle change of editor MIDI channel
def on_editor_midi_chan(*args):
    if editor_midi_channel_is_global.get():
        spn_chan['state'] = tk.DISABLED
        scene_data.set_group_channel(editor_group_offset,  16)
    else:
        spn_chan['state'] = tk.NORMAL
        scene_data.set_group_channel(editor_group_offset,  editor_midi_channel.get() - 1)


# Handle change of editor assign (control mode)
def on_editor_assign(*args):
    try:
        scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'assign', editor_assign.get())
    except:
        pass
    if editor_assign.get() == 0:
        # Disabled
        for ctrl in [rb_editor_momentary, rb_editor_toggle, spn_cmd, spn_min, spn_max, spn_chan, chk_global]:
            ctrl['state'] = tk.DISABLED
    elif editor_assign.get() == 1:
        # CC
        for ctrl in [spn_cmd, spn_min, spn_max, chk_global, lbl_cmd]:
            ctrl['state'] = tk.NORMAL
        lbl_cmd['text'] = 'CC'
        if editor_ctrl in ['knob', 'slider']:
            lbl_max['text'] = 'Max'
        else:
            lbl_max['text'] = 'On'
        cmb_mmc_cmd.grid_remove()
        spn_cmd.grid()
        spn_min.grid()
    elif editor_assign.get() == 2:
        # Note / MMC
        for ctrl in [rb_editor_momentary, rb_editor_toggle, spn_cmd, spn_min, spn_max, spn_chan, chk_global]:
            ctrl['state'] = tk.NORMAL
        if editor_group_offset == control_map[scene_data.device_type]['transport']:
            lbl_cmd['text'] = 'MMC Command'
            if scene_data.device_type == 'nanoKONTROL1':
                cmb_mmc_cmd.grid()
                spn_cmd.grid_remove()
                spn_min.grid_remove()
        else:
            lbl_cmd['text'] = 'Note'

    if editor_assign.get():
        if editor_ctrl not in ['slider', 'knob']:
            rb_editor_momentary['state'] = tk.NORMAL
            rb_editor_toggle['state'] = tk.NORMAL
        if scene_data.get_group_channel(editor_group_offset) < 16:
            spn_chan['state'] = tk.NORMAL
        else:
            spn_chan['state'] = tk.DISABLED


# Handle change of editor behaviour
def on_editor_behaviour(*args):
    try:
        scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'behaviour', editor_behaviour.get())
    except:
        pass


# Handle change of editor command (CC/Note/MMC)
def on_editor_cmd(*args):
    try:
        scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'cmd', editor_cmd.get())
    except:
        pass


# Handle change of editor min/off
def on_editor_min(*args):
    try:
        scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'min', editor_min.get())
    except:
        pass


# Handle change of editor max/on
def on_editor_max(*args):
    try:
        scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'max', editor_max.get())
    except:
        pass


# Handle change of editor MMC command
def on_editor_mmc_cmd(*args):
    try:
        mmc_cmd_index = mmc_commands.index(editor_mmc_cmd.get())
        scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'mmc_cmd', mmc_cmd_index)
    except:
        pass


# Handle change of editor MMC device ID
def on_editor_mmc_id(*args):
    try:
        scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'mmc_id', editor_mmc_id.get())
    except:
        pass


# Handle change of global MIDI channel
def on_editor_global_midi_chan(*args):
    try:
        scene_data.set_global_channel(editor_global_midi_channel.get() - 1)
    except:
        pass


# Handle change of LED mode (nanoKONTROL2 only)
def on_editor_global_led_mode(*args):
    try:
        scene_data.set_led_mode(editor_global_led_mode.get())
    except:
        pass


# Restore the data from last downloaded
def restore_last_download():
    scene_data.data = scene_backup.data.copy()
    populate_editor()


# Show application info (about...)
def show_info():
    msg = 'nanoKONTROL-Config\nriban 2022\n'
    for credit in credits:
        msg += '\n{}'.format(credit)
    messagebox.showinfo('About...', msg)


# Resize the device image
def resize_image(event):
    global canvas_img
    canvas_img = ImageTk.PhotoImage(img.resize((event.width, event.height), Image.ANTIALIAS))
    canvas.itemconfig(device_image, image=canvas_img)


# Handle mouse click on image - react to hot-spot clicks
#   event: Mouse event
def on_canvas_click(event):
    #print(event.x, event.y)

    if scene_data.device_type == 'nanoKONTROL1':
        # x coord range as ratio of image size for each group (0..7, 8=transport)
        group_coords = [(0.20,0.28), (0.29,0.36), (0.38,0.45), (0.47,0.54), (0.55,0.62), (0.64,0.71), (0.72,0.79), (0.81,0.88), (0.89,0.97), (0.02,0.19)]
        # relative coords as ration of image size of each control within group from group offset (y coord is absolute)
        group_ctrl_coords = {
            'knob': [0.03, 0.11, 0.08, 0.2],
            'slider': [0.04, 0.47, 0.07, 0.75],
            'button_a': [0.00, 0.44, 0.03, 0.54],
            'button_b': [0.00, 0.70, 0.03, 0.80]
        }
        transport_ctrl_coords = {
            'rew': [0.03, 0.52, 0.08, 0.61],
            'play': [0.08, 0.52, 0.13, 0.61],
            'ff': [0.14, 0.52, 0.19, 0.61],
            'cycle': [0.03, 0.66, 0.08, 0.74],
            'stop': [0.08, 0.66, 0.13, 0.74],
            'rec': [0.14, 0.66, 0.19, 0.74]
        }
    elif scene_data.device_type == 'nanoKONTROL2':
        # x coord range as ratio of image size for each group (0..7, 8=transport)
        group_coords = [(0.30,0.37), (0.39,0.45), (0.47,0.54), (0.56,0.63), (0.64,0.71), (0.73,0.80), (0.81,0.88), (0.90,0.96), (0.04, 0.27)]
        # relative coords as ration of image size of each control within group from group offset (y coord is absolute)
        group_ctrl_coords = {
            'knob': [0.03, 0.11, 0.07, 0.26],
            'slider': [0.04, 0.4, 0.06, 0.74],
            'solo': [0.00, 0.39, 0.03, 0.48],
            'mute': [0.00, 0.59, 0.03, 0.67],
            'prime': [0.00, 0.76, 0.03, 0.86],
        }
        transport_ctrl_coords = {
            'prev_track': [0.04, 0.45, 0.07, 0.50],
            'next_track': [0.09, 0.45, 0.12, 0.50],
            'cycle': [0.04, 0.60, 0.07, 0.66],
            'set_marker': [0.14, 0.60, 0.17, 0.66],
            'prev_marker': [0.19, 0.60, 0.22, 0.66],
            'next_marker': [0.24, 0.60, 0.27, 0.66],
            'rew': [0.04, 0.76, 0.07, 0.88],
            'ff': [0.09, 0.76, 0.12, 0.88],
            'stop': [0.14, 0.76, 0.17, 0.88],
            'play': [0.19, 0.76, 0.22, 0.88],
            'rec': [0.24, 0.76, 0.27, 0.88],
        }
    else:
        return
    x = event.x / canvas_img.width()
    y = event.y / canvas_img.height()
    group = None
    for i,coord in enumerate(group_coords):
        if x > coord[0] and x < coord[1]:
            group = i
            group_offset_x = coord[0]
            break
    
    if group is None:
        return

    if group < len(group_coords) - 1:            
        for ctrl in group_ctrl_coords:
            if x > group_offset_x + group_ctrl_coords[ctrl][0] and y > group_ctrl_coords[ctrl][1] and x < group_offset_x + group_ctrl_coords[ctrl][2] and y < group_ctrl_coords[ctrl][3]:
                #print('Clicked on control {} {}'.format(ctrl, group + 1))
                populate_editor(ctrl, group)
                break
    else:
        for ctrl in transport_ctrl_coords:
            if x > transport_ctrl_coords[ctrl][0] and y > transport_ctrl_coords[ctrl][1] and x < transport_ctrl_coords[ctrl][2] and y < transport_ctrl_coords[ctrl][3]:
                #print('Clicked on control {}'.format(ctrl))
                populate_editor(ctrl, None)
                break


# Set the device type
#   type: Device type ['nanoKONTROL1', 'nanoKONTROL2']
def set_device_type(type):
    global img
    global canvas_img
    scene_data.set_device_type(type)
    width = canvas_img.width()
    height = canvas_img.height()
    img = Image.open('{}.png'.format(scene_data.device_type))
    canvas_img = ImageTk.PhotoImage(img.resize((width, height), Image.ANTIALIAS))
    canvas.itemconfig(device_image, image=canvas_img)
    populate_editor()


# Handle MIDI data received from JACK or ALSA
#   indata: List of raw MIDI data bytes
def handle_midi_input(indata):
    
    data = struct.unpack('{}B'.format(len(indata)), indata)
    str = '[{}] '.format(len(data))
    for i in data:
        str += '{:02X} '.format(i)
    #print(str)
    txt_midi_in.set(str)

    if len(data) == 14 and data[:2] == (0xF0, 0x7E) and data[3:5] == (0x06, 0x02, 0x42):
        # Device inquiry reply
        scene_data.global_midi_chan = data[2]
        major = data[12] + (data[13 << 7])
        minor = data[10] + (data[11] << 7)
    elif data[:4] == (0xF0, 0x42, 0x50, 0x01) and data[5] == echo_id:
        # Search device reply
        scene_data.global_midi_chan = data[4]
        family_id = data[6] + (data[7] << 7)
        member_id = data[8] + (data[9] << 7)
        minor = data[10]  + (data[11]<< 7)
        major = data[12] + (data[13]<< 7)
        if family_id == 132:
            set_device_type('nanoKONTROL1')
        elif family_id == 147:
            set_device_type('nanoKONTROL2')
        device_info.set('Device version: {}.{}'.format(major,minor))
    elif len(data) == 3:
        cmd = data[0] & 0xF0
        if cmd == 0x80 or cmd == 0x90 and data[2] == 0:
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
    elif len(data) > 10 and data[:7] == (0xF0, 0x42, 0x40 | scene_data.global_midi_chan) + scene_data.get_sysex_id():
        # Command list
        if data[7:13] == (0x7F, 0x7F, 0x02, 0x03, 0x05, 0x40):
            # nanoKONTROL2 data dump
            scene_data.set_data(data[13:-1])
            scene_backup.data = scene_data.data.copy()
            set_device_type('nanoKONTROL2')
        elif data[7:13] == (0x7F, 0x7F, 0x02, 0x02, 0x26, 0x40):
            # nanoKONTROL1 data dump
            scene_data.set_data(data[13:-1])
            scene_backup.data = scene_data.data.copy()
            set_device_type('nanoKONTROL1')
        elif data[7:10] == (0x5F, 0x23, 0x00):
            # Load data ACK
            #TODO: Indicate successful reception of data
            pass
        elif data[7:10] == (0x5F, 0x24, 0x00):
            # Load data NAK
            #TODO: Indicate failed reception of data
            pass
        elif data[7:10] == (0x5F, 0x21, 0x00):
            # Write completed
            #TODO: Indicate successful data write
            pass
        elif data[7:10] == (0x5F, 0x22, 0x00):
            # Write error
            #TODO: Indicate failed data write
            pass
    elif data[7:10] == (0x40, 0x00, 0x02):
        # Native mode out
        pass
    elif data[7:10] == (0x40, 0x00, 0x03):
        # Native mode in
        pass
    elif data[7:10] == (0x5F, 0x42, 0x00):
        # Normal mode
        pass
    elif data[7:10] == (0x5F, 0x42, 0x01):
        # Native mode
        pass


## JACK Functions ##

# Process jack frames
def jack_process(frames):
    global ev

    jack_midi_out.clear_buffer()
    if ev:
        jack_midi_out.write_midi_event(0, ev)
        ev = None
    
    # Process incoming messages
    for offset, indata in jack_midi_in.incoming_midi_events():
        handle_midi_input(indata)
        

# Refresh jack MIDI ports
def refresh_jack_ports():
    global cmb_jack_source
    global cmb_jack_dest

    ports = jack_client.get_ports(is_midi=True, is_output=True)
    ports.remove(jack_midi_out)
    for port in ports:
        source_ports[port.name] = ['jack', port]

    jack_dest_ports = []
    ports = jack_client.get_ports(is_midi=True, is_input=True)
    ports.remove(jack_midi_in)
    for port in ports:
        destination_ports[port.name] = ['jack', port]

    update_ports()


## ALSA Functions ##

# Thread worker listening for ALSA MIDI events
def alsa_midi_in_thread():
    while True:
        event = alsa_client.event_input(prefer_bytes=True)
        try:
            handle_midi_input(event.midi_bytes)
        except:
            print(repr(event))


##################################### 
## Core sequential functional code ##
##################################### 

scene_data = scene()
scene_backup = scene()

## Initialise MIDI interfaces ##
jack_client = None
try:
    jack_client = jack.Client('riban-nanoKonfig')
    jack_midi_in = jack_client.midi_inports.register('in')
    jack_midi_out = jack_client.midi_outports.register('out')
except:
    pass

alsa_client = None
try:
    alsa_client = alsa_midi.SequencerClient('riban-nanoKonfig')
    alsa_midi_in = alsa_client.create_port('in', caps=alsa_midi.WRITE_PORT)
    alsa_midi_out = alsa_client.create_port('out', caps=alsa_midi.READ_PORT)
except:
    pass

if alsa_client == jack_client == None:
    logging.error('Failed to create ALSA or JACK client')
    exit(-1)


# Create UI
source_ports = {} # Dictionary of available MIDI source ports: display_name:[type,port] where type is jack or alsa
destination_ports = {} # Dictionary of available MIDI destination ports: display_name:[type,port] where type is jack or alsa

# Root window
root = tk.Tk()
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(2, weight=1)
root.title('riban nanoKONTROL editor')

# Icons
img_transfer_down = ImageTk.PhotoImage(Image.open('transfer.png'), Image.ANTIALIAS)
img_transfer_up = ImageTk.PhotoImage(Image.open('transfer.png').rotate(180), Image.ANTIALIAS)
img_save = ImageTk.PhotoImage(Image.open('save.png'), Image.ANTIALIAS)
img_info = ImageTk.PhotoImage(Image.open('info.png'), Image.ANTIALIAS)
img_restore = ImageTk.PhotoImage(Image.open('restore.png'), Image.ANTIALIAS)

tk.Label(root, text='riban nanoKONTROL editor', bg='#80cde0').grid(columnspan=2, sticky='ew')

# Top frame
frame_top = tk.Frame(root, padx=2, pady=2)
frame_top.columnconfigure(7, weight=1)
frame_top.grid(row=1, columnspan=2, sticky='enw')

jack_source = tk.StringVar()
ttk.Label(frame_top, text='MIDI input').grid(row=0, column=0, sticky='w')
cmb_jack_source = ttk.Combobox(frame_top, textvariable=jack_source, state='readonly')
cmb_jack_source.bind('<<ComboboxSelected>>', source_changed)
cmb_jack_source.grid(row=1, column=0, sticky='n')
cmb_jack_source.bind('<Enter>', populate_asla_source)

txt_midi_in = tk.StringVar()
ttk.Label(root, textvariable=txt_midi_in, anchor='w', background='#aacf55', width=1).grid(row=3, column=0, columnspan=2, sticky='ew') # width=<any> stops received MIDI messages stretching width of display 

jack_dest = tk.StringVar()
ttk.Label(frame_top, text='MIDI output').grid(row=0, column=1, sticky='w')
cmb_jack_dest = ttk.Combobox(frame_top, textvariable=jack_dest, state='readonly')
cmb_jack_dest.bind('<<ComboboxSelected>>', destination_changed)
cmb_jack_dest.grid(row=1, column=1, sticky='n')
cmb_jack_dest.bind('<Enter>', populate_asla_dest)

btn_download = ttk.Button(frame_top, image=img_transfer_down, command=send_dump_request)
btn_download.grid(row=0, column=2, rowspan=2)
btn_upload = ttk.Button(frame_top, image=img_transfer_up, command=send_scene_data)
btn_upload.grid(row=0, column=3, rowspan=2)
btn_save = ttk.Button(frame_top, image=img_save, command=send_scene_write_request)
btn_save.grid(row=0, column=4, rowspan=2)
btn_restore = ttk.Button(frame_top, image=img_restore, command=restore_last_download)
btn_restore.grid(row=0, column=5, rowspan=2)
btn_info = ttk.Button(frame_top, image=img_info, command=show_info)
btn_info.grid(row=0, column=6, rowspan=2)
device_info = tk.StringVar()
lbl_device_info = tk.Label(frame_top, textvariable=device_info)
lbl_device_info.grid(row=0, column=7, sticky='ne')

# Control editor frame
editor_midi_channel = tk.IntVar()
editor_midi_channel_is_global = tk.IntVar()
editor_assign = tk.IntVar()
editor_behaviour = tk.IntVar()
editor_cmd = tk.IntVar()
editor_min = tk.IntVar()
editor_max = tk.IntVar()
editor_group_offset = 0
editor_ctrl = None
editor_group = None
editor_mmc_cmd = tk.StringVar()
editor_mmc_id = tk.IntVar()
editor_title = tk.StringVar()
editor_global_midi_channel = tk.IntVar()
editor_global_led_mode = tk.IntVar()

frame_editor = tk.Frame(root, padx=4, pady=4, bd=2, relief='groove')
frame_editor.grid(row=2, column=1, sticky='nsw')
frame_editor.columnconfigure(0, uniform='editor_uni', weight=1)
frame_editor.columnconfigure(1, uniform='editor_uni', weight=1)
frame_editor.columnconfigure(2, uniform='editor_uni', weight=1)

tk.Label(frame_editor, textvariable=editor_title, width=1, bg='#bf64ed').grid(row=0, column=0, columnspan=3, sticky='wne')

frame_assign = tk.Frame(frame_editor, bd=2, relief='groove')
frame_assign.grid(row=1, columnspan=3, sticky='ew')

tk.Radiobutton(frame_assign, text='Disabled', variable=editor_assign, value=0).grid(row=0, column=0)
rb_editor_cmd = tk.Radiobutton(frame_assign, text='CC', variable=editor_assign, value=1)
rb_editor_cmd.grid(row=0, column=1)
rb_editor_note = tk.Radiobutton(frame_assign, text='Note', variable=editor_assign, value=2)
rb_editor_note.grid(row=0, column=2)

frame_behaviour = tk.Frame(frame_editor, bd=2, relief='groove')
frame_behaviour.grid(row=2, columnspan=3, sticky='ew')
rb_editor_momentary = tk.Radiobutton(frame_behaviour, text='Momentary', variable=editor_behaviour, value=0)
rb_editor_momentary.grid(row=0, column=0, sticky='w')
rb_editor_toggle = tk.Radiobutton(frame_behaviour, text='Toggle', variable=editor_behaviour, value=1)
rb_editor_toggle.grid(row=0, column=1, sticky='w')

lbl_cmd = tk.Label(frame_editor, text='CC')
lbl_cmd.grid(row=3, column=0, sticky='w')
lbl_min = tk.Label(frame_editor, text='Min')
lbl_min.grid(row=3, column=1, sticky='w')
lbl_max = tk.Label(frame_editor, text='Max')
lbl_max.grid(row=3, column=2, sticky='w')

cmb_mmc_cmd = ttk.Combobox(frame_editor, textvariable=editor_mmc_cmd, state='readonly', values=mmc_commands)
spn_mmc_id = tk.Spinbox(frame_editor, from_=0, to=127, textvar=editor_mmc_id, width=3)
spn_mmc_id.grid(row=4, column=2, sticky='w')
spn_mmc_id.grid_remove()
spn_cmd = tk.Spinbox(frame_editor, from_=0, to=127, textvariable=editor_cmd, width=3)
spn_cmd.grid(row=4, column=0, sticky='ew')
spn_min = tk.Spinbox(frame_editor, from_=0, to=127, textvariable=editor_min, width=3)
spn_min.grid(row=4, column=1, sticky='ew')
spn_max = tk.Spinbox(frame_editor, from_=0, to=127, textvariable=editor_max, width=3)
spn_max.grid(row=4, column=2, sticky='ew')

tk.Label(frame_editor, text='MIDI Channel').grid(row=5, column=0, sticky='w')
spn_chan = tk.Spinbox(frame_editor, from_=1, to=16, textvariable=editor_midi_channel, width=3)
spn_chan.grid(row=5, column=1, sticky='ew')
chk_global = tk.Checkbutton(frame_editor, text='Global', variable=editor_midi_channel_is_global)
chk_global.grid(row=5, column=2, sticky='wsn')

tk.Label(frame_editor, text='Global Settings', bg='#bf64ed').grid(row=6, column=0, columnspan=3, sticky='we')

tk.Label(frame_editor, text='MIDI Channel').grid(row=7, column=0, sticky='w')
tk.Spinbox(frame_editor, from_=1, to=16, textvar=editor_global_midi_channel, width=3).grid(row=7, column=1, sticky='ew')

frame_led_mode = tk.Frame(frame_editor, bd=2, relief='groove')
frame_led_mode.grid(row=8, columnspan=3, sticky='ew')
tk.Label(frame_led_mode, text="LED Mode").grid(row=0, column=0)
tk.Radiobutton(frame_led_mode, text='Internal', variable=editor_global_led_mode, value=0).grid(row=0, column=1)
tk.Radiobutton(frame_led_mode, text='External', variable=editor_global_led_mode, value=1).grid(row=0, column=2)

# Configure variable change event handlers
editor_midi_channel.trace('w', on_editor_midi_chan)
editor_midi_channel_is_global.trace('w', on_editor_midi_chan)
editor_assign.trace('w', on_editor_assign)
editor_behaviour.trace('w', on_editor_behaviour)
editor_cmd.trace('w', on_editor_cmd)
editor_min.trace('w', on_editor_min)
editor_max.trace('w', on_editor_max)
editor_mmc_cmd.trace('w', on_editor_mmc_cmd)
editor_mmc_id.trace('w', on_editor_mmc_id)
editor_global_midi_channel.trace('w', on_editor_global_midi_chan)
editor_global_led_mode.trace('w', on_editor_global_led_mode)

# Start jack client
if jack_client:
    jack_client.set_process_callback(jack_process)
    jack_client.set_graph_order_callback(refresh_jack_ports)

    # Activate jack client and get available MIDI ports
    jack_client.activate()


# Start ALSA MIDI listening thread
if alsa_client:
    alsa_thread = Thread(target=alsa_midi_in_thread, args=())
    alsa_thread.name = 'alsa_in'
    alsa_thread.daemon = True
    alsa_thread.start()


# Device image
canvas = tk.Canvas(root, width=800, height=250)
img = Image.open('{}.png'.format(scene_data.device_type))
canvas_img = ImageTk.PhotoImage(img, Image.ANTIALIAS)
device_image = canvas.create_image(0, 0, anchor='nw', image=canvas_img)
canvas.grid(row=2, column=0, sticky='nsew')
canvas.bind('<Button-1>', on_canvas_click)
canvas.bind('<Configure>', resize_image)

set_device_type('nanoKONTROL2')

tooltip_obj = ToolTips.ToolTips(
    [btn_download, btn_upload, btn_save, btn_restore, btn_info],
    ['Download from nanoKONTROL', 'Upload to nanoKONTROL', 'Save current scene on nanoKONTROL', 'Restore to last download', 'About']
)

root.mainloop()
