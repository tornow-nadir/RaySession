
from patchcanvas import patchcanvas
from gui_server_thread import GUIServerThread

# Port Type
PORT_TYPE_NULL = 0
PORT_TYPE_AUDIO = 1
PORT_TYPE_MIDI = 2

# Port Mode
PORT_MODE_NULL = 0
PORT_MODE_INPUT = 1
PORT_MODE_OUTPUT = 2

# Port Flags
PORT_IS_INPUT = 0x01
PORT_IS_OUTPUT = 0x02
PORT_IS_PHYSICAL = 0x04
PORT_CAN_MONITOR = 0x08
PORT_IS_TERMINAL = 0x10
PORT_IS_CONTROL_VOLTAGE = 0x100

USE_ALIAS_NONE = 0
USE_ALIAS_1 = 1
USE_ALIAS_2 = 2


class Connection:
    def __init__(self, connection_id: int, port_out, port_in):
        self.connection_id = connection_id
        self.port_out = port_out
        self.port_in = port_in
    
    def add_to_canvas(self):
        patchcanvas.connectPorts(
            self.connection_id,
            self.port_out.group_id, self.port_out.port_id,
            self.port_in.group_id, self.port_in.port_id)
        
    def remove_from_canvas(self):
        patchcanvas.disconnectPorts(self.connection_id)


class Port:
    display_name = ''
    group_id = -1
    portgroup_id = 0
    prevent_stereo = False
    set_the_one_on_pair = False

    def __init__(self, port_id: int, name: str, alias_1: str, alias_2: str,
                 port_type: int, flags: int, metadata: str):
        self.port_id = port_id
        self.full_name = name
        self.alias_1 = alias_1
        self.alias_2 = alias_2
        self.type = port_type
        self.flags = flags
        self.metadata = metadata

    def mode(self):
        if self.flags & PORT_IS_OUTPUT:
            return PORT_MODE_OUTPUT
        elif self.flags & PORT_IS_INPUT:
            return PORT_MODE_INPUT
        else:
            return PORT_MODE_NULL

    def set_the_one(self):
        self.display_name += ' 1'
        self.set_the_one_on_pair = False
        self.change_canvas_properties()

    def add_to_canvas(self):
        port_mode = PORT_MODE_NULL
        if self.flags & PORT_IS_INPUT:
            port_mode = PORT_MODE_INPUT
        elif self.flags & PORT_IS_OUTPUT:
            port_mode = PORT_MODE_OUTPUT
        else:
            return

        patchcanvas.addPort(self.group_id, self.port_id, self.display_name,
                            port_mode, self.type, self.portgroup_id)
    
    def remove_from_canvas(self):
        patchcanvas.removePort(self.group_id, self.port_id)
    
    def change_canvas_properties(self):
        patchcanvas.changePortProperties(self.group_id, self.port_id,
                                         self.portgroup_id, self.display_name)


class Portgroup:
    # Portgroup is a stereo pair of ports
    # but could be a group of more ports
    def __init__(self, group_id: int, portgroup_id: int, port_mode: int):
        self.group_id = group_id
        self.portgroup_id = portgroup_id
        self.port_mode = port_mode
        self.ports = []
    
    def add_ports(self, *ports):
        for port in ports:
            port.portgroup_id = self.portgroup_id
            self.ports.append(port)
    
    def add_to_canvas(self):
        if len(self.ports) < 2:
            return
        
        port_mode = self.ports[0].mode()
        port_type = self.ports[0].type

        patchcanvas.addPortGroup(self.group_id, self.portgroup_id,
                                 self.port_mode, port_type)
        for port in self.ports:
            patchcanvas.addPortToPortGroup(
                self.group_id, port.port_id, self.portgroup_id)

    def remove_from_canvas(self):
        for port in self.ports:
            port.portgroup_id = 0

        patchcanvas.removePortGroup(self.group_id, self.portgroup_id)


class Group:
    def __init__(self, group_id: int, name: str):
        self.group_id = group_id
        self.name = name
        self.display_name = name
        self.ports = []
        self.portgroups = []
        self._is_hardware = False
        self.client_icon = ''

    def add_to_canvas(self):
        icon_type = patchcanvas.ICON_APPLICATION
        icon_name = ""

        icon_name = self.name.partition('.')[0].lower()
        
        if self._is_hardware:
            icon_type = patchcanvas.ICON_HARDWARE
            if self.name == "a2j":
                icon_name = "a2j"
        if self.client_icon:
            icon_type = patchcanvas.ICON_CLIENT
            icon_name = self.client_icon

        if self.name.startswith("PulseAudio "):
            self.display_name = self.name.replace(' ', '/', 1)

        patchcanvas.addGroup(self.group_id, self.display_name,
                             patchcanvas.SPLIT_UNDEF,
                             icon_type, icon_name)
    
    def remove_from_canvas(self):
        patchcanvas.removeGroup(self.group_id)

    def set_port_alignments(self):
        pass
        #inputs, outputs = 0
        
        #input_names = []
        #output_names = []
        
        #for port in self.ports:
            #if port.flags & PORT_IS_INPUT:
                #input_names.append(port.display_name)
            #elif port.flags & PORT_IS_OUTPUT:
                #output_names.append(port.display_name)
        
        #if not (input_names and output_names):
            #return
        
        #if len(input_names) == len(output_names):
            #return
        
        #align_max = abs(len(input_names) - len(output_names))
        #align_done = 0
        
        #if len(input_names) < len(output_names):
            #for i in range(len(input_names)):
                #if input_names[i] in output_names:
                    #index_diff = output_names.index(input_names[i]) -i + align_done
                    #if index_diff < 0:
                        #continue
                    #if index_diff > 
        

    def midi_alignable(self)->int:
        in_audio = in_midi = out_audio = out_midi = 0

        for port in self.ports:
            if port.flags & PORT_IS_INPUT:
                if port.type == PORT_TYPE_AUDIO:
                    in_audio += 1
                elif port.type == PORT_TYPE_MIDI:
                    in_midi += 1
            elif port.flags & PORT_IS_OUTPUT:
                if port.type == PORT_TYPE_AUDIO:
                    out_audio += 1
                elif port.type == PORT_TYPE_MIDI:
                    out_midi += 1

        if in_audio <= out_audio:
            if in_midi <= out_midi:
                return PORT_MODE_INPUT
        else:
            if out_midi <= in_midi:
                return PORT_MODE_OUTPUT

        return PORT_MODE_NULL

    def add_port(self, port, use_alias: int):
        port_full_name = port.full_name
        
        if use_alias == USE_ALIAS_1:
            port_full_name = port.alias_1
        elif use_alias == USE_ALIAS_2:
            port_full_name = port.alias_2
        
        port.group_id = self.group_id
        
        if (port_full_name.startswith('a2j:')
                and not port.flags & PORT_IS_PHYSICAL):
            port_full_name = port_full_name.partition(':')[2]
        port.display_name = port_full_name.partition(':')[2]

        if not self.ports:
            # we are adding the first port of the group
            if port.flags & PORT_IS_PHYSICAL:
                self._is_hardware = True
        
        self.ports.append(port)
    
    def remove_port(self, port):
        if port in self.ports:
            self.ports.remove(port)
    
    def set_client_icon(self, icon_name:str):
        self.client_icon = icon_name
    
    def get_pretty_client(self):
        for client_name in ('firewire_pcm', 'a2j',
                            'Hydrogen', 'ardour', 'Ardour', 'Qtractor',
                            'SooperLooper', 'sooperlooper', 'Luppp',
                            'seq64', 'calfjackhost'):
            if self.name == client_name:
                return client_name

            if self.name.startswith(client_name + '_'):
                if self.name.replace(client_name + '_', '', 1).isdigit():
                    return client_name
            
            if self.name.startswith(client_name + '.'):
                # TODO or to check what happens
                return client_name
        return ''
    
    def graceful_port(self, port):
        def split_end_digits(name: str)->tuple:
            num = ''
            while name and name[-1].isdigit():
                num = name[-1] + num
                name = name[:-1]
            
            return (name, num)
        
        def cut_end(name: str, *ends: str)->str:
            for end in ends:
                if name.endswith(end):
                    return name.rsplit(end)[0]
            return name
            
        client_name = self.get_pretty_client()
        
        display_name = port.display_name
        s_display_name = display_name
        
        if client_name == 'firewire_pcm':
            if '(' in display_name and ')' in display_name:
                after_para = display_name.partition('(')[2]
                display_name = after_para.rpartition(')')[0]
                display_name, num = split_end_digits(display_name)
                
                if num:
                    if display_name.endswith(':'):
                        display_name = display_name[:-1]
                    display_name += ' ' + num
            else:
                display_name = display_name.partition('_')[2]
                display_name = cut_end(display_name, '_in', '_out')
                
        elif client_name == 'Hydrogen':
            if display_name.startswith('Track_'):
                display_name = display_name.replace('Track_', '', 1)
                
                num, udsc, name = display_name.partition('_')
                if num.isdigit():
                    display_name = num + ' ' + name
            
            if display_name.endswith('_Main_L'):
                display_name = display_name.replace('_Main_L', ' L', 1)
            elif display_name.endswith('_Main_R'):
                display_name = display_name.replace('_Main_R', ' R', 1)
        
        elif client_name == 'a2j':
            name_1, colon, name_2 = display_name.partition(':')
            if name_2:
                display_name = name_2
                
                if display_name.startswith(' '):
                    display_name = display_name[1:]
                
                display_name = cut_end(display_name, ' Port-0', ' MIDI 1')
                    
        elif client_name in ('ardour', 'Ardour'):
            display_name, num = split_end_digits(display_name)
            if num:
                display_name = cut_end(display_name,
                                       '/audio_out ', '/audio_in ',
                                       '/midi_out ', '/midi_in ')
                if num == '1':
                    port.set_the_one_on_pair = True
                else:
                    display_name += ' ' + num
        
        elif client_name == 'Qtractor':
            display_name, num = split_end_digits(display_name)
            if num:
                display_name = cut_end(display_name,
                                       '/in_', '/out_')
                if num == '1':
                    port.set_the_one_on_pair = True
                else:
                    display_name += ' ' + num
        
        elif client_name in ('SooperLooper', 'sooperlooper'):
            display_name, num = split_end_digits(display_name)
            if num:
                display_name = cut_end(display_name,
                                       '_in_', '_out_')
                if num == '1':
                    port.set_the_one_on_pair = True
                else:
                    display_name += ' ' + num
                    
        elif client_name == 'Luppp':
            if display_name.endswith('\n'):
                display_name = display_name[:-1]
            
            display_name = display_name.replace('_', ' ')
        
        elif client_name == 'seq64':
            display_name = display_name.replace('seq64 midi ', '', 1)
        
        elif client_name == 'calfjackhost':
            display_name, num = split_end_digits(display_name)
            if num:
                display_name = cut_end(display_name,
                                       ' Out #', ' In #')
                
                display_name += " " + num
        
        elif not client_name:
            display_name = display_name.replace('_', ' ')
        
        port.display_name = display_name if display_name else s_display_name
    
    def add_portgroup(self, portgroup):
        self.portgroups.append(portgroup)
    
    def stereo_detection(self, port):
        if port.type != PORT_TYPE_AUDIO:
            return
        
        # find the last port with same type and mode in the group
        for other_port in reversed(self.ports):
            if other_port == port:
                continue
            
            if (other_port.type == port.type
                    and other_port.mode() == port.mode()
                    and not other_port.portgroup_id
                    and not other_port.prevent_stereo):
                break
        else:
            return

        may_match_list = []
        
        port_name = port.full_name.replace(self.name + ':', '', 1)
        other_port_name = other_port.full_name.replace(self.name + ':', '', 1)

        if port.flags & PORT_IS_PHYSICAL:
            # force stereo detection for system ports
            # it forces it for firewire long and strange names
            may_match_list.append(other_port_name)
        
        elif port_name[-1].isdigit():
            # Port ends with digit
            base_port = port_name[:-1]
            in_num = port_name[-1]

            while base_port[-1].isdigit():
                in_num = base_port[-1] + in_num
                base_port = base_port[:-1]
            
            # if Port ends with Ldigits or Rdigits
            if base_port.endswith('R'):
                may_match_list.append(base_port[:-1] + 'L' + in_num)
            else:
                may_match_list.append(base_port + str(int(in_num) -1))
                
                if int(in_num) in (1, 2):
                    if base_port.endswith((' ', ('_'))):
                        may_match_list.append(base_port[:-1])
                    else:
                        may_match_list.append(base_port)
        else:
            # Port ends with non digit
            if port_name.endswith('R'):
                may_match_list.append(port_name[:-1] + 'L')
                if len(port_name) >= 2:
                    if port_name[-2] == ' ':
                        may_match_list.append(port_name[:-2])
                    else:
                        may_match_list.append(port_name[:-1])
            
            elif port_name.endswith('right'):
                may_match_list.append(port_name[:-5] + 'left')
                
            elif port_name.endswith('Right'):
                may_match_list.append(port_name[:-5] + 'Left')
                
            elif port_name.endswith('(Right)'):
                may_match_list.append(port_name[:-7] + '(Left)')
                
            elif port_name.endswith('.r'):
                may_match_list.append(port_name[:-2] + '.l')
            
            elif port_name.endswith('_r'):
                may_match_list.append(port_name[:-2] + '_l')
            
            elif port_name.endswith('_r\n'):
                may_match_list.append(port_name[:-3] + '_l\n')
            
            for x in ('out', 'Out', 'output', 'Output', 'in', 'In',
                      'input', 'Input', 'audio input', 'audio output'):
                if port_name.endswith('R ' + x):
                    may_match_list.append('L ' + x)
                    
                elif port_name.endswith('right ' + x):
                    may_match_list.append('left ' + x)
                    
                elif port_name.endswith('Right ' + x):
                    may_match_list.append('Left ' + x)
        
        if other_port_name in may_match_list:
            return other_port

        
class PatchbayManager:
    def __init__(self, session):
        self.session = session
        self.group_positions = []
        self.groups = []
        self.connections = []
        self._next_group_id = 0
        self._next_port_id = 0
        self._next_portgroup_id = 1
        self._next_connection_id = 0
        
        self.use_alias = USE_ALIAS_NONE
        
    def send_to_patchbay_daemon(self, *args):
        server = GUIServerThread.instance()
        if not server:
            return
        
        if server.patchbay_addr is None:
            return
            
        server.send(server.patchbay_addr, *args)

    def send_to_daemon(self, *args):
        server = GUIServerThread.instance()
        if not server:
            return
        server.toDaemon(*args)

    def canvas_callbacks(self, action, value1, value2, value_str):
        if action == patchcanvas.ACTION_GROUP_INFO:
            pass

        elif action == patchcanvas.ACTION_GROUP_RENAME:
            pass

        elif action == patchcanvas.ACTION_GROUP_SPLIT:
            group_id = value1
            patchcanvas.splitGroup(group_id)

        elif action == patchcanvas.ACTION_GROUP_JOIN:
            group_id = value1
            patchcanvas.joinGroup(group_id)
        
        elif action == patchcanvas.ACTION_GROUP_MOVE:
            group_id = value1
            in_or_out = value2
            x_y_str = value_str
            
            str_x, colon, str_y = x_y_str.partition(':')
            
            for group in self.groups:
                if group.group_id == group_id:
                    self.send_to_daemon(
                        '/ray/server/patchbay/save_coordinates',
                        in_or_out, group.name, int(str_x), int(str_y))
                    break
        
        elif action == patchcanvas.ACTION_PORT_GROUP_ADD:
            g_id, p_mode, p_type, p_id1, p_id2 =  [
                int(i) for i in value_str.split(":")]
            
            print('add_new_group_from_canvsss', self._next_portgroup_id, g_id)
            portgroup = Portgroup(g_id, self._next_portgroup_id, p_mode)
            self._next_portgroup_id += 1
            
            
            for port_id in p_id1, p_id2:
                port = self.get_port_from_id(port_id)
                portgroup.add_ports(port)
            
            for group in self.groups:
                if group.group_id == g_id:
                    group.add_portgroup(portgroup)
            
            portgroup.add_to_canvas()
            
            #patchcanvas.addPortGroup(g_id, pg_id, p_mode, p_type)
            #patchcanvas.addPortToPortGroup(g_id, p_id1, pg_id)
            #patchcanvas.addPortToPortGroup(g_id, p_id2, pg_id)
        
        elif action == patchcanvas.ACTION_PORT_GROUP_REMOVE:
            
            group_id = value1
            portgrp_id = value2

            for group in self.groups:
                if group.group_id == group_id:
                    for portgroup in group.portgroups:
                        if portgroup.portgroup_id == portgrp_id:
                            group.portgroups.remove(portgroup)
                            portgroup.remove_from_canvas()
                            break
                    break
        
        elif action == patchcanvas.ACTION_PORT_INFO:
            pass

        elif action == patchcanvas.ACTION_PORT_RENAME:
            pass

        elif action == patchcanvas.ACTION_PORTS_CONNECT:
            g_out, p_out, g_in, p_in = [int(i) for i in value_str.split(":")]

            port_out = self.get_port_from_id(p_out)
            port_in = self.get_port_from_id(p_in)
            
            if port_out is None or port_in is None:
                return

            self.send_to_patchbay_daemon(
                '/ray/patchbay/connect',
                port_out.full_name, port_in.full_name)

        elif action == patchcanvas.ACTION_PORTS_DISCONNECT:
            connection_id = value1
            for connection in self.connections:
                if connection.connection_id == connection_id:
                    self.send_to_patchbay_daemon(
                        '/ray/patchbay/disconnect',
                        connection.port_out.full_name, 
                        connection.port_in.full_name)
                    break

        elif action == patchcanvas.ACTION_DOUBLE_CLICK:
            server = GUIServerThread.instance()
            if server:
                server._session._main_win.toggleSceneFullScreen()

        elif action == patchcanvas.ACTION_INLINE_DISPLAY:
            pass

    def get_port_from_name(self, port_name: str):
        for group in self.groups:
            for port in group.ports:
                if port.full_name == port_name:
                    return port
    
    def get_port_from_id(self, port_id: int):
        for group in self.groups:
            for port in group.ports:
                if port.port_id == port_id:
                    return port
    
    def get_client_icon(self, group_name: str)->str:
        for client in self.session.client_list:
            if (client.name == group_name
                    or client.name + '.' + client.client_id == group_name):
                return client.icon
        return ''
    
    def add_port(self, name: str, alias_1: str, alias_2: str,
                 port_type: int, flags: int, metadata: str):
        port = Port(self._next_port_id, name, alias_1, alias_2,
                    port_type, flags, metadata)
        self._next_port_id += 1

        full_port_name = name
        if self.use_alias == USE_ALIAS_1:
            full_port_name = alias_1
        elif self.use_alias == USE_ALIAS_2:
            full_port_name = alias_2
        
        group_name, colon, port_name = full_port_name.partition(':')
        
        if (full_port_name.startswith('a2j:')
                and not port.flags & PORT_IS_PHYSICAL):
            group_name, colon, port_name = port_name.partition(':')
            group_name = group_name.rpartition(' [')[0]
        
        group_is_new = False

        for group in self.groups:
            if group.name == group_name:
                break
        else:
            # port is an non existing group, create the group
            group = Group(self._next_group_id, group_name)
            client_icon = self.get_client_icon(group_name)
            group.set_client_icon(client_icon)
            
            self._next_group_id += 1
            self.groups.append(group)
            group_is_new = True
        
        group.add_port(port, self.use_alias)
        group.graceful_port(port)
        
        if group_is_new:
            group.add_to_canvas()
            
            for gp in self.group_positions:
                if gp['group'] == group.name:
                    patchcanvas.moveGroupBox(
                        group.group_id, gp['in_or_out'], gp['x'], gp['y'])
                
        port.add_to_canvas()
        
        other_port = group.stereo_detection(port)
        if other_port is not None:
            portgroup = Portgroup(group.group_id, self._next_portgroup_id,
                                  port.mode())
            self._next_portgroup_id += 1
            portgroup.add_ports(other_port, port)
            group.add_portgroup(portgroup)
            
            if other_port.set_the_one_on_pair:
                other_port.set_the_one()
            
            portgroup.add_to_canvas()

    def remove_port(self, name: str):
        port = self.get_port_from_name(name)
        if port is None:
            return
        
        for group in self.groups:
            if group.group_id == port.group_id:
                group.remove_port(port)
                port.remove_from_canvas()
                if not group.ports:
                    group.remove_from_canvas()
                    self.groups.remove(group)
                break
    
    def rename_port(self, name: str, new_name: str):
        port = self.get_port_from_name(name)
        if port is None:
            return
        
        group_name = name.partition(':')[0]
        new_group_name = new_name.partition(':')[0]
        
        # In case a port rename implies another group for the port
        if (self.use_alias == USE_ALIAS_NONE
                and group_name != new_group_name):
            for group in self.groups:
                if group.name == group_name:
                    group.remove_port(port)
                    if not group.ports:
                        self.groups.remove(group)
                    break
            
            port.remove_from_canvas()
            port.full_name = new_name

            for group in self.groups:
                if group.name == new_group_name:
                    group.add_port(port)
                    break
            else:
                group = Group(self._next_group_id, new_group_name)
                self._next_group_id += 1
                group.add_port(port)
                group.add_to_canvas()
            
            port.add_to_canvas()
            return
        
        for group in self.groups:
            if group.group_id == port.group_id:
                port.full_name = new_name
                group.graceful_port(port)
                port.change_canvas_properties()
                break
    
    def add_connection(self, port_out_name: str, port_in_name: str):
        port_out = self.get_port_from_name(port_out_name)
        port_in = self.get_port_from_name(port_in_name)
        
        if port_out is None or port_in is None:
            return
        
        for connection in self.connections:
            if (connection.port_out == port_out
                    and connection.port_in == port_in):
                return
        
        connection = Connection(self._next_connection_id, port_out, port_in)
        self._next_connection_id += 1
        self.connections.append(connection)
        connection.add_to_canvas()
    
    def remove_connection(self, port_out_name: str, port_in_name: str):
        port_out = self.get_port_from_name(port_out_name)
        port_in = self.get_port_from_name(port_in_name)
        
        if port_out is None or port_in is None:
            return
        
        for connection in self.connections:
            if (connection.port_out == port_out
                    and connection.port_in == port_in):
                self.connections.remove(connection)
                connection.remove_from_canvas()
                break
    
    def update_group_position(self, in_or_out: int, group_name: str,
                              x: int, y: int):
        for group in self.groups:
            if group.name == group_name:
                patchcanvas.moveGroupBox(group.group_id, in_or_out, x, y)
                break
        else:
            self.group_positions.append(
                {'in_or_out': in_or_out,
                 'group': group_name,
                 'x': x,
                 'y': y})

    def update_portgroup(self, group_name: str, port_mode: int,
                         port1: str, port2:str):
        pass