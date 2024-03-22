import os
import webbrowser

import gi

from config import config

gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import Pango
from gi.repository import GdkPixbuf as pixbuf
from model import Database


# Partly based on:
# - https://stackoverflow.com/a/56047460
# - https://python-gtk-3-tutorial.readthedocs.io/en/latest/treeview.html
class SearchWindow(gtk.Window):
    """
    Window to filter and search for an entry.
    """

    def __init__(self, database : Database):
        gtk.Window.__init__(self)
        self.set_default_size(800, 500)
        self.set_title("Search")

        self.database = database
        self.filter_text = ''

        self.grid = gtk.Grid(margin_top=25, margin_bottom=25, margin_end=25, margin_start=25)
        self.grid.set_column_homogeneous(True)
        #self.grid.set_row_homogeneous(True)
        self.add(self.grid)

        self.searchentry = gtk.SearchEntry()
        self.searchentry.grab_focus()
        self.grid.attach(self.searchentry, 0, 0, 3, 1)

        self.subtree_checkbox = gtk.CheckButton(label="show subtrees of matches")
        self.grid.attach(self.subtree_checkbox, 4,0,1,1)

        self.treeview = gtk.TreeView(headers_visible=True)
        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(title="Name")
        col.pack_start(renderer, True)
        col.add_attribute(renderer, "text", 0)
        col.add_attribute(renderer, "weight", 4)
        col.set_reorderable(True)
        col.set_resizable(True)
        self.treeview.append_column(col)

        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(title="Type")
        col.pack_start(renderer, True)
        col.add_attribute(renderer, "text", 1)
        col.add_attribute(renderer, "weight", 4)
        col.set_reorderable(True)
        col.set_resizable(True)
        self.treeview.append_column(col)

        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(title="Action")
        col.pack_start(renderer, True)
        col.add_attribute(renderer, "text", 2)
        col.add_attribute(renderer, "weight", 4)
        col.set_reorderable(True)
        col.set_resizable(True)
        self.treeview.append_column(col)

        self.treeview.expand_all()

        self.scrollable_treelist = gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)

        # Create the filter with the liststore model
        self.tree_store = self.database.get_item_hierarchy()
        self.tree_store.foreach(self.reset_row, True)
        self.filter_ = self.tree_store.filter_new()
        # We do not use a filter function, but a column in the model that
        # determines whether to display an entry or not.
        self.filter_.set_visible_column(3)
        self.treeview.set_model(self.filter_)

        # Show all. Eventually remove in future ...
        self.treeview.expand_all()

        self.scrollable_treelist.add(self.treeview)
        self.grid.attach(self.scrollable_treelist, 0, 1, 5, 2)

        self.clipboard = gtk.Clipboard.get(gdk.SELECTION_CLIPBOARD)

        self.connect("key-press-event", self.on_key_event)
        self.subtree_checkbox.connect("toggled", lambda source: self.refresh_results())
        self.treeview.connect('button-press-event', self.do_execute_action)

        self.set_up_context_menu()

    def set_up_context_menu(self) -> None:
        """
        Creates the context menu for the table view.
        :return: Nothing.
        """

        def popup_action(button, event):
            # Right click
            if event.button != 3:
                return

            # Check entry type
            sel = self.treeview.get_selection()
            model, treeiter = sel.get_selected_rows()
            if treeiter is not None and model[treeiter][1] == Database.Item.TYPE_WEB:
                self.www_menu.popup(None, None, None, None, event.button, event.time)
            elif treeiter is not None and model[treeiter][1] == Database.Item.TYPE_MENU:
                self.menu_menu.popup(None, None, None, None, event.button, event.time)

        # www menu
        self.www_menu = gtk.Menu()

        desired_width = desired_height = 25

        button_exec = gtk.ImageMenuItem("Open website")
        button_exec.connect('activate', lambda source: self.do_execute_action(source))
        pb = pixbuf.Pixbuf.new_from_file(os.path.join(config['script_dir'], 'default_images', 'execute.png'))
        pb = pb.scale_simple(desired_width, desired_height, pixbuf.InterpType.BILINEAR)
        img = gtk.Image()
        img.set_from_pixbuf(pb)
        button_exec.set_image(img)
        button_exec.set_always_show_image(True)
        self.www_menu.append(button_exec)

        button_copy = gtk.ImageMenuItem("Copy link")
        button_copy.connect('activate', lambda source: self.copy_to_clipboard())
        img = gtk.Image.new_from_icon_name("edit-copy", gtk.IconSize.MENU)
        button_copy.set_image(img)
        button_copy.set_always_show_image(True)
        self.www_menu.append(button_copy)

        button_copy = gtk.ImageMenuItem("Copy title")
        button_copy.connect('activate', lambda source: self.copy_to_clipboard(what='text'))
        img = gtk.Image.new_from_icon_name("edit-copy", gtk.IconSize.MENU)
        button_copy.set_image(img)
        button_copy.set_always_show_image(True)
        self.www_menu.append(button_copy)

        button_edit = gtk.ImageMenuItem("Edit")
        button_edit.connect('activate', lambda source: self.not_implemented())
        img = gtk.Image.new_from_icon_name("edit-entry", gtk.IconSize.MENU)
        button_edit.set_image(img)
        button_edit.set_always_show_image(True)
        self.www_menu.append(button_edit)

        button_delete = gtk.ImageMenuItem("Delete")
        button_delete.connect('activate', lambda source: self.do_delete_entry(source))
        img = gtk.Image.new_from_icon_name("delete", gtk.IconSize.MENU)
        button_delete.set_image(img)
        button_delete.set_always_show_image(True)
        self.www_menu.append(button_delete)

        self.www_menu.show_all()

        # menu menu
        self.menu_menu = gtk.Menu()

        button_copy = gtk.ImageMenuItem("Copy title")
        button_copy.connect('activate', lambda source: self.copy_to_clipboard(what='text'))
        img = gtk.Image.new_from_icon_name("edit-copy", gtk.IconSize.MENU)
        button_copy.set_image(img)
        button_copy.set_always_show_image(True)
        self.menu_menu.append(button_copy)

        button_edit = gtk.ImageMenuItem("Edit")
        button_edit.connect('activate', lambda source: self.not_implemented())
        img = gtk.Image.new_from_icon_name("edit-entry", gtk.IconSize.MENU)
        button_edit.set_image(img)
        button_edit.set_always_show_image(True)
        self.menu_menu.append(button_edit)

        button_delete = gtk.ImageMenuItem("Delete")
        button_delete.connect('activate', lambda source: self.do_delete_entry(source))
        img = gtk.Image.new_from_icon_name("delete", gtk.IconSize.MENU)
        button_delete.set_image(img)
        button_delete.set_always_show_image(True)
        self.menu_menu.append(button_delete)

        self.menu_menu.show_all()

        self.treeview.connect('button-release-event', popup_action)

    def on_key_event(self, widget : gtk.Widget, event : gdk.EventKey) -> None:
        """
        Support Strg+C to copy and Enter to open an entry.
        :param widget:
        :param event:
        :return: Nothing
        """
        self.filter_text = self.searchentry.get_text()
        self.refresh_results()

        shortcut = gtk.accelerator_get_label(event.keyval, event.state)
        #print(shortcut)
        if shortcut in ("Strg+Mod2+C", "Strg+C", "Ctrl+C", "Ctrl+Mod2+C"):
            self.copy_to_clipboard()
        elif shortcut in ("Enter", "Mod2+Enter"):
            sel = self.treeview.get_selection()
            model, treeiter = sel.get_selected_rows()
            if treeiter is not None and model[treeiter][1] == Database.Item.TYPE_WEB:
                webbrowser.open(model[treeiter][2])

    def copy_to_clipboard(self, what = 'action'):
        sel = self.treeview.get_selection()
        model, treeiter = sel.get_selected_rows()
        if treeiter is not None and model[treeiter][1] == Database.Item.TYPE_WEB:
            if what == 'action':
                self.clipboard.set_text(model[treeiter][2], -1)
            elif what == 'text':
                self.clipboard.set_text(model[treeiter][0], -1)
        elif treeiter is not None and what == 'text':
            self.clipboard.set_text(model[treeiter][0], -1)

    def refresh_results(self) -> None:
        """
        Refresh the results in the table view.
        :return: Nothing
        """
        search_query = self.filter_text.lower()
        show_subtrees_of_matches = self.subtree_checkbox.get_active()
        if search_query == "":
            self.tree_store.foreach(self.reset_row, True)
            self.treeview.expand_all()
        else:
            self.tree_store.foreach(self.reset_row, False)
            self.tree_store.foreach(self.show_matches, search_query, show_subtrees_of_matches)
            self.treeview.expand_all()
        self.filter_.refilter()

    def reset_row(self, model : gtk.TreeModel, path : gtk.TreePath, iter : gtk.TreeIter, make_visible : bool) -> bool:
        """
        Resets the filter properties of a given entry.
        :param model:
        :param path:
        :param iter:
        :param make_visible:
        :return: always False
        """
        self.tree_store.set_value(iter, 4, Pango.Weight.NORMAL)
        self.tree_store.set_value(iter, 3, make_visible)
        return False # do not stop iterating

    def make_path_visible(self, model : gtk.TreeModel, iter : gtk.TreeIter) -> None:
        """
        Makes the path from the root to iter visible.
        :param model:
        :param iter:
        :return: nothing
        """
        while iter:
            self.tree_store.set_value(iter, 3, True)
            iter = model.iter_parent(iter)

    def make_subtree_visible(self, model : gtk.TreeModel, iter : gtk.TreeIter) -> None:
        """
        Make child rows visible.
        :param model:
        :param iter:
        :return: nothing
        """
        for i in range(model.iter_n_children(iter)):
            subtree = model.iter_nth_child(iter, i)
            if model.get_value(subtree, 3):
                # Subtree already visible
                continue
            self.tree_store.set_value(subtree, 3, True)
            self.make_subtree_visible(model, subtree)

    def show_matches(self, model : gtk.TreeModel,
                           path : gtk.TreePath,
                           iter : gtk.TreeIter,
                           search_query : str,
                           show_subtrees_of_matches : bool) -> bool:
        text = model.get_value(iter, 0).lower()
        if search_query in text:
            # Highlight direct match with bold
            self.tree_store.set_value(iter, 4, Pango.Weight.BOLD)
            # Propagate visibility change up
            self.make_path_visible(model, iter)
            if show_subtrees_of_matches:
                # Propagate visibility change down
                self.make_subtree_visible(model, iter)
            return False
        return False

    def do_execute_action(self, widget : gtk.Widget, event = None) -> None:
        """
        Execute the action (e.g., open the selected website).
        :param widget:
        :param event:
        :return: Nothing.
        """
        if event is None or event.type == gdk.EventType.DOUBLE_BUTTON_PRESS:
            sel = self.treeview.get_selection()
            model, treeiter = sel.get_selected_rows()
            if treeiter is not None and model[treeiter][1] == Database.Item.TYPE_WEB:
                webbrowser.open(model[treeiter][2])

    def do_delete_entry(self, widget : gtk.Widget) -> None:
        sel = self.treeview.get_selection()
        model, treeiter = sel.get_selected_rows()
        if treeiter is not None:
            id = model[treeiter][5]

            if model[treeiter][1] == self.database.Item.TYPE_MENU:
                dialog = gtk.MessageDialog(self, gtk.DialogFlags.DESTROY_WITH_PARENT,
                                           gtk.MessageType.QUESTION, gtk.ButtonsType.YES_NO)
                dialog.set_title("Delete selected menu?")
                dialog.set_markup("Should the following menu be <b>deleted</b> (including sub-entries!)?\n"
                                  f"<i>{model[treeiter][0]}</i>")
                dialog.set_icon_name("dialog-ok")
                response = dialog.run()
                dialog.destroy()
            else:
                dialog = gtk.MessageDialog(self, gtk.DialogFlags.DESTROY_WITH_PARENT,
                                           gtk.MessageType.QUESTION, gtk.ButtonsType.YES_NO)
                dialog.set_title("Delete selected element?")
                dialog.set_markup("Should the following element be <b>deleted</b>?\n"
                                 f"<i>{model[treeiter][0]}</i> (<tt>{model[treeiter][1]}</tt>)")
                dialog.set_icon_name("dialog-ok")
                response = dialog.run()
                dialog.destroy()

            if response != gtk.ResponseType.YES:
                return

            if self.database.delete_item_by_id(id):
                try:
                    self.database.save_data()

                    # Create the filter with the liststore model
                    self.tree_store = self.database.get_item_hierarchy()
                    self.tree_store.foreach(self.reset_row, True)
                    self.filter_ = self.tree_store.filter_new()
                    # We do not use a filter function, but a column in the model that
                    # determines whether to display an entry or not.
                    self.filter_.set_visible_column(3)
                    self.treeview.set_model(self.filter_)
                    self.treeview.expand_all()

                except Exception as e:
                    parent = self
                    md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                                           gtk.ButtonsType.CLOSE, "Error writing file. Message: " + str(e))
                    md.run()
                    md.destroy()
                    return
            else:
                parent = self
                md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                                       gtk.ButtonsType.CLOSE, "Element not found. Something weird happend ...")
                md.run()
                md.destroy()
                return
            print("Global ID",id)

    def not_implemented(self):
        parent = self
        md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                               gtk.ButtonsType.CLOSE, "Not implemented, yet. Please directly modify the XML file.")
        md.run()
        md.destroy()
        return
