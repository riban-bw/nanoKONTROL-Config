# Configuration editor for Korg nanoKONTROL
#
# Copyright riban.co.uk
# Licencse GPL V3.0
#
# Dependencies: tkinter, jack

import struct
import jack
import tkinter as tk
from tkinter import ttk
import logging
from time import sleep
from PIL import ImageTk, Image

midi_chan = 0 # MIDI channel (0 based)
sysex_device_type = {
    'nanoKONTROL1': [0x00, 0x01, 0x04, 0x00],
    'nanoKONTROL2': [0x00, 0x01, 0x13, 0x00]
}
client = jack.Client("riban-nanoKonfig")
midi_in = client.midi_inports.register('in')
midi_out = client.midi_outports.register('out')
ev = []
echo_id = 0x00

ctrl_map = {} # Map of GUI controls with associated data structures

assign_options = ['Disabled', 'CC', 'Note']
behaviour_options = ['Momentary', 'Toggle']
control_map = {
    'nanoKONTROL1': {
        'param map': {
            'assign':[0, 2],
            'behaviour': [6, 1],
            'cc/note': [1, 127],
            'off': [2, 127],
            'on': [3, 127],
            'attack': [4, 127],
            'decay': [5, 127],
            'mmc cmd': [2, 12],
            'mmc id': [3, 127],
            'transport behaviour': [5, 1]
        },
        'group map': {
            'channel': 0,
            'slider': 1,
            'knob': 5,
            'button_a': 9,
            'button_b': 16,
            'transport 1': 1,
            'transport 2': 6,
            'transport 3': 11,
            'transport 4': 16,
            'transport 5': 21,
            'transport 6': 26,
        },
        'groups': [16, 32, 48, 64, 80, 96, 112, 128, 144],
        'transport': 224,
    },
    'nanoKONTROL2': {
        'param map': {
            'assign':[0, 2],
            'behaviour': [1, 1],
            'cc/note': [2, 127],
            'off': [3, 127],
            'on': [4, 127]
        },
        'group map': {
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


class scene:
    def __init__(self):
        self.data = [0] * 339 # Raw data (nanoKONTROL1 only has 256 bytes so ignore upper data)
        self.device_type = "nanoKONTROL2"
        self.reset_data()


    # Reset scene data to default values
    def reset_data(self):
        if self.device_type == "nanoKONTROL1":
            self.data = [0] * 256
            self.set_scene_name("scene 0")
        elif self.device_type == "nanoKONTROL2":
            self.data = [0] * 339
            self.set_control_mode(0)
            self.set_led_mode(0)
        self.set_global_channel(15)
        for group, group_offset in enumerate(control_map[self.device_type]['groups']):
            self.set_group_channel(group, 15)
            if self.device_type == "nanoKONTROL1":
                for i, control in enumerate(('slider', 'knob', 'button_a', 'button_b')):
                    self.set_control_parameter(group_offset, control, 'assign', 1)
                    self.set_control_parameter(group_offset, control, 'cc/note', 0x10 * i + group) #TODO: What is the default CC?
                    self.set_control_parameter(group_offset, control, 'off', 0)
                    self.set_control_parameter(group_offset, control, 'on', 127)
                for i, control in enumerate(('button_a', 'button_b')):
                    self.set_control_parameter(group_offset, control, 'behaviour', 0)
                    self.set_control_parameter(group_offset, control, 'attack', 0) #TODO: What is the default attack value
                    self.set_control_parameter(group_offset, control, 'decay', 0) #TODO: What is the default decay value
            elif self.device_type == "nanoKONTROL2":
                for i, control in enumerate(('slider', 'knob', 'solo', 'mute', 'prime')):
                    self.set_control_parameter(group_offset, control, 'assign', 1)
                    self.set_control_parameter(group_offset, control, 'cc/note', 0x10 * i + group)
                    self.set_control_parameter(group_offset, control, 'off', 0)
                    self.set_control_parameter(group_offset, control, 'on', 127)
                    self.set_control_parameter(group_offset, control, 'behaviour', 0)

        transport_offset = control_map[self.device_type]['transport']
        if self.device_type == 'nanoKONTROL1':
            pass #TODO Implement nanoKONTROL1 transport

        elif self.device_type == 'nanoKONTROL2':
            for i, control in enumerate(('play', 'stop', 'rew', 'ff', 'rec', 'cycle', 'prev_track', 'next_track', 'set_marker', 'prev_marker', 'next_marker')):
                transport_offset = control_map[self.device_type]['transport']
                self.set_control_parameter(transport_offset, control, 'assign', 1)
                if i < 6:
                    self.set_control_parameter(transport_offset, control, 'cc/note',  0x29 + i)
                else:
                    self.set_control_parameter(transport_offset, control, 'cc/note',  0x34 + i)
                self.set_control_parameter(transport_offset, control, 'off', 0)
                self.set_control_parameter(transport_offset, control, 'on', 127)
                self.set_control_parameter(transport_offset, control, 'behaviour', 0)

            self.set_led_mode(1)

            for i in range(318, 323):
                self.data[i] = 0 #TODO: What are default custom daw values?


    # Get data in MIDI sysex format
    # Convert Korg 8-bit data to 7-bit MIDI data
    # nanoKONTROL1 has 256 bytes of data which gives 36 blocks of 7 bytes plus 4 extra bytes
    # nanoKONTROL2 has 339 bytes of data which gives 48 blocks of 7 bytes plus 3 extra bytes
    # Each block is converted to 8 MIDI bytes (first byte represents most significant bit of subsequent 7 bytes)
    # Remaining 3 or 4 bytes are sent similarly but not padded to full block of 8, i.e. nanoKONTROL1 MIDI has 36 * 8 + 1 + 4 bytes in payload
    #   data: 8-bit Korg data
    #   returns: List containing sysex data
    def get_midi_data(self):
        sysex = []
        for offset in range(0, len(self.data), 7):
            block = self.data[offset:offset+7]
            b0 = 0
            for b in range(len(block)):
                b0 |= ((block[b] & 0x80) >> (7 - b))
            sysex.append(b0)
            for word in range(len(block)):
                sysex.append(self.data[offset + word] & 0x7F)
        return sysex


    # Set data from MIDI sysex format data
    # Convert raw 7-bit MIDI data to Korg 8-bit data
    # Raw data: 1st byte holds bit-7 of subsequent bytes, next 7 bytes hold bits 0..7 of each byte
    #   data: raw 7-bit MIDI data (multiple 8 x 7-bit blocks of data)
    def set_data(self, data):
        i = 0
        for offset in range(0, len(data), 8):
            block = data[offset:offset+8]
            for word in range(1, len(block)):
                self.data[i] = (data[offset + word] | (data[offset] & 1 << (word - 1)) << 8 - word)
            i += 1


    # Get scene name
    #   returns: Scene name
    #   nanoKONTROL1 only
    def get_scene_name(self):
        name = ""
        if self.device_type == 'nanoKONTROL1':
            for c in self.data[:12]:
                name += chr(c)
        return name


    # Set scene name
    #   name: Scene name (12 characters)
    #   nanoKONTROL1 only
    def set_scene_name(self, name):
        if self.device_type == 'nanoKONTROL1':
            for i,c in enumerate(name[:12]):
                self.data[i] = ord(c)


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
        if self.device_type == 'nanoKONTROL1' and chan < 16:
            self.data[12] = chan


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
        if self.device_type == 'nanoKONTROL2' and mode < 1:
            self.data[2] = mode
        return 0


    # Get group MIDI channel
    #   returns: MIDI channel
    def get_group_channel(self, group):
        if group < len(control_map[self.device_type]['groups']):
            group_offset = control_map[self.device_type]['groups'][group]
            channel_offset = control_map[self.device_type]['group map']['channel']
            return self.data[group_offset + channel_offset]
        return 0


    # Set group MIDI channel
    #   chan: MIDI channel
    def set_group_channel(self, group, chan):
        if group < len(control_map[self.device_type]['groups']) and chan <= 16:
            group_offset = control_map[self.device_type]['groups'][group]
            channel_offset = control_map[self.device_type]['group map']['channel']
            self.data[group_offset + channel_offset] = chan


    # Get control parameter
    #   group_offset: Offset of group / transport
    #   control: Control name, e.g. 'button_a'
    #   param: Control parameter ['assign', 'behaviour', 'cc/note', 'off', 'on']
    #   returns: Parameter value or 0 if parameter not available
    def get_control_parameter(self, group_offset, control, param):
        try:
            control_offset = control_map[self.device_type]['group map'][control]
            param_offset = control_map[self.device_type]['param map'][param][0]
            return self.data[group_offset + control_offset + param_offset]
        except:
            return 0


    # Set control parameter
    #   group_offset: Offset of group / transport
    #   control: Control name, e.g. 'button_a'
    #   param: Control parameter ['assign', 'behaviour', 'cc/note', 'off', 'on']
    #   value: Parameter value
    def set_control_parameter(self, group_offset, control, param, value):
        try:
            control_offset = control_map[self.device_type]['group map'][control]
            param_offset = control_map[self.device_type]['param map'][param][0]
            param_max = control_map[self.device_type]['param map'][param][1]
            if value > param_max:
                return False
            self.data[group_offset + control_offset + param_offset] = value
        except:
            return False
        return True


    # Get configuration info about a control as text
    #   control Name of control, e.g. "prime 1"
    def get_info(self, control):
        parts = control.split()
        if parts[0] in ('slider', 'knob', 'button_a', 'solo', 'button_b', 'mute', 'button_c', 'prime'):
            group = int(parts[1])
            group_offset = control_map[self.device_type]['groups'][group]
            title = parts[0].replace('_', ' ').capitalize() + " " + str(group + 1)
        elif parts[0] in ('transport 1', 'prev_track', 'transport 2', 'next_track', 'transport 3', 'cycle', 'transport 4', 'set_marker', 'transport 5', 'prev_marker', 'transport 6', 'next_marker', 'transport 7', 'rew', 'transport 8', 'ff', 'transport 9', 'stop', 'play', 'rec'):
            group_offset = control_map[self.device_type]['transport']
            title = parts[0].replace('_', ' ').capitalize()
        else:
            return control
        assign = assign_options[self.get_control_parameter(group_offset, parts[0], 'assign')]
        cc_note = self.get_control_parameter(group_offset, parts[0], 'cc/note')
        return "{}\n{}: {}\n{}\nMin: {}\nMax: {}".format(
            title,
            assign,
            cc_note,
            behaviour_options[self.get_control_parameter(group_offset, parts[0], 'behaviour')],
            self.get_control_parameter(group_offset, parts[0], 'off'),
            self.get_control_parameter(group_offset, parts[0], 'on')
        )

scene_data = scene()

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
    try:
        ev = [0xF0, 0x42, 0x40 | midi_chan] + sysex_device_type[scene_data.device_type] + data + [0xF7]
    except Exception as e:
        logging.warning(e)


# Request current scene data dump from device
def send_dump_request():
    send_command_list([0x1F, 0x10, 0x00])


# Request current temporary scene data be saved on device
#   scene: Index of scene to save [0..3, Default: 0]
def send_scene_write_request(scene=0):
    if scene < 0 or scene > 3:
        return
    send_command_list([0x1F, 0x11, scene])


# Request native mode in (nanoKONTROL2)
def send_native_mode():
    send_command_list([0x00, 0x00, 0x00])


# Request native mode out (nanoKONTROL2)
def send_native_mode():
    send_command_list([0x00, 0x00, 0x01])


# Request mode (nanoKONTROL2)
def send_query_mode():
    send_command_list([0x1F, 0x12, 0x00])



# Request a scene change (nanoKONTROL1)
#   scene: Requested scene [0..3]
def send_scene_change_request(scene):
    if(scene >= 0 and scene <= 3):
        send_command_list([0x1F, 0x14, scene, 0xF7])


# Upload a scene to device "current scene"
# Must write scene to save to persistent memory
def send_scene_data():
    if scene_data.device_type == 'nanoKONTROL1':
        send_command_list([0x7F, 0x7F, 0x02, 0x02, 0x26, 0x40] + scene_data.get_midi_data())
    elif scene_data.device_type == 'nanoKONTROL2':
        send_command_list([0x7F, 0x7F, 0x02, 0x03, 0x05, 0x40] + scene_data.get_midi_data())


# Send port detect request
def send_port_detect():
    send_command_list([0x1E, 0x00, echo_id])

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


# Handle device search request button
def on_device_type_press():
    global device_type
    device_type.set('-')
    send_device_search()


# Blink each LED
def test_leds():
    global ev
    for led in range(0x29, 0x2F):
        ev = [0xBF, led, 0x7F]
        sleep(0.05)
        ev = [0xBF, led, 0x00]
        sleep(0.05)
    for group in range(8):
        for fn in range(3):
            led = 0x20 +  0x10 * fn + group
            ev = [0xBF, led, 0x7F]
            sleep(0.05)
            ev = [0xBF, led, 0x00]
            sleep(0.05)



def assert_editor():
    scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'assign', editor_assign.get())
    scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'behaviour', editor_behaviour.get())
    scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'cc/note', editor_cmd.get())
    scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'off', editor_min.get())
    scene_data.set_control_parameter(editor_group_offset, editor_ctrl, 'on', editor_max.get())


# Show the control editor
#   ctrl: Name of the control to edit
#   group: Control group or None (default) for transport controls
def show_editor(ctrl, group=None):
    global editor_group_offset
    global editor_assign
    global editor_behaviour
    global editor_cmd
    global editor_min
    global editor_max
    global editor_ctrl
    global rb_editor_note
    global rb_editor_momentary
    global rb_editor_toggle
    global lbl_editor_min
    global lbl_editor_max

    editor_ctrl = ctrl
    is_button = editor_ctrl not in ('knob', 'slider')

    if group is None:
        editor_group_offset = control_map[scene_data.device_type]['transport']
        editor_title.set('{}'.format(ctrl))
    elif group < len(control_map[scene_data.device_type]['groups']):
        editor_group_offset = control_map[scene_data.device_type]['groups'][group]
        editor_title.set('{} {}'.format(ctrl, group + 1))

    if is_button:
        rb_editor_note.grid()
        editor_behaviour.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'behaviour'))
        rb_editor_momentary.grid()
        rb_editor_toggle.grid()
        lbl_editor_min['text'] = "Off"
        lbl_editor_max['text'] = "On"
    else:
        rb_editor_note.grid_remove()
        rb_editor_momentary.grid_remove()
        rb_editor_toggle.grid_remove()
        lbl_editor_min['text'] = "Min"
        lbl_editor_max['text'] = "Max"

    editor_assign.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'assign'))
    editor_cmd.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'cc/note'))
    editor_min.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'off'))
    editor_max.set(scene_data.get_control_parameter(editor_group_offset, editor_ctrl, 'on'))



root = tk.Tk()
root.title("riban nanoKONTROL editor")

editor_assign = tk.IntVar()
editor_behaviour = tk.IntVar()
editor_cmd = tk.IntVar()
editor_min = tk.IntVar()
editor_max = tk.IntVar()
editor_group_offset = 0
editor_ctrl = ''


frame_top = tk.Frame(root, padx=2, pady=2)
frame_editor = tk.Frame(root, padx=2, pady=2)

frame_top.grid(row=0, columnspan=2, sticky='n')
frame_editor.grid(row=1, column=1, sticky='nw')
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

## Top frame ##

ttk.Label(frame_top, text="riban nanoKONTROL editor").grid(columnspan=6)

jack_source = tk.StringVar()
ttk.Label(frame_top, text="MIDI input: ").grid(row=1, column=0)
cmb_jack_source = ttk.Combobox(frame_top, textvariable=jack_source, state='readonly')
cmb_jack_source.bind('<<ComboboxSelected>>', jack_source_changed)
cmb_jack_source.grid(row=1, column=1)

txt_midi_in = tk.StringVar()
lbl_midi_in = ttk.Label(frame_top, textvariable=txt_midi_in, anchor='w', background='#aacf55', width=20)
lbl_midi_in.grid(row=2, column=0, columnspan=2, sticky='ew')

jack_dest = tk.StringVar()
ttk.Label(frame_top, text="MIDI output: ").grid(row=1, column=2)
cmb_jack_dest = ttk.Combobox(frame_top, textvariable=jack_dest, state='readonly')
cmb_jack_dest.bind('<<ComboboxSelected>>', jack_dest_changed)
cmb_jack_dest.grid(row=1, column=3)

device_type = tk.StringVar(value='-')
ttk.Label(frame_top, text="Device: ").grid(row=1, column=4)
btn_device_type = ttk.Button(frame_top, textvariable=device_type, command=on_device_type_press)
btn_device_type.grid(row=1, column=5)

btn_get_scene = ttk.Button(frame_top, text="Get Scene", command=send_dump_request)
btn_get_scene.grid(row=1, column=6)

btn_send_scene = ttk.Button(frame_top, text="Send Scene", command=send_scene_data)
btn_send_scene.grid(row=2, column=6)

btn_write_scene = ttk.Button(frame_top, text="Write Scene", command=send_scene_write_request)
btn_write_scene.grid(row=2, column=7)

btn_test_leds = ttk.Button(frame_top, text="Test LEDs", command=test_leds)
btn_test_leds.grid(row=1, column=7)

## Control editor frame ##

editor_title = tk.StringVar()

tk.Label(frame_editor, textvariable=editor_title).grid(row=0, column=0, columnspan=3)
tk.Radiobutton(frame_editor, text="Disabled", variable=editor_assign, value=0).grid(row=1, column=0, sticky='w')
tk.Radiobutton(frame_editor, text="CC", variable=editor_assign, value=1).grid(row=1, column=1, sticky='w')
rb_editor_note = tk.Radiobutton(frame_editor, text="Note", variable=editor_assign, value=2)
rb_editor_note.grid(row=1, column=2, sticky='w')
rb_editor_momentary = tk.Radiobutton(frame_editor, text="Momentary", variable=editor_behaviour, value=0)
rb_editor_momentary.grid(row=2, column=0, sticky='w')
rb_editor_toggle = tk.Radiobutton(frame_editor, text="Toggle", variable=editor_behaviour, value=1)
rb_editor_toggle.grid(row=2, column=1, sticky='w')
tk.Label(frame_editor, text="CC").grid(row=3, column=0, sticky='w')
tk.Spinbox(frame_editor, from_=0, to=127, textvariable=editor_cmd, width=3).grid(row=3, column=1, sticky='w')
lbl_editor_min = tk.Label(frame_editor, text="Off")
lbl_editor_min.grid(row=4, column=0, sticky='w')
tk.Spinbox(frame_editor, from_=0, to=127, textvariable=editor_min, width=3).grid(row=4, column=1, sticky='w')
lbl_editor_max = tk.Label(frame_editor, text="On")
lbl_editor_max.grid(row=5, column=0, sticky='w')
tk.Spinbox(frame_editor, from_=0, to=127, textvariable=editor_max, width=3).grid(row=5, column=1, sticky='w')
ttk.Button(frame_editor, text="OK", command=assert_editor).grid(row=6, column=1, sticky='w')
    

# Handle mouse click on image
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
            'solo': [0.00, 0.44, 0.03, 0.54],
            'mute': [0.00, 0.70, 0.03, 0.80]
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
            'rec': [0.00, 0.76, 0.03, 0.86],
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
    x = event.x / 800
    y = event.y / 250
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
                #print("Clicked on control {} {}".format(ctrl, group + 1))
                show_editor(ctrl, group)
    else:
        for ctrl in transport_ctrl_coords:
            if x > transport_ctrl_coords[ctrl][0] and y > transport_ctrl_coords[ctrl][1] and x < transport_ctrl_coords[ctrl][2] and y < transport_ctrl_coords[ctrl][3]:
                #print("Clicked on control {}".format(ctrl))
                show_editor(ctrl)

## Device image ##

img1 = ImageTk.PhotoImage(Image.open('nanoKONTROL1.png').resize((800,250), Image.ANTIALIAS))
img2 = ImageTk.PhotoImage(Image.open('nanoKONTROL2.png').resize((800,250), Image.ANTIALIAS))
canvas = tk.Canvas(root)
device_image = canvas.create_image(0, 0, anchor='nw', image=img2)
root.grid_columnconfigure(0, minsize=800)
canvas.grid(row=1, column=0, sticky='nsew')
canvas.bind('<Button-1>', on_canvas_click)


# Set the device type
#   type: Device type ['nanoKONTROL1', 'nanoKONTROL2']
def set_device_type(type):
    device_type.set(type)
    scene_data.device_type = type
    scene_data.reset_data()
    if type == 'nanoKONTROL1':
        btn_test_leds.grid_remove()
        canvas.itemconfigure(device_image, image=img1, state=tk.NORMAL)

    elif type == 'nanoKONTROL2':
        btn_test_leds.grid()
        btn_test_leds.grid()
        canvas.itemconfigure(device_image, image=img2, state=tk.NORMAL)


##########
## JACK ##
##########

@client.set_process_callback
def process(frames):
    global ev
    global midi_chan
    global device_type

    midi_out.clear_buffer()
    if ev:
        midi_out.write_midi_event(0, ev)
        ev = None
    
    # Process incoming messages
    for offset, indata in midi_in.incoming_midi_events():
        data = struct.unpack('{}B'.format(len(indata)), indata)
        str = "[{}] ".format(len(data))
        for i in data:
            str += "{:02X} ".format(i)
        #print(str)
        txt_midi_in.set(str)

        if len(data) == 14 and data[:2] == (0xF0, 0x7E) and data[3:5] == (0x06, 0x02, 0x42):
            # Device inquiry reply
            midi_chan = data[2]
            major = data[12] + (data[13 << 7])
            minor = data[10] + (data[11] << 7)
        elif data[:4] == (0xF0, 0x42, 0x50, 0x01) and data[5] == echo_id:
            # Search device reply
            midi_chan = data[4]
            family_id = data[6] + (data[7] << 7)
            member_id = data[8] + (data[9] << 7)
            minor = data[10]  + (data[11]<< 7)
            major = data[12] + (data[13]<< 7)
            if family_id == 132:
                set_device_type('nanoKONTROL1')
            elif family_id == 147:
                set_device_type('nanoKONTROL2')
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
        elif len(data) > 10 and data[:7] == [0xF0, 0x42, 0x40 | midi_chan] + sysex_device_type:
            # Command list
            if data[7:13] == [0x7F, 0x7F, 0x02, 0x03, 0x05, 0x40]:
                # nanoKONTROL2 data dump
                scene_data.set_data(data[13:-1])
            elif data[7:13] == [0x7F, 0x7F, 0x02, 0x02, 0x26, 0x40]:
                # nanoKONTROL1 data dump
                scene_data.set_data(data[13:-1])
            elif data[7:10] == [0x5F, 0x23, 0x00]:
                # Load data ACK
                #TODO: Indicate successful reception of data
                pass
            elif data[7:10] == [0x5F, 0x24, 0x00]:
                # Load data NAK
                #TODO: Indicate failed reception of data
                pass
            elif data[7:10] == [0x5F, 0x21, 0x00]:
                # Write completed
                #TODO: Indicate successful data write
                pass
            elif data[7:10] == [0x5F, 0x22, 0x00]:
                # Write error
                #TODO: Indicate failed data write
                pass
        elif data[7:10] == [0x40, 0x00, 0x02]:
            # Native mode out
            pass
        elif data[7:10] == [0x40, 0x00, 0x03]:
            # Native mode in
            pass
        elif data[7:10] == [0x5F, 0x42, 0x00]:
            # Normal mode
            pass
        elif data[7:10] == [0x5F, 0x42, 0x01]:
            # Native mode
            pass
        

# Refresh jack MIDI ports
@client.set_graph_order_callback
def refresh_jack_ports():
    global cmb_jack_source
    global cmb_jack_dest

    jack_source_ports = []
    ports = client.get_ports(is_midi=True, is_output=True)
    ports.remove(midi_out)
    for port in ports:
        jack_source_ports.append(port.name)
    cmb_jack_source['values'] = jack_source_ports

    jack_dest_ports = []
    ports = client.get_ports(is_midi=True, is_input=True)
    ports.remove(midi_in)
    for port in ports:
        jack_dest_ports.append(port.name)
    cmb_jack_dest['values'] = jack_dest_ports

# Activate jack client and get available MIDI ports
client.activate()

set_device_type('nanoKONTROL2')

root.mainloop()
