import webbrowser

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import Pango
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
        self.grid.attach(self.searchentry, 0, 0, 3, 1)

        #vbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
        self.subtree_checkbox = gtk.CheckButton(label="show subtrees of matches")
        self.grid.attach(self.subtree_checkbox, 4,0,1,1)

        self.treeview = gtk.TreeView(headers_visible=True)
        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(title="Name")
        col.pack_start(renderer, True)
        col.add_attribute(renderer, "text", 0)
        self.treeview.append_column(col)

        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(title="Type")
        col.pack_start(renderer, True)
        col.add_attribute(renderer, "text", 1)
        self.treeview.append_column(col)

        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(title="Action")
        col.pack_start(renderer, True)
        col.add_attribute(renderer, "text", 2)
        self.treeview.append_column(col)

        self.treeview.expand_all()

        self.scrollable_treelist = gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)

        # Create the filter with the liststore model
        self.tree_store = self.database.get_item_hierarchy()
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
            sel = self.treeview.get_selection()
            model, treeiter = sel.get_selected_rows()
            if treeiter is not None and model[treeiter][1] == Database.Item.TYPE_WEB:
                self.clipboard.set_text(model[treeiter][2], -1)
        elif shortcut in ("Enter", "Mod2+Enter"):
            sel = self.treeview.get_selection()
            model, treeiter = sel.get_selected_rows()
            if treeiter is not None and model[treeiter][1] == Database.Item.TYPE_WEB:
                webbrowser.open(model[treeiter][2])

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

    def do_execute_action(self, widget : gtk.Widget, event) -> None:
        """
        Execute the action (e.g., open the selected website).
        :param widget:
        :param event:
        :return: Nothing.
        """
        if event.type == gdk.EventType.DOUBLE_BUTTON_PRESS:
            sel = self.treeview.get_selection()
            model, treeiter = sel.get_selected_rows()
            if treeiter is not None and model[treeiter][1] == Database.Item.TYPE_WEB:
                webbrowser.open(model[treeiter][2])
