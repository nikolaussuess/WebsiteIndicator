#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pprint
import shutil
import webbrowser
from typing import Optional, TypeVar, List

import gi
import xmltodict
import xml.etree.ElementTree as ET

from config import config

gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk as gtk
from gi.repository import Pango
from gi.repository import GdkPixbuf as pixbuf

T = TypeVar('T')


class Database:
    """
    Stores the data (menu entries) and is able to convert it to e.g. Gtk menu entries, ...
    """

    class Item:
        """
        A menu item.
        """
        """
        Gtk Menu separator.
        """
        TYPE_SEPARATOR='separator'
        """
        Web browser. Will be opened using webbrowser.open(action).
        """
        TYPE_WEB='www'
        """
        The top-level entry or a submenu.
        """
        TYPE_MENU = "menu"

        TYPES = [TYPE_SEPARATOR, TYPE_WEB, TYPE_MENU]
        """
        Each menu item has a unique ID. This static variable holds the current maximum ID.
        """
        GLOBAL_ID = 0

        def __init__(self : T, text : str = '', action : Optional[str] = None, type : str = TYPE_WEB, icon : Optional[str] = None):
            """

            :param text: The label / menu entry text.
            :param action: The action can be, e.g., the URL of the website in case of www.
            :param type: One of Database.Item.TYPES (e.g., wwww for a website).
            :param icon: Relative path to an icon.
            """
            self.text = text
            self.action = action
            self.type = type
            self.children : List[T] = []
            self.icon = icon
            Database.Item.GLOBAL_ID = Database.Item.GLOBAL_ID + 1
            self.global_id = Database.Item.GLOBAL_ID

        def set_text(self, new_text : str) -> None:
            self.text = new_text

        def set_action(self, new_action : Optional[str]) -> None:
            self.action = new_action

        def set_type(self, new_type : str) -> None:
            self.type = new_type

        def set_icon(self, new_icon : Optional[str]) -> None:
            self.icon = new_icon

        def add_child(self : T, child : T) -> None:
            self.children.append(child)

        def get_children(self : T) -> List[T]:
            return self.children

        def __str__(self) -> str:
            return "[text="+str(self.text)+", action("+str(self.type)+")="+str(self.action)+", children="+\
                ', '.join(map(lambda s:str(s), self.children))+"]"

        def has_submenus(self) -> bool:
            return any(x for x in self.children if x.type == Database.Item.TYPE_MENU)

    def __init__(self, filename : str):
        super()
        self.filename : str = filename
        self.data : Database.Item = Database.Item()

    def parse_file(self) -> bool:
        """
        Read the entries / data from an XML file.
        :return: False if the file was empty and the menu was newly created, True otherwise
        """
        with open(self.filename) as fd:
            contents = fd.read()
            # File is empty
            if not contents.strip(" "):
                self.data = Database.Item(type=Database.Item.TYPE_MENU)
                self.data.set_text("Menu")
                return False
            doc = xmltodict.parse(contents)
            xml_menu = doc['menu']
        self.data = self._parse_file_recursive(xml_menu)
        print(self.data)
        return True

    def _parse_file_recursive(self, xml_menu : dict) -> Item:
        menu = Database.Item(type=Database.Item.TYPE_MENU)
        for key, value in xml_menu.items():
            if key == '@name':
                menu.set_text(value)
            elif key == 'item':
                if not isinstance(value, list):
                    value = [value]
                for item in value:
                    dbitem = Database.Item()
                    item_key = ''
                    for item_key, item_value in item.items():
                        if item_key == 'text':
                            dbitem.set_text(item_value)
                        elif item_key == 'action':
                            for action_key, action_value in item_value.items():
                                if action_key == '#text':
                                    dbitem.set_action(action_value)
                                elif action_key == '@type':
                                    dbitem.set_type(action_value)
                        elif item_key == 'icon':
                            dbitem.set_icon(item_value)
                        elif item_key == 'separator':
                            menu.add_child(Database.Item(type=Database.Item.TYPE_SEPARATOR))
                            break
                    if item_key != 'separator':
                        menu.add_child(dbitem)
            elif key == 'menu':
                if not isinstance(value, list):
                    value = [value]
                for item in value:
                    menu.add_child(self._parse_file_recursive(item))

        return menu

    def save_data(self) -> None:
        """
        Writes the current data to the XML file.

        Note, that this function saves the old file (as "filename~") to avoid data loss.
        This could perhaps be improved (e.g., keep more versions) ...
        :return: Nothing
        """
        data = ET.Element("menu")
        data.set("name", self.data.text)
        self._save_data_recursive(self.data, data)
        ET.indent(data, space=" ", level=0)

        # Make a copy of the file to not loose content just in case
        shutil.copy(self.filename, self.filename + "~")

        with open(self.filename, "wb") as f:
            f.write(ET.tostring(data))

    def _save_data_recursive(self, parent : Item, parent_tag : ET.Element):
        for item in parent.get_children():
            if item.type == Database.Item.TYPE_MENU:
                element = ET.SubElement(parent_tag, 'menu')
                element.set('name', item.text)
                if item.icon is not None:
                    ET.SubElement(element, 'icon').text = item.icon
                self._save_data_recursive(item, element)
            elif item.type == Database.Item.TYPE_WEB:
                element = ET.SubElement(parent_tag, 'item')
                ET.SubElement(element, 'text').text = item.text
                if item.icon is not None:
                    ET.SubElement(element, 'icon').text = item.icon
                se = ET.SubElement(element, 'action')
                se.text = item.action
                se.set('type', 'www')
            elif item.type == Database.Item.TYPE_SEPARATOR:
                element = ET.SubElement(parent_tag, 'item')
                ET.SubElement(element, 'separator')

    def to_gtk_menu(self, data : Optional[Item] = None) -> gtk.Menu:
        """
        Exports the data as a Gtk menu.
        :param data: The menu to start with. If not given, self.data is used.
        :return: The Gtk menu containing all (sub)entries of data or self.data.
        """
        if data is None:
            data = self.data

        gtk_menu = gtk.Menu()
        for item in data.get_children():
            if item.type == Database.Item.TYPE_WEB:

                if item.icon is not None:

                    pb = pixbuf.Pixbuf.new_from_file(
                        os.path.join(os.path.join(config['general']['image_dir'], item.icon)))
                    pb = pb.scale_simple(25, 25, pixbuf.InterpType.BILINEAR)
                    img = gtk.Image()
                    img.set_from_pixbuf(pb)
                    gtk_menu_item = gtk.ImageMenuItem(item.text)
                    gtk_menu_item.set_image(img)
                    gtk_menu_item.set_always_show_image(True)
                else:
                    gtk_menu_item = gtk.MenuItem(item.text)
                gtk_menu_item.connect('activate', lambda source, action=item.action: webbrowser.open(action))
                gtk_menu.append(gtk_menu_item)

            elif item.type == Database.Item.TYPE_SEPARATOR:
                gtk_menu.append(gtk.SeparatorMenuItem())

            elif item.type == Database.Item.TYPE_MENU:
                submenu = self.to_gtk_menu(item)
                if item.icon is not None:
                    pb = pixbuf.Pixbuf.new_from_file(
                        os.path.join(os.path.join(config['general']['image_dir'], item.icon)))
                    pb = pb.scale_simple(25, 25, pixbuf.InterpType.BILINEAR)
                    img = gtk.Image()
                    img.set_from_pixbuf(pb)
                    submenu_item = gtk.ImageMenuItem(item.text)
                    submenu_item.set_image(img)
                    submenu_item.set_always_show_image(True)
                else:
                    submenu_item = gtk.MenuItem(item.text)
                submenu_item.set_submenu(submenu)
                gtk_menu.append(submenu_item)
        return gtk_menu

    def get_menu_hierarchy(self) -> gtk.TreeStore:
        """
        Exports all submenus (without entries) as TreeStore.
        This is used, e.g., for the form where you can choose where to add the bookmark.
        The treestore contains (0) the text (str) and (1) the global id (int).
        :return: Treestore containing all menus.
        """
        treestore = gtk.TreeStore.new(types=[str,int])
        toplevel = treestore.append(None)
        treestore.set_value(toplevel, 0, self.data.text)
        treestore.set_value(toplevel, 1, self.data.global_id)
        self._get_menu_hierarchy_recursive(self.data, treestore, toplevel)
        return treestore

    def _get_menu_hierarchy_recursive(self, parent_entry : Item, treestore : gtk.TreeStore, parent_level : gtk.TreeIter) -> None:
        for menu_entry in parent_entry.get_children():
            if menu_entry.type != Database.Item.TYPE_MENU:
                continue
            newlevel = treestore.append(parent_level)
            treestore.set_value(newlevel, 0, menu_entry.text)
            treestore.set_value(newlevel, 1, menu_entry.global_id)
            if menu_entry.has_submenus():
                self._get_menu_hierarchy_recursive(menu_entry, treestore, newlevel)

    def get_item_hierarchy(self) -> gtk.TreeStore:
        """
        Exports all entries as TreeStore. It is used for filtering.
        The structure is:
        (1) str:            label/text
        (2) str:            item type (www/menu/...)
        (3) str:            action
        (4) bool:           always true on return; can be used to hide some elements in the view
        (5) Pango.Weight:   not set on return; can be used to print some entries bold
        (6) int:            global ID
        :return: Menu entries
        """
        treestore = gtk.TreeStore.new(types=[str, str, str, bool, Pango.Weight, int])
        toplevel : gtk.TreeIter = treestore.append(None)
        treestore.set_value(toplevel, 0, self.data.text)
        if self.data.type is not None:
            treestore.set_value(toplevel, 1, self.data.type)
        if self.data.action is not None:
            treestore.set_value(toplevel, 2, self.data.action)
        treestore.set_value(toplevel, 3, True)
        treestore.set_value(toplevel, 5, self.data.global_id)
        self._get_item_hierarchy_recursive(self.data, treestore, toplevel)
        return treestore

    def _get_item_hierarchy_recursive(self, parent_entry : Item, treestore : gtk.TreeStore, parent_level : gtk.TreeIter) -> None:
        for menu_entry in parent_entry.get_children():
            if menu_entry.type == Database.Item.TYPE_SEPARATOR:
                continue
            newlevel = treestore.append(parent_level)
            treestore.set_value(newlevel, 0, menu_entry.text)
            if menu_entry.type is not None:
                treestore.set_value(newlevel, 1, menu_entry.type)
            if menu_entry.action is not None:
                treestore.set_value(newlevel, 2, menu_entry.action)
            treestore.set_value(newlevel, 3, True)
            treestore.set_value(newlevel, 5, menu_entry.global_id)
            self._get_item_hierarchy_recursive(menu_entry, treestore, newlevel)

    def add_item(self, parent_id : int, item : Item) -> bool:
        """
        Add a new entry.
        :param parent_id: The id of the parent item. The item is appended as a child element.
        :param item: Item to add.
        :return: True when the item could be added, False otherwise (e.g., the parent item does not exist)
        """
        return self._add_item_recursive(parent_id, item, self.data)

    def _add_item_recursive(self, parent_id : int, item : Item, data : Item) -> bool:
        if data.global_id == parent_id:
            data.add_child(item)
            return True

        for child in data.get_children():
            if self._add_item_recursive(parent_id, item, child):
                return True
        return False

    def delete_item_by_id(self, id : int) -> bool:
        """
        Delete an entry by ID
        :param id: The id of the item to be deleted.
        :return: True when the item could be deleted, False otherwise (e.g., the item does not exist)
        """
        return self._delete_item_recursive(id, self.data)

    def _delete_item_recursive(self, id : int, data : Item) -> bool:
        found = False
        idx = 0
        for idx in range(len(data.get_children())):
            if data.get_children()[idx].global_id == id:
                found = True
                break
            if self._delete_item_recursive(id, data.get_children()[idx]):
                return True

        if found:
            del data.get_children()[idx]
            return True
        else:
            return False

    def __str__(self) -> str:
        return pprint.pformat(self.data)
