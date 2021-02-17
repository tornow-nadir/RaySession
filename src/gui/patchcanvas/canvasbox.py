#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# PatchBay Canvas engine using QGraphicsView/Scene
# Copyright (C) 2010-2019 Filipe Coelho <falktx@falktx.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the doc/GPL.txt file.

# ------------------------------------------------------------------------------------------------------------
# Imports (Global)

from sip import voidptr
from struct import pack

from PyQt5.QtCore import qCritical, Qt, QPointF, QRectF, QTimer
from PyQt5.QtGui import QCursor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter, QPen, QPolygonF, QColor
from PyQt5.QtWidgets import QGraphicsItem, QMenu

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom)

from . import (
    canvas,
    features,
    options,
    port_dict_t,
    CanvasBoxType,
    ANTIALIASING_FULL,
    ACTION_PLUGIN_EDIT,
    ACTION_PLUGIN_SHOW_UI,
    ACTION_PLUGIN_CLONE,
    ACTION_PLUGIN_REMOVE,
    ACTION_PLUGIN_RENAME,
    ACTION_PLUGIN_REPLACE,
    ACTION_GROUP_INFO,
    ACTION_GROUP_JOIN,
    ACTION_GROUP_SPLIT,
    ACTION_GROUP_RENAME,
    ACTION_GROUP_MOVE,
    ACTION_PORTS_DISCONNECT,
    ACTION_INLINE_DISPLAY,
    EYECANDY_FULL,
    PORT_MODE_NULL,
    PORT_MODE_INPUT,
    PORT_MODE_OUTPUT,
    PORT_TYPE_NULL,
    PORT_TYPE_AUDIO_JACK,
    PORT_TYPE_MIDI_ALSA,
    PORT_TYPE_MIDI_JACK,
    PORT_TYPE_PARAMETER,
    MAX_PLUGIN_ID_ALLOWED,
    ICON_HARDWARE,
)

from .canvasboxshadow import CanvasBoxShadow
from .canvasicon import CanvasSvgIcon, CanvasIconPixmap
from .canvasport import CanvasPort
from .canvasportgroup import CanvasPortGroup
from .theme import Theme
from .utils import (CanvasItemFX,
                    CanvasGetFullPortName, 
                    CanvasGetPortConnectionList,
                    CanvasGetPortGroupName,
                    CanvasGetPortGroupPosition,
                    CanvasCallback)

# ------------------------------------------------------------------------------------------------------------

class cb_line_t(object):
    def __init__(self, line, connection_id):
        self.line = line
        self.connection_id = connection_id

# ------------------------------------------------------------------------------------------------------------

class CanvasBox(QGraphicsItem):
    INLINE_DISPLAY_DISABLED = 0
    INLINE_DISPLAY_ENABLED  = 1
    INLINE_DISPLAY_CACHED   = 2

    def __init__(self, group_id: int, group_name: str, icon_type: int,
                 icon_name: str, parent=None):
        QGraphicsItem.__init__(self)
        self.setParentItem(parent)

        # Save Variables, useful for later
        self.m_group_id = group_id
        self.m_group_name = group_name

        # plugin Id, < 0 if invalid
        self.m_plugin_id = -1
        self.m_plugin_ui = False
        self.m_plugin_inline = self.INLINE_DISPLAY_DISABLED

        # Base Variables
        self.p_width = 50
        self.p_width_in = 0
        self.p_width_out = 0
        self.p_height = canvas.theme.box_header_height + canvas.theme.box_header_spacing + 1

        self.m_last_pos = QPointF()
        self.m_splitted = False
        self.m_splitted_mode = PORT_MODE_NULL

        self.m_cursor_moving = False
        self.m_forced_split = False
        self.m_mouse_down = False
        self.m_inline_data = None
        self.m_inline_image = None
        self.m_inline_scaling = 1.0

        self.m_port_list_ids = []
        self.m_connection_lines = []

        # Set Font
        self.m_font_name = QFont()
        self.m_font_name.setFamily(canvas.theme.box_font_name)
        self.m_font_name.setPixelSize(canvas.theme.box_font_size)
        self.m_font_name.setWeight(canvas.theme.box_font_state)

        self.m_font_port = QFont()
        self.m_font_port.setFamily(canvas.theme.port_font_name)
        self.m_font_port.setPixelSize(canvas.theme.port_font_size)
        self.m_font_port.setWeight(canvas.theme.port_font_state)

        self._is_hardware = bool(icon_type == ICON_HARDWARE)
        self._icon_name = icon_name
        
        # Icon
        if canvas.theme.box_use_icon:
            if icon_type == ICON_HARDWARE:
                port_mode = PORT_MODE_NULL
                if self.m_splitted:
                    port_mode = self.m_splitted_mode
                self.top_icon = CanvasSvgIcon(
                    icon_type, icon_name, port_mode, self)
            else:
                self.top_icon = CanvasIconPixmap(
                    icon_type, icon_name, self.m_group_name, self)
                if self.top_icon.is_null():
                    canvas.scene.removeItem(self.top_icon)
                    self.top_icon = None
        else:
            self.top_icon = None

        # Shadow
        self.shadow = None
        # FIXME FX on top of graphic items make them lose high-dpi
        # See https://bugreports.qt.io/browse/QTBUG-65035
        if options.eyecandy and canvas.scene.getDevicePixelRatioF() == 1.0:
            self.shadow = CanvasBoxShadow(self.toGraphicsObject())
            self.shadow.setFakeParent(self)
            self.setGraphicsEffect(self.shadow)

        # Final touches
        self.setFlags(QGraphicsItem.ItemIsFocusable
                      | QGraphicsItem.ItemIsMovable
                      | QGraphicsItem.ItemIsSelectable)

        # Wait for at least 1 port
        if options.auto_hide_groups:
            self.setVisible(False)

        if options.auto_select_items:
            self.setAcceptHoverEvents(True)

        self.updatePositions()

        canvas.scene.addItem(self)
        QTimer.singleShot(0, self.fixPos)

    def getGroupId(self):
        return self.m_group_id

    def getGroupName(self):
        return self.m_group_name

    def isSplitted(self):
        return self.m_splitted

    def getSplittedMode(self):
        return self.m_splitted_mode

    def getPortCount(self):
        return len(self.m_port_list_ids)

    def getPortList(self):
        return self.m_port_list_ids

    def redrawInlineDisplay(self):
        if self.m_plugin_inline == self.INLINE_DISPLAY_CACHED:
            self.m_plugin_inline = self.INLINE_DISPLAY_ENABLED
            self.update()

    def removeAsPlugin(self):
        #del self.m_inline_image
        #self.m_inline_data = None
        #self.m_inline_image = None
        #self.m_inline_scaling = 1.0

        self.m_plugin_id = -1
        self.m_plugin_ui = False
        #self.m_plugin_inline = self.INLINE_DISPLAY_DISABLED

    def setAsPlugin(self, plugin_id, hasUI, hasInlineDisplay):
        if hasInlineDisplay and not options.inline_displays:
            hasInlineDisplay = False

        if not hasInlineDisplay:
            del self.m_inline_image
            self.m_inline_data = None
            self.m_inline_image = None
            self.m_inline_scaling = 1.0

        self.m_plugin_id = plugin_id
        self.m_plugin_ui = hasUI
        self.m_plugin_inline = self.INLINE_DISPLAY_ENABLED if hasInlineDisplay else self.INLINE_DISPLAY_DISABLED
        self.update()

    def setIcon(self, icon_type, icon_name):
        if icon_type == ICON_HARDWARE:
            self.removeIconFromScene()
            port_mode = PORT_MODE_NULL
            if self.m_splitted:
                port_mode = self.m_splitted_mode
            self.top_icon = CanvasSvgIcon(icon_type, icon_name, port_mode, self)
            return
        
        if self.top_icon is not None:
            self.top_icon.setIcon(icon_type, icon_name, self.m_group_name)

    def has_top_icon(self)->bool:
        if self.top_icon is None:
            return False
        
        return not self.top_icon.is_null()

    def setSplit(self, split, mode=PORT_MODE_NULL):
        self.m_splitted = split
        self.m_splitted_mode = mode
        if self._is_hardware:
            self.setIcon(ICON_HARDWARE, self._icon_name)

    def setGroupName(self, group_name):
        self.m_group_name = group_name
        self.updatePositions()

    def setShadowOpacity(self, opacity):
        if self.shadow:
            self.shadow.setOpacity(opacity)

    def addPortFromGroup(self, port_id, port_mode, port_type, 
                         port_name, portgrp_id, is_alternate):
        if len(self.m_port_list_ids) == 0:
            if options.auto_hide_groups:
                if options.eyecandy == EYECANDY_FULL:
                    CanvasItemFX(self, True, False)
                self.setVisible(True)

        new_widget = CanvasPort(self.m_group_id, port_id, port_name, port_mode, 
                                port_type, portgrp_id, is_alternate, self)

        port_dict = port_dict_t()
        port_dict.group_id = self.m_group_id
        port_dict.port_id = port_id
        port_dict.port_name = port_name
        port_dict.port_mode = port_mode
        port_dict.port_type = port_type
        port_dict.portgrp_id = portgrp_id
        port_dict.is_alternate = is_alternate
        port_dict.widget = new_widget

        self.m_port_list_ids.append(port_id)

        return new_widget

    def removePortFromGroup(self, port_id):
        if port_id in self.m_port_list_ids:
            self.m_port_list_ids.remove(port_id)
        else:
            qCritical("PatchCanvas::CanvasBox.removePort(%i) - unable to find port to remove" % port_id)
            return

        if len(self.m_port_list_ids) > 0:
            self.updatePositions()

        elif self.isVisible():
            if options.auto_hide_groups:
                if options.eyecandy == EYECANDY_FULL:
                    CanvasItemFX(self, False, False)
                else:
                    self.setVisible(False)
    
    def addPortGroupFromGroup(self, portgrp_id, port_mode, port_type, port_id_list):
        new_widget = CanvasPortGroup(self.m_group_id, portgrp_id, port_mode, 
                                     port_type, port_id_list, self)
        
        return new_widget
    
    def addLineFromGroup(self, line, connection_id):
        new_cbline = cb_line_t(line, connection_id)
        self.m_connection_lines.append(new_cbline)

    def removeLineFromGroup(self, connection_id):
        for connection in self.m_connection_lines:
            if connection.connection_id == connection_id:
                self.m_connection_lines.remove(connection)
                return
        qCritical("PatchCanvas::CanvasBox.removeLineFromGroup(%i) - unable to find line to remove" % connection_id)

    def checkItemPos(self):
        if not canvas.size_rect.isNull():
            pos = self.scenePos()
            if not (canvas.size_rect.contains(pos) and
                    canvas.size_rect.contains(pos + QPointF(self.p_width, self.p_height))):
                if pos.x() < canvas.size_rect.x():
                    self.setPos(canvas.size_rect.x(), pos.y())
                elif pos.x() + self.p_width > canvas.size_rect.width():
                    self.setPos(canvas.size_rect.width() - self.p_width, pos.y())

                pos = self.scenePos()
                if pos.y() < canvas.size_rect.y():
                    self.setPos(pos.x(), canvas.size_rect.y())
                elif pos.y() + self.p_height > canvas.size_rect.height():
                    self.setPos(pos.x(), canvas.size_rect.height() - self.p_height)

    def removeIconFromScene(self):
        if self.top_icon is None:
            return

        item = self.top_icon
        self.top_icon = None
        canvas.scene.removeItem(item)
        del item

    def get_string_size(self, string: str)->int:
        return QFontMetrics(self.m_font_name).width(string)

    def updatePositions(self):
        self.prepareGeometryChange()

        # Check Text Name size
        box_title, slash, box_subtitle = self.m_group_name.partition('/')
        title_size = self.get_string_size(box_title)
        subtitle_size = self.get_string_size(box_subtitle)
        self.p_width = max(title_size, subtitle_size)
        
        if self.has_top_icon():
            self.p_width += 37
        else:
            self.p_width += 16
        
        self.p_width = max(200 if self.m_plugin_inline != self.INLINE_DISPLAY_DISABLED else 50, self.p_width)

        # Get Port List
        port_list = []
        for port in canvas.port_list:
            if port.group_id == self.m_group_id and port.port_id in self.m_port_list_ids:
                port_list.append(port)

        if len(port_list) == 0:
            self.p_height = canvas.theme.box_header_height
            self.p_width_in = 0
            self.p_width_out = 0
        else:
            max_in_width = max_out_width = 0
            port_spacing = canvas.theme.port_height + canvas.theme.port_spacing

            # Get Max Box Width, vertical ports re-positioning
            port_types = [PORT_TYPE_AUDIO_JACK, PORT_TYPE_MIDI_JACK, PORT_TYPE_MIDI_ALSA, PORT_TYPE_PARAMETER]
            last_in_type = last_out_type = PORT_TYPE_NULL
            last_in_pos = last_out_pos = canvas.theme.box_header_height + canvas.theme.box_header_spacing
            last_of_portgrp = True
            
            for port_type in port_types:
                for port in port_list:
                    if port.port_type != port_type:
                        continue
                    
                    port_pos, pg_len = CanvasGetPortGroupPosition(self.m_group_id,
                                                port.port_id, port.portgrp_id)
                    first_of_portgrp = bool(port_pos == 0)
                    last_of_portgrp = bool(port_pos+1 == pg_len)
                    
                    size = QFontMetrics(self.m_font_port).width(port.port_name)
                    if port.portgrp_id:
                        size = 0
                        totsize = QFontMetrics(self.m_font_port).width(port.port_name) + 3
                        # FIXME
                        for portgrp in canvas.portgrp_list:
                            if portgrp.portgrp_id == port.portgrp_id:
                                portgrp_name = CanvasGetPortGroupName(self.m_group_id, portgrp.port_id_list)
                                size = QFontMetrics(self.m_font_port).width(portgrp_name) + canvas.theme.port_in_portgrp_width
                                break
                        size = max(size, totsize)
                    
                    if port.port_mode == PORT_MODE_INPUT:
                        max_in_width = max(max_in_width, size)
                        if port.port_type != last_in_type:
                            if last_in_type != PORT_TYPE_NULL:
                                last_in_pos += canvas.theme.port_spacingT
                            last_in_type = port.port_type
                        port.widget.setY(last_in_pos)
                        
                        if port.portgrp_id and first_of_portgrp:
                            for portgrp in canvas.portgrp_list:
                                if (portgrp.group_id == self.m_group_id
                                        and portgrp.portgrp_id == port.portgrp_id):
                                    if portgrp.widget:
                                        portgrp.widget.setY(last_in_pos)
                                    break
                        
                        if last_of_portgrp:
                            last_in_pos += port_spacing
                        else:
                            last_in_pos += canvas.theme.port_height

                    elif port.port_mode == PORT_MODE_OUTPUT:
                        max_out_width = max(max_out_width, size)
                        if port.port_type != last_out_type:
                            if last_out_type != PORT_TYPE_NULL:
                                last_out_pos += canvas.theme.port_spacingT
                            last_out_type = port.port_type
                        port.widget.setY(last_out_pos)
                        
                        if port.portgrp_id and first_of_portgrp:
                            for portgrp in canvas.portgrp_list:
                                if (portgrp.group_id == self.m_group_id
                                        and portgrp.portgrp_id == port.portgrp_id):
                                    if portgrp.widget:
                                        portgrp.widget.setY(last_out_pos)
                                    break
                        
                        if last_of_portgrp:
                            last_out_pos += port_spacing
                        else:
                            last_out_pos += canvas.theme.port_height

            self.p_width = max(self.p_width, (100 if self.m_plugin_inline != self.INLINE_DISPLAY_DISABLED else 30) + max_in_width + max_out_width)
            self.p_width_in = max_in_width
            self.p_width_out = max_out_width

            #if self.m_plugin_inline:
                #self.p_width += 10

            # Horizontal ports re-positioning
            inX = canvas.theme.port_offset
            outX = self.p_width - max_out_width - canvas.theme.port_offset - 12
            out_in_portgrpX = self.p_width - canvas.theme.port_offset - 12 - canvas.theme.port_in_portgrp_width
            
            for port_type in port_types:
                for port in port_list:
                    if port.port_mode == PORT_MODE_INPUT:
                        port.widget.setX(inX)
                        if port.portgrp_id:
                            port.widget.setPortWidth(canvas.theme.port_in_portgrp_width)
                            
                            for portgrp in canvas.portgrp_list:
                                if (portgrp.group_id == self.m_group_id
                                        and portgrp.port_id_list
                                        and portgrp.port_id_list[0] == port.port_id):
                                    if portgrp.widget:
                                        portgrp.widget.setPortGroupWidth(max_in_width)
                                        portgrp.widget.setX(canvas.theme.port_offset +1)
                                    break
                            
                        else:
                            port.widget.setPortWidth(max_in_width)

                    elif port.port_mode == PORT_MODE_OUTPUT:
                        if port.portgrp_id:
                            port.widget.setX(out_in_portgrpX)
                            port.widget.setPortWidth(canvas.theme.port_in_portgrp_width)
                            
                            for portgrp in canvas.portgrp_list:
                                if (portgrp.group_id == self.m_group_id
                                        and portgrp.port_id_list
                                        and portgrp.port_id_list[0] == port.port_id):
                                    if portgrp.widget:
                                        portgrp.widget.setX(outX)
                                        portgrp.widget.setPortGroupWidth(max_out_width)
                                    break
                        else:
                            port.widget.setX(outX)
                            port.widget.setPortWidth(max_out_width)

            self.p_height  = max(last_in_pos, last_out_pos)
            self.p_height += max(canvas.theme.port_spacing, canvas.theme.port_spacingT) - canvas.theme.port_spacing
            self.p_height += canvas.theme.box_pen.widthF()

        #if self.m_splitted and self.m_splitted_mode == PORT_MODE_OUTPUT:
            #if self.has_top_icon():
                #self.top_icon.align_right(self.p_width)
        #elif not self.m_splitted:
        if self.has_top_icon():
            self.top_icon.align_at((self.p_width - max(title_size, subtitle_size) - 29)/2)

        self.repaintLines(True)
        self.update()

    def repaintLines(self, forced=False):
        if self.pos() != self.m_last_pos or forced:
            for connection in self.m_connection_lines:
                connection.line.updateLinePos()

        self.m_last_pos = self.pos()

    def resetLinesZValue(self):
        for connection in canvas.connection_list:
            if connection.port_out_id in self.m_port_list_ids and connection.port_in_id in self.m_port_list_ids:
                z_value = canvas.last_z_value
            else:
                z_value = canvas.last_z_value - 1

            connection.widget.setZValue(z_value)

    def type(self):
        return CanvasBoxType

    def contextMenuEvent(self, event):
        event.accept()
        menu = QMenu()

        # Conenct menu stuff
        connMenu = QMenu("Connect", menu)

        our_port_types = []
        our_port_outs = {
            PORT_TYPE_AUDIO_JACK: [],
            PORT_TYPE_MIDI_JACK: [],
            PORT_TYPE_MIDI_ALSA: [],
        }
        for port in canvas.port_list:
            if port.group_id != self.m_group_id:
                continue
            if port.port_mode != PORT_MODE_OUTPUT:
                continue
            if port.port_id not in self.m_port_list_ids:
                continue
            if port.port_type not in our_port_types:
                our_port_types.append(port.port_type)
            our_port_outs[port.port_type].append((port.group_id, port.port_id))

        if len(our_port_types) != 0:
            act_x_conn = None
            for group in canvas.group_list:
                if self.m_group_id == group.group_id:
                    continue

                has_ports = False
                target_ports = {
                    PORT_TYPE_AUDIO_JACK: [],
                    PORT_TYPE_MIDI_JACK: [],
                    PORT_TYPE_MIDI_ALSA: [],
                }

                for port in canvas.port_list:
                    if port.group_id != group.group_id:
                        continue
                    if port.port_mode != PORT_MODE_INPUT:
                        continue
                    if port.port_type not in our_port_types:
                        continue
                    has_ports = True
                    target_ports[port.port_type].append((port.group_id, port.port_id))

                if not has_ports:
                    continue

                act_x_conn = connMenu.addAction(group.group_name)
                act_x_conn.setData((our_port_outs, target_ports))
                act_x_conn.triggered.connect(canvas.qobject.PortContextMenuConnect)

            if act_x_conn is None:
                act_x_disc = connMenu.addAction("Nothing to connect to")
                act_x_disc.setEnabled(False)

        else:
            act_x_disc = connMenu.addAction("No output ports")
            act_x_disc.setEnabled(False)

        # Disconnect menu stuff
        discMenu = QMenu("Disconnect", menu)

        conn_list = []
        conn_list_ids = []

        for port_id in self.m_port_list_ids:
            tmp_conn_list = CanvasGetPortConnectionList(self.m_group_id, port_id)
            for tmp_conn_id, tmp_group_id, tmp_port_id in tmp_conn_list:
                if tmp_conn_id not in conn_list_ids:
                    conn_list.append((tmp_conn_id, tmp_group_id, tmp_port_id))
                    conn_list_ids.append(tmp_conn_id)

        if len(conn_list) > 0:
            for conn_id, group_id, port_id in conn_list:
                act_x_disc = discMenu.addAction(CanvasGetFullPortName(group_id, port_id))
                act_x_disc.setData(conn_id)
                act_x_disc.triggered.connect(canvas.qobject.PortContextMenuDisconnect)
        else:
            act_x_disc = discMenu.addAction("No connections")
            act_x_disc.setEnabled(False)

        menu.addMenu(connMenu)
        menu.addMenu(discMenu)
        act_x_disc_all = menu.addAction("Disconnect &All")
        act_x_sep1 = menu.addSeparator()
        act_x_info = menu.addAction("Info")
        act_x_rename = menu.addAction("Rename")
        act_x_sep2 = menu.addSeparator()
        act_x_split_join = menu.addAction("Join" if self.m_splitted else "Split")

        if not features.group_info:
            act_x_info.setVisible(False)

        if not features.group_rename:
            act_x_rename.setVisible(False)

        if not (features.group_info and features.group_rename):
            act_x_sep1.setVisible(False)

        if self.m_plugin_id >= 0 and self.m_plugin_id <= MAX_PLUGIN_ID_ALLOWED:
            menu.addSeparator()
            act_p_edit = menu.addAction("Edit")
            act_p_ui = menu.addAction("Show Custom UI")
            menu.addSeparator()
            act_p_clone = menu.addAction("Clone")
            act_p_rename = menu.addAction("Rename...")
            act_p_replace = menu.addAction("Replace...")
            act_p_remove = menu.addAction("Remove")

            if not self.m_plugin_ui:
                act_p_ui.setVisible(False)

        else:
            act_p_edit = act_p_ui = None
            act_p_clone = act_p_rename = None
            act_p_replace = act_p_remove = None

        haveIns = haveOuts = False
        for port in canvas.port_list:
            if port.group_id == self.m_group_id and port.port_id in self.m_port_list_ids:
                if port.port_mode == PORT_MODE_INPUT:
                    haveIns = True
                elif port.port_mode == PORT_MODE_OUTPUT:
                    haveOuts = True

        if not (self.m_splitted or bool(haveIns and haveOuts)):
            act_x_sep2.setVisible(False)
            act_x_split_join.setVisible(False)

        act_selected = menu.exec_(event.screenPos())

        if act_selected is None:
            pass

        elif act_selected == act_x_disc_all:
            for conn_id in conn_list_ids:
                canvas.callback(ACTION_PORTS_DISCONNECT, conn_id, 0, "")

        elif act_selected == act_x_info:
            canvas.callback(ACTION_GROUP_INFO, self.m_group_id, 0, "")

        elif act_selected == act_x_rename:
            canvas.callback(ACTION_GROUP_RENAME, self.m_group_id, 0, "")

        elif act_selected == act_x_split_join:
            if self.m_splitted:
                canvas.callback(ACTION_GROUP_JOIN, self.m_group_id, 0, "")
            else:
                canvas.callback(ACTION_GROUP_SPLIT, self.m_group_id, 0, "")

        elif act_selected == act_p_edit:
            canvas.callback(ACTION_PLUGIN_EDIT, self.m_plugin_id, 0, "")

        elif act_selected == act_p_ui:
            canvas.callback(ACTION_PLUGIN_SHOW_UI, self.m_plugin_id, 0, "")

        elif act_selected == act_p_clone:
            canvas.callback(ACTION_PLUGIN_CLONE, self.m_plugin_id, 0, "")

        elif act_selected == act_p_rename:
            canvas.callback(ACTION_PLUGIN_RENAME, self.m_plugin_id, 0, "")

        elif act_selected == act_p_replace:
            canvas.callback(ACTION_PLUGIN_REPLACE, self.m_plugin_id, 0, "")

        elif act_selected == act_p_remove:
            canvas.callback(ACTION_PLUGIN_REMOVE, self.m_plugin_id, 0, "")

    def keyPressEvent(self, event):
        if self.m_plugin_id >= 0 and event.key() == Qt.Key_Delete:
            event.accept()
            canvas.callback(ACTION_PLUGIN_REMOVE, self.m_plugin_id, 0, "")
            return
        QGraphicsItem.keyPressEvent(self, event)

    def hoverEnterEvent(self, event):
        if options.auto_select_items:
            if len(canvas.scene.selectedItems()) > 0:
                canvas.scene.clearSelection()
            self.setSelected(True)
        QGraphicsItem.hoverEnterEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        if self.m_plugin_id >= 0:
            event.accept()
            canvas.callback(ACTION_PLUGIN_SHOW_UI if self.m_plugin_ui else ACTION_PLUGIN_EDIT, self.m_plugin_id, 0, "")
            return

        QGraphicsItem.mouseDoubleClickEvent(self, event)

    def mousePressEvent(self, event):
        canvas.last_z_value += 1
        self.setZValue(canvas.last_z_value)
        self.resetLinesZValue()
        self.m_cursor_moving = False

        if event.button() == Qt.RightButton:
            event.accept()
            canvas.scene.clearSelection()
            self.setSelected(True)
            self.m_mouse_down = False
            return

        elif event.button() == Qt.LeftButton:
            if self.sceneBoundingRect().contains(event.scenePos()):
                self.m_mouse_down = True
            else:
                # FIXME: Check if still valid: Fix a weird Qt behaviour with right-click mouseMove
                self.m_mouse_down = False
                event.ignore()
                return

        else:
            self.m_mouse_down = False

        QGraphicsItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.m_mouse_down:
            if not self.m_cursor_moving:
                self.setCursor(QCursor(Qt.SizeAllCursor))
                self.m_cursor_moving = True
            self.repaintLines()
        QGraphicsItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.m_cursor_moving:
            self.unsetCursor()
            QTimer.singleShot(0, self.fixPosAfterMove)
        self.m_mouse_down = False
        self.m_cursor_moving = False
        QGraphicsItem.mouseReleaseEvent(self, event)

    def fixPos(self):
        self.setX(round(self.x()))
        self.setY(round(self.y()))

    def fixPosAfterMove(self):
        self.fixPos()
        
        in_or_out = 3
        if self.m_splitted:
            in_or_out = self.m_splitted_mode
        
        x_y_str = "%i:%i" % (round(self.x()), round(self.y()))
        
        CanvasCallback(ACTION_GROUP_MOVE, self.m_group_id, in_or_out, x_y_str)
        
    def boundingRect(self):
        if self._is_hardware:
            return QRectF(-9, -9, self.p_width + 9, self.p_height + 9)
        return QRectF(0, 0, self.p_width, self.p_height)

    def paint(self, painter, option, widget):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, bool(options.antialiasing == ANTIALIASING_FULL))
        
        # Draw rectangle
        pen = QPen(canvas.theme.box_pen_sel if self.isSelected() else canvas.theme.box_pen)
        pen.setWidthF(pen.widthF() + 0.00001)
        painter.setPen(pen)
        lineHinting = pen.widthF() / 2
        
        if self._is_hardware:
            d = 9
            hw_gradient = QLinearGradient(-d, -d, self.p_width +d, self.p_height +d)
            hw_gradient.setColorAt(0, QColor(70, 70, 50))
            hw_gradient.setColorAt(1, QColor(50, 50, 30))
            painter.setBrush(hw_gradient)
            painter.setPen(QPen(QColor(30, 30, 30), 1))
            if self.m_splitted:
                hardware_poly = QPolygonF()
                    
                if self.m_splitted_mode == PORT_MODE_INPUT:
                    hardware_poly += QPointF(- lineHinting, - lineHinting)
                    hardware_poly += QPointF(- lineHinting, 34)
                    hardware_poly += QPointF(-d /2.0, 34)
                    hardware_poly += QPointF(-d, 34 - d / 2.0)
                    hardware_poly += QPointF(-d, -d / 2.0)
                    hardware_poly += QPointF(-d / 2.0, -d)
                    hardware_poly += QPointF(self.p_width + d/2.0, -d)
                    hardware_poly += QPointF(self.p_width + d, -d / 2.0)
                    hardware_poly += QPointF(self.p_width + d, self.p_height + d/2.0)
                    hardware_poly += QPointF(self.p_width + d/2.0, self.p_height + d)
                    hardware_poly += QPointF(-d/2.0, self.p_height +d)
                    hardware_poly += QPointF(-d, self.p_height +d/2.0)
                    hardware_poly += QPointF(-d, self.p_height -3 + d/2.0)
                    hardware_poly += QPointF(-d/2.0, self.p_height -3)
                    hardware_poly += QPointF(- lineHinting, self.p_height -3)
                    hardware_poly += QPointF(- lineHinting, self.p_height + lineHinting)
                    hardware_poly += QPointF(self.p_width + lineHinting, self.p_height + lineHinting)
                    hardware_poly += QPointF(self.p_width + lineHinting, - lineHinting)
                else:
                    hardware_poly += QPointF(self.p_width + lineHinting, - lineHinting)
                    hardware_poly += QPointF(self.p_width + lineHinting, 34)
                    hardware_poly += QPointF(self.p_width + d/2.0, 34)
                    hardware_poly += QPointF(self.p_width + d, 34 - d/2.0)
                    hardware_poly += QPointF(self.p_width +d, -d / 2.0)
                    hardware_poly += QPointF(self.p_width + d/2.0, -d)
                    hardware_poly += QPointF(-d / 2.0, -d)
                    hardware_poly += QPointF(-d, -d/2.0)
                    hardware_poly += QPointF(-d, self.p_height + d/2.0)
                    hardware_poly += QPointF(-d/2.0, self.p_height + d)
                    hardware_poly += QPointF(self.p_width + d/2.0, self.p_height + d)
                    hardware_poly += QPointF(self.p_width + d, self.p_height + d/2.0)
                    hardware_poly += QPointF(self.p_width +d, self.p_height -3 + d/2.0)
                    hardware_poly += QPointF(self.p_width + d/2, self.p_height -3)
                    hardware_poly += QPointF(self.p_width + lineHinting, self.p_height -3)
                    hardware_poly += QPointF(self.p_width + lineHinting, self.p_height + lineHinting)
                    hardware_poly += QPointF(-lineHinting, self.p_height + lineHinting)
                    hardware_poly += QPointF(-lineHinting, -lineHinting)
                    
                painter.drawPolygon(hardware_poly)
            else:
                hw_poly_top = QPolygonF()
                hw_poly_top += QPointF(-lineHinting, -lineHinting)
                hw_poly_top += QPointF(-lineHinting, 34)
                hw_poly_top += QPointF(-d /2.0, 34)
                hw_poly_top += QPointF(-d, 34 - d / 2.0)
                hw_poly_top += QPointF(-d, -d / 2.0)
                hw_poly_top += QPointF(-d / 2.0, -d)
                hw_poly_top += QPointF(self.p_width + d/2.0, -d)
                hw_poly_top += QPointF(self.p_width + d, -d / 2.0)
                hw_poly_top += QPointF(self.p_width + d, 34 - d/2)
                hw_poly_top += QPointF(self.p_width+ d/2, 34)
                hw_poly_top += QPointF(self.p_width + lineHinting, 34)
                hw_poly_top += QPointF(self.p_width + lineHinting, -lineHinting)
                painter.drawPolygon(hw_poly_top)
                
                hw_poly_bt = QPolygonF()
                hw_poly_bt += QPointF(-lineHinting, self.p_height + lineHinting)
                hw_poly_bt += QPointF(-lineHinting, self.p_height -3)
                hw_poly_bt += QPointF(-d/2, self.p_height -3)
                hw_poly_bt += QPointF(-d, self.p_height -3 + d/2)
                hw_poly_bt += QPointF(-d, self.p_height + d/2)
                hw_poly_bt += QPointF(-d/2, self.p_height + d)
                hw_poly_bt += QPointF(self.p_width + d/2, self.p_height + d)
                hw_poly_bt += QPointF(self.p_width +d, self.p_height + d/2)
                hw_poly_bt += QPointF(self.p_width +d, self.p_height -3 + d/2)
                hw_poly_bt += QPointF(self.p_width +d/2, self.p_height -3)
                hw_poly_bt += QPointF(self.p_width + lineHinting, self.p_height -3)
                hw_poly_bt += QPointF(self.p_width + lineHinting, self.p_height + lineHinting)
                painter.drawPolygon(hw_poly_bt)
                    
            pen = QPen(canvas.theme.box_pen_sel if self.isSelected() else canvas.theme.box_pen)
            pen.setWidthF(pen.widthF() + 0.00001)
            painter.setPen(pen)
        
        rect = QRectF(0, 0, self.p_width, self.p_height)

        if canvas.theme.box_bg_type == Theme.THEME_BG_GRADIENT:
            box_gradient = QLinearGradient(0, 0, 0, self.p_height)
            box_gradient.setColorAt(0, canvas.theme.box_bg_1)
            box_gradient.setColorAt(1, canvas.theme.box_bg_2)
            painter.setBrush(box_gradient)
        else:
            painter.setBrush(canvas.theme.box_bg_1)

        rect.adjust(lineHinting, lineHinting, -lineHinting, -lineHinting)
        painter.drawRect(rect)

        # Draw plugin inline display if supported
        self.paintInlineDisplay(painter)

        # Draw pixmap header
        rect.setHeight(canvas.theme.box_header_height)
        if canvas.theme.box_header_pixmap:
            painter.setPen(Qt.NoPen)
            painter.setBrush(canvas.theme.box_bg_2)

            # outline
            rect.adjust(lineHinting, lineHinting, -lineHinting, -lineHinting)
            painter.drawRect(rect)

            rect.adjust(1, 1, -1, 0)
            painter.drawTiledPixmap(rect, canvas.theme.box_header_pixmap, rect.topLeft())

        # Draw text
        

        #if canvas.theme.box_use_icon:
            #textPos = QPointF(33, canvas.theme.box_text_ypos)
        #else:
            #appNameSize = QFontMetrics(self.m_font_name).width(self.m_group_name)
            #rem = self.p_width - appNameSize
            #textPos = QPointF(rem/2, canvas.theme.box_text_ypos)

        title_x_pos = 8
        if self.has_top_icon():
            title_x_pos += 25
        
        subtitle_x_pos = title_x_pos
        
        title_y_pos = canvas.theme.box_text_ypos

        box_title = self.m_group_name
        box_subtitle = ''
        if '/' in box_title:
            box_title, slash, box_subtitle = self.m_group_name.partition('/')

        title_size = self.get_string_size(box_title)
        subtitle_size = self.get_string_size(box_subtitle)

        painter.setPen(QPen(QColor(255, 192, 0, 80), 1))

        #if self.m_splitted:
            #if self.m_splitted_mode == PORT_MODE_OUTPUT:
                #title_x_pos = self.p_width - 8 - title_size
                #subtitle_x_pos = self.p_width - 8 - subtitle_size

                #if self.has_top_icon():
                    #title_x_pos -= 25
                    #subtitle_x_pos -= 25
                
                #if min(title_x_pos, subtitle_x_pos) > 10:
                    #painter.drawLine(5, 16, min(title_x_pos, subtitle_x_pos) - 5, 16)
        #else:
        if self.has_top_icon():
            title_x_pos = 29 + (self.p_width - 29 - max(title_size, subtitle_size)) / 2
            subtitle_x_pos = title_x_pos
            
            if title_x_pos > 43:
                painter.drawLine(5, 16, title_x_pos -29 -5, 16)
                painter.drawLine(
                    title_x_pos + max(title_size, subtitle_size) + 5, 16,
                    self.p_width -5, 16)
            
        else:
            title_x_pos = (self.p_width - title_size) / 2
            subtitle_x_pos = (self.p_width - subtitle_size) / 2
            if min(title_x_pos, subtitle_x_pos) > 10:
                painter.drawLine(5, 16, min(title_x_pos, subtitle_x_pos) - 5, 16)
                painter.drawLine(
                    max(title_x_pos + title_size, subtitle_x_pos + subtitle_size) + 5, 16,
                    self.p_width - 5, 16)

        painter.setFont(self.m_font_name)

        if self.isSelected():
            painter.setPen(canvas.theme.box_text_sel)
        else:
            painter.setPen(canvas.theme.box_text)

        if box_subtitle:
            painter.drawText(
                QPointF(title_x_pos, title_y_pos -6), box_title)
            painter.drawText(
                QPointF(subtitle_x_pos, title_y_pos +9), box_subtitle)
        else:
            painter.drawText(
                QPointF(title_x_pos, title_y_pos), self.m_group_name)

        self.repaintLines()

        painter.restore()

    def paintInlineDisplay(self, painter):
        if self.m_plugin_inline == self.INLINE_DISPLAY_DISABLED:
            return
        if not options.inline_displays:
            return

        inwidth  = self.p_width - self.p_width_in - self.p_width_out - 16
        inheight = self.p_height - canvas.theme.box_header_height - canvas.theme.box_header_spacing - canvas.theme.port_spacing - 3
        scaling  = canvas.scene.getScaleFactor() * canvas.scene.getDevicePixelRatioF()

        if self.m_plugin_id >= 0 and self.m_plugin_id <= MAX_PLUGIN_ID_ALLOWED and (
           self.m_plugin_inline == self.INLINE_DISPLAY_ENABLED or self.m_inline_scaling != scaling):
            size = "%i:%i" % (int(inwidth*scaling), int(inheight*scaling))
            data = canvas.callback(ACTION_INLINE_DISPLAY, self.m_plugin_id, 0, size)
            if data is None:
                return

            # invalidate old image first
            del self.m_inline_image

            self.m_inline_data = pack("%iB" % (data['height'] * data['stride']), *data['data'])
            self.m_inline_image = QImage(voidptr(self.m_inline_data), data['width'], data['height'], data['stride'], QImage.Format_ARGB32)
            self.m_inline_scaling = scaling
            self.m_plugin_inline = self.INLINE_DISPLAY_CACHED

        if self.m_inline_image is None:
            print("ERROR: inline display image is None for", self.m_plugin_id, self.m_group_name)
            return

        swidth = self.m_inline_image.width() / scaling
        sheight = self.m_inline_image.height() / scaling

        srcx = int(self.p_width_in + (self.p_width - self.p_width_in - self.p_width_out) / 2 - swidth / 2)
        srcy = int(canvas.theme.box_header_height + canvas.theme.box_header_spacing + 1 + (inheight - sheight) / 2)

        painter.drawImage(QRectF(srcx, srcy, swidth, sheight), self.m_inline_image)

# ------------------------------------------------------------------------------------------------------------