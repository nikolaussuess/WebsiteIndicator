#!/usr/bin/env python
# -*- coding: utf-8 -*-
# this is an indicator
import argparse
from typing import Optional

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk

# gi.require_version('AppIndicator3', '0.1')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import AyatanaAppIndicator3 as appindicator
# from gi.repository import AppIndicator3 as appindicator
import signal
import sys

from searchwindow import SearchWindow
from newentry import NewEntryWindow
from model import Database
from config import *


APPINDICATOR_ID = 'lesezeichen'


def quit(source = None) -> None:
    """
    Quit the whole program.
    :param source: Source widget, if called via a button click. Currently not used.
    :return: Nothing
    """
    gtk.main_quit()


def create_database() -> Database:
    """
    Read the (database) file and return a database object.
    :return: database containing the bookmark entries
    """
    try:
        database = Database(config['general']['file_path'])

        # If bookmark database file does not exist, ask whether it should be created or not.
        # If the user chooses "yes", then an empty file is created (could be improved later ...).
        if not os.path.isfile(config['general']['file_path']):
            # FIXME: If parent is none, the message dialog is shown in background ...
            # This is why a temporary window is created ... but a better solution should be found ...
            parent = gtk.Window()
            parent.set_default_size(0, 0)
            parent.show()
            dialog = gtk.MessageDialog(parent, gtk.DialogFlags.MODAL,
                                       gtk.MessageType.QUESTION, gtk.ButtonsType.YES_NO)
            dialog.set_title("Bookmark file does not exist")
            dialog.set_markup("File '" + config['general']['file_path'] + "' does not exist. " +
                              "Create it?\n\nNote: If you choose 'No', the program is quited.")
            dialog.set_icon_name("dialog-question")
            response = dialog.run()
            dialog.destroy()
            if response == gtk.ResponseType.YES:
                with open(config['general']['file_path'], 'w') as fp:
                    pass
                parent.destroy()
            else:
                parent.destroy()
                quit()
                exit(0)

        # If the file was empty, ask how to proceed.
        if not database.parse_file():
            # FIXME: If parent is none, the message dialog is shown in background ...
            # This is why a temporary window is created ... but a better solution should be found ...
            parent = gtk.Window()
            parent.set_default_size(0, 0)
            parent.show()
            dialog = gtk.MessageDialog(parent, gtk.DialogFlags.MODAL,
                                       gtk.MessageType.QUESTION, gtk.ButtonsType.YES_NO)
            dialog.set_title("Bookmark file empty")
            dialog.set_markup("File '" + config['general']['file_path'] + "' was empty. " +
                                   "Hence, a new menu was created. If this is an error and there should be an existing "
                                   "database file, please check the config file '"+str(config['dir'])+"/config.yml'.\n"
                                   "Do you want to proceed?")
            dialog.set_icon_name("dialog-question")
            response = dialog.run()
            dialog.destroy()
            if response != gtk.ResponseType.YES:
                parent.destroy()
                quit()
                exit(0)
            else:
                parent.destroy()
    except Exception as e:
        # File not found, not access rights etc.
        print("Exception: ",str(e))
        # FIXME: If parent is none, the message dialog is shown in background ...
        # This is why a temporary window is created ... but a better solution should be found ...
        parent = gtk.Window()
        parent.set_default_size(0,0)
        parent.show()
        md = gtk.MessageDialog(parent, gtk.DialogFlags.MODAL, gtk.MessageType.ERROR,
                               gtk.ButtonsType.CLOSE)
        md.set_title("Error parsing XML file")
        md.set_markup("Error parsing XML file '"+config['general']['file_path']+"':\n" + str(e))
        md.run()
        md.destroy()
        exit(1)
    return database


def create_menu(indicator : Optional[appindicator.Indicator], database : Optional[Database] = None) -> None:
    """
    Create the menu for the indicator and sets it.
    :param indicator: Gtk indicator (AyatanaAppIndicator3 or AppIndicator3).
    :param database: Data to be displayed in the menu, if already available.
    :return: Nothing
    """
    # At first call, when the input file has not been read, read the file.
    # If we, on the other hand, already have read the data, use it from the parameter.
    if database is None:
        database = create_database()
    # If the search window was started using --search, then create_menu is called with indicator=None.
    # We do not have to create a new menu and can return.
    if indicator is None:
        return

    menu = database.to_gtk_menu()
    menu.append(gtk.SeparatorMenuItem())

    # Add default entries
    item = gtk.ImageMenuItem('Search')
    img = gtk.Image.new_from_icon_name("search", gtk.IconSize.MENU)
    item.set_image(img)
    item.set_always_show_image(True)
    item.connect('activate', lambda source: show_search_window(indicator, database))
    menu.append(item)

    img = gtk.Image()
    img.set_from_file(os.path.join(config['script_dir'], 'default_images', 'reload.png'))
    item = gtk.ImageMenuItem('Reload file')
    item.set_image(img)
    item.set_always_show_image(True)
    item.connect('activate', lambda source: create_menu(indicator))
    menu.append(item)

    img = gtk.Image()
    img.set_from_file(os.path.join(config['script_dir'], 'default_images', 'add.png'))
    item = gtk.ImageMenuItem('New entry')
    item.set_image(img)
    item.set_always_show_image(True)
    item.connect('activate', lambda source: add_new_entry_window(indicator, database))
    menu.append(item)

    # Quit-Button
    item = gtk.ImageMenuItem('Beenden')
    img = gtk.Image.new_from_icon_name("window-close", gtk.IconSize.MENU)
    item.set_image(img)
    item.set_always_show_image(True)
    item.connect('activate', quit)
    menu.append(item)

    menu.show_all()

    indicator.set_menu(menu)


def add_new_entry_window(indicator : Optional[appindicator.Indicator], database : Database):
    """
    Open the window to add a new entry.
    :param indicator: Reference to indicator, in order to update the entries there.
    :param database: Data to be displayed in the menu.
    :return: Nothing
    """
    window = NewEntryWindow(database)
    window.connect('destroy', lambda source: create_menu(indicator, database))
    window.show_all()
    window.present()
    return window


def show_search_window(indicator : Optional[appindicator.Indicator], database : Database) -> gtk.Window:
    """
    Open the window to search / filter for an entry.
    :param indicator: Indicator that might be updated when the search window is closed (necessary after deleting) (optional)
    :param database: Data to be displayed in the menu.
    :return: Nothing
    """
    window = SearchWindow(database)
    window.connect('destroy', lambda source: create_menu(indicator, database))
    window.show_all()
    window.present()
    return window


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser(prog="WebsiteIndicator", description="Bookmark management tool with indicator.")
    parser.add_argument('--version', action='version', version='dev')
    #parser.add_argument('--no-indicator', action='store_true', help="Does NOT start the indicator.")
    parser.add_argument('--add', action='store_true', help="Opens the window for adding a new bookmark only.")
    parser.add_argument('--search', action='store_true', help="Opens the window for searching and filtering only.")
    parser.add_argument('--print-config', action='store_true', help="Prints the current runtime configuration to screen.")
    args = vars(parser.parse_args())

    if args['search']:
        database = create_database()
        show_search_window(None, database).connect('destroy', gtk.main_quit)
        gtk.main()
    elif args['add']:
        database = create_database()
        add_new_entry_window(None, database).connect('destroy', gtk.main_quit)
        gtk.main()
    elif args['print_config']:
        print("##### config.yml of WebsiteIndicator #####")
        yaml.dump(config, stream=sys.stdout)
        print()
        exit(0)
    else:
        # Create indicator
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        indicator = appindicator.Indicator.new(APPINDICATOR_ID,
                                               os.path.join(config['script_dir'], 'default_images', 'lesezeichen.jpg'),
                                               appindicator.IndicatorCategory.SYSTEM_SERVICES)
        indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

        create_menu(indicator)

        gtk.main()
