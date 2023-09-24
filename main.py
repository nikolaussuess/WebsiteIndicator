#!/usr/bin/env python
# -*- coding: utf-8 -*-
# this is an indicator
from typing import Optional

import gi

import newentry

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk

# gi.require_version('AppIndicator3', '0.1')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import AyatanaAppIndicator3 as appindicator
# from gi.repository import AppIndicator3 as appindicator
import signal
import os

from searchwindow import SearchWindow
from newentry import NewEntryWindow
from model import Database


APPINDICATOR_ID = 'lesezeichen'


def quit(source = None) -> None:
    """
    Quit the whole program.
    :param source: Source widget, if called via a button click. Currently not used.
    :return: Nothing
    """
    gtk.main_quit()


def create_menu(indicator : appindicator.Indicator, database : Optional[Database] = None) -> None:
    """
    Create the menu for the indicator and sets it.
    :param indicator: Gtk indicator (AyatanaAppIndicator3 or AppIndicator3).
    :param database: Data to be displayed in the menu, if already available.
    :return: Nothing
    """
    # At first call, when the input file has not been read, read the file.
    # If we, on the other hand, already have read the data, use it from the parameter.
    if database is None:
        try:
            database = Database("lesezeichen.xml")
            database.parse_file()
        except Exception as e:
            # File not found, not access rights etc.
            parent = None
            md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                                   gtk.ButtonsType.CLOSE, "Error parsing XML file.\n" + str(e))
            md.run()
            md.destroy()
            return

    menu = database.to_gtk_menu()
    menu.append(gtk.SeparatorMenuItem())

    # Add default entries
    img = gtk.Image()
    img.set_from_file(os.path.dirname(os.path.realpath(__file__)) + '/logos/search.png')
    item = gtk.ImageMenuItem('Search')
    item.set_image(img)
    item.set_always_show_image(True)
    item.connect('activate', lambda source: show_search_window(database))
    menu.append(item)

    img = gtk.Image()
    img.set_from_file(os.path.dirname(os.path.realpath(__file__)) + '/logos/reload.png')
    item = gtk.ImageMenuItem('Reload file')
    item.set_image(img)
    item.set_always_show_image(True)
    item.connect('activate', lambda source: create_menu(indicator))
    menu.append(item)

    img = gtk.Image()
    img.set_from_file(os.path.dirname(os.path.realpath(__file__)) + '/logos/add.png')
    item = gtk.ImageMenuItem('New entry')
    item.set_image(img)
    item.set_always_show_image(True)
    item.connect('activate', lambda source: add_new_entry_window(indicator, database))
    menu.append(item)

    # Quit-Button
    img = gtk.Image()
    img.set_from_file(os.path.dirname(os.path.realpath(__file__)) + '/logos/quit.png')
    item = gtk.ImageMenuItem('Beenden')
    item.set_image(img)
    item.set_always_show_image(True)
    item.connect('activate', quit)
    menu.append(item)

    menu.show_all()

    indicator.set_menu(menu)


def add_new_entry_window(indicator : appindicator.Indicator, database : Database):
    """
    Open the window to add a new entry.
    :param indicator: Reference to indicator, in order to update the entries there.
    :param database: Data to be displayed in the menu.
    :return: Nothing
    """
    window = NewEntryWindow(database)
    window.connect('destroy', lambda source: create_menu(indicator, database))
    window.show_all()


def show_search_window(database : Database) -> None:
    """
    Open the window to search / filter for an entry.
    :param database: Data to be displayed in the menu.
    :return: Nothing
    """
    window = SearchWindow(database)
    window.show_all()


if __name__ == "__main__":
    # Create indicator
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    indicator = appindicator.Indicator.new(APPINDICATOR_ID, os.path.abspath(
        os.path.dirname(os.path.realpath(__file__)) + '/logos/lesezeichen.jpg'),
                                           appindicator.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

    create_menu(indicator)

    gtk.main()
