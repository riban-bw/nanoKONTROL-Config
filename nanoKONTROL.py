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
            'chan': 0,
            'slider': 1,
            'knob': 5,
            'button a': 9,
            'button b': 16,
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
            'button a': 13,
            'solo': 13,
            'button b': 19,
            'mute': 19,
            'button c': 25,
            'prime': 25,
            'transport 1': 1,
            'prev track': 1,
            'transport 2': 7,
            'next track': 7,
            'transport 3': 13,
            'cycle': 13,
            'transport 4': 19,
            'marker set': 19,
            'transport 5': 25,
            'prev marker': 25,
            'transport 6': 31,
            'next marker': 31,
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
            self.set_scene_name("scene 0")
        elif self.device_type == "nanoKONTROL2":
            self.set_control_mode(0)
            self.set_led_mode(0)
        self.set_global_channel(15)
        for group, group_offset in enumerate(control_map[self.device_type]['groups']):
            self.set_group_channel(group, 15)
            if self.device_type == "nanoKONTROL1":
                for i, control in enumerate(('slider', 'knob', 'button a', 'button b')):
                    self.set_control_parameter(group_offset, control, 'assign', 1)
                    self.set_control_parameter(group_offset, control, 'cc/note', 0x10 * i + group) #TODO: What is the default CC?
                    self.set_control_parameter(group_offset, control, 'off', 0)
                    self.set_control_parameter(group_offset, control, 'on', 127)
                for i, control in enumerate(('button a', 'button b')):
                    self.set_control_parameter(group_offset, control, 'behaviour', 0)
                    self.set_control_parameter(group_offset, control, 'attack', 0) #TODO: What is the default attack value
                    self.set_control_parameter(group_offset, control, 'decay', 0) #TODO: What is the default decay value
            elif self.device_type == "nanoKONTROL2":
                for i, control in enumerate(('slider', 'knob', 'solo', 'mute', 'prime', 'prime')):
                    self.set_control_parameter(group_offset, control, 'assign', 1)
                    self.set_control_parameter(group_offset, control, 'cc/note', 0x10 * i + group)
                    self.set_control_parameter(group_offset, control, 'off', 0)
                    self.set_control_parameter(group_offset, control, 'on', 127)
                    self.set_control_parameter(group_offset, control, 'behaviour', 0)

        transport_offset = control_map[self.device_type]['transport']
        if self.device_type == 'nanoKONTROL1':
            pass #TODO Implement nanoKONTROL1 transport

        elif self.device_type == 'nanoKONTROL2':
            for i, transport in enumerate(('play', 'stop', 'rew', 'ff', 'rec', 'cycle', 'prev track', 'next track', 'marker set', 'prev marker', 'next marker')):
                transport_offset = control_map[self.device_type]['group map'][transport]
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
    #   data: 8-bit Korg data
    #   returns: List containing sysex data
    def get_midi_data(self):
        sysex = []
        dest_offset = 0
        for offset in range(0, len(self.data), 7):
            b0 = 0
            sysex.append(b0)
            dest_offset += 1
            for word in range(8):
                b0 |= (self.data[offset + word] & 0x80) >> (7 - word)
                sysex.append(self.data[dest_offset] & 0x7F)
                dest_offset += 1
            sysex[offset] = b0
        return sysex


    # Set data from MIDI sysex format data
    # Convert raw 7-bit MIDI data to Korg 8-bit data
    # Raw data: 1st byte holds bit-7 of subsequent bytes, next 7 bytes hold bits 0..7 of each byte
    #   data: raw 7-bit MIDI data (multiple 8 x 7-bit blocks of data)
    def set_data(self, data):
        if len(data) // 8:
            return False # Not a valid set of 8-byte blocks
        i = 0
        for offset in range(0, len(data), 8):
            for word in range(1, 8):
                self.data[i] = (data[offset + word] | (data[offset] & 1 << (word - 1)) << 8 - word)
            i += 1


    # Get scene name
    #   returns: Scene name
    #   nanoKONTROL1 only
    def get_scene_name(self):
        name = ""
        if device_type == 'nanoKONTROL1':
            for c in self.data[:12]:
                name += chr(c)
        return name


    # Set scene name
    #   name: Scene name (12 characters)
    #   nanoKONTROL1 only
    def set_scene_name(self, name):
        if device_type == 'nanoKONTROL1':
            for i,c in enumerate(name[:12]):
                self.data[i] = ord(c)


    # Get global MIDI channel
    #   returns: MIDI channel
    def get_global_channel(self):
        if device_type == 'nanoKONTROL1':
            return self.data[12]
        elif device_type == 'nanoKONTROL2':
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
    #   control: Control name, e.g. 'button a'
    #   param: Control parameter ['assign', 'behaviour', 'cc/note', 'off', 'on']
    #   returns: Parameter value or 0 if parameter not available
    def get_control_parameter(self, group_offset, control, param):
        try:
            control_offset = control_map[self.device_type]['transport map'][control]
            param_offset = control_map[self.device_type]['param map'][param][0]
            return self.data[group_offset + control_offset + param_offset]
        except:
            return 0


    # Set control parameter
    #   group_offset: Offset of group / transport
    #   control: Control name, e.g. 'button a'
    #   param: Control parameter ['assign', 'behaviour', 'cc/note', 'off', 'on']
    #   value: Parameter value
    def set_control_parameter(self, group_offset, control, param, value):
        try:
            control_offset = control_map[self.device_type]['group map'][control]
            param_offset = control_map[self.device_type]['param_map'][param][0]
            param_max = control_map[self.device_type]['param_map'][param][1]
            if value > param_max:
                return False
            self.data[group_offset + control_offset + param_offset] = value
        except:
            return False
        return True





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
        ev = [0xF0, 0x42, 0x40 | midi_chan] + sysex_device_type[device_type.get()] + data + [0xF7]
    except Exception as e:
        logging.warning(e)


# Request current scene data dump from device
def send_dump_request():
    send_command_list([0x1F, 0x10, 0x00])


# Request current temporary scene data be saved on device
#   scene: Index of scene to save
def send_scene_write_request(scene):
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


scene_data = scene()

root = tk.Tk()
root.title("riban nanoKONTROL editor")

frame_left = tk.Frame(root, padx=2, pady=2)
frame_top = tk.Frame(root, padx=2, pady=2)
frame_controls = tk.Frame(root, padx=2, pady=2)

frame_top.grid(row=0, columnspan=2)
frame_left.grid(row=1, column=0)
frame_controls.grid(row=1, column=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(1, weight=1)

ttk.Label(frame_top, text="riban nanoKONTROL editor").grid(columnspan=6)

jack_source = tk.StringVar()
ttk.Label(frame_top, text="MIDI input: ").grid(row=1, column=0)
cmb_jack_source = ttk.Combobox(frame_top, textvariable=jack_source, state='readonly')
cmb_jack_source.bind('<<ComboboxSelected>>', jack_source_changed)
cmb_jack_source.grid(row=1, column=1)

txt_midi_in = tk.StringVar()
lbl_midi_in = ttk.Label(frame_top, textvariable=txt_midi_in, anchor='w', background='#aacf55')
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

ttk.Label(frame_left, text="TRACK").grid(row=0, columnspan=2)
btn_prev_track = tk.Button(frame_left, width=6, padx=2, pady=2, text="<")
btn_prev_track.grid(row=1, column=0)
btn_next_track = tk.Button(frame_left, width=6, padx=2, pady=2, text=">")
btn_next_track.grid(row=1, column=1)

ttk.Label(frame_left, text="MARKER").grid(row=2, column=2, columnspan=3)
btn_cycle = tk.Button(frame_left, width=6, padx=2, pady=2, text="CYCLE")
btn_cycle.grid(row=3, column=0)
btn_marker_set = tk.Button(frame_left, width=6, padx=2, pady=2, text="SET")
btn_marker_set.grid(row=3, column=2)
btn_marker_prev = tk.Button(frame_left, width=6, padx=2, pady=2, text="<")
btn_marker_prev.grid(row=3, column=3)
btn_marker_next = tk.Button(frame_left, width=6, padx=2, pady=2, text=">")
btn_marker_next.grid(row=3, column=4)

btn_rew = tk.Button(frame_left, width=6, padx=2, pady=2, text="<<")
btn_rew.grid(row=4, column=0)
btn_ff = tk.Button(frame_left, width=6, padx=2, pady=2, text=">>")
btn_ff.grid(row=4, column=1)
btn_stop = tk.Button(frame_left, width=6, padx=2, pady=2, text="STOP")
btn_stop.grid(row=4, column=2)
btn_play = tk.Button(frame_left, width=6, padx=2, pady=2, text="PLAY")
btn_play.grid(row=4, column=3)
btn_rec = tk.Button(frame_left, width=6, padx=2, pady=2, text="REC")
btn_rec.grid(row=4, column=4)

for group in range(8):
    frame_controls.columnconfigure(group * 2 + 1, weight=1)
    lbl = ttk.Label(frame_controls, text = "{}".format(group + 1))
    lbl.grid(row=0, column = group * 2 + 1)
    slider = ttk.Scale(frame_controls, orient="horizontal", from_=0, to=127, value=64)
    slider.grid(row = 1, column = group * 2 + 1)
    slider = ttk.Scale(frame_controls, orient="vertical", from_=127, to=0, value=100)
    slider.grid(row = 2, column = group * 2 + 1, rowspan=3, sticky='ns')
    btn = tk.Button(frame_controls, width=2, padx=2, pady=2, text = "S")
    btn.grid(row = 2, column=group * 2)
    btn = tk.Button(frame_controls, width=2, padx=2, pady=2, text="M")
    btn.grid(row = 3, column=group * 2)
    btn = tk.Button(frame_controls, width=2, padx=2, pady=2, text="R")
    btn.grid(row = 4, column = group * 2)


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
        str = ""
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
            if family_id == 147:
                device_type.set('nanoKONTROL2')
            elif family_id == 132:
                device_type.set('nanoKONTROL1')
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

root.mainloop()
