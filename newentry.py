import shutil
import gi

from model import Database
from config import *

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk


# Based on: https://python-gtk-3-tutorial.readthedocs.io/en/latest/treeview.html
class NewEntryWindow(gtk.Window):
    def __init__(self, database : Database):
        gtk.Window.__init__(self)
        self.set_default_size(width=600, height=500)
        self.set_title("Add new bookmark entry")

        self.database = database

        self.set_icon_from_file(os.path.join(config['script_dir'], 'default_images', 'lesezeichen.jpg'))

        self.grid = gtk.Grid(margin_top=25, margin_bottom=25, margin_end=25, margin_start=25)
        self.grid.set_column_homogeneous(True)
        #self.grid.set_row_homogeneous(True)

        self.add(self.grid)

        l = gtk.Label(margin_top=5, margin_start=5, margin_end=5, margin_bottom=5)
        l.set_text("Name:")
        l.set_xalign(0.0)
        self.grid.attach(l, 1, 1, 1, 1)

        self.name_entry = gtk.Entry()
        self.grid.attach(self.name_entry, 2, 1, 2, 1)

        l = gtk.Label(margin_top=5, margin_start=5, margin_end=5, margin_bottom=5)
        l.set_text("Type:")
        l.set_xalign(0.0)
        self.grid.attach(l, 1, 2, 1, 1)

        self.type_field_store = gtk.ListStore(str)
        for e in Database.Item.TYPES:
            self.type_field_store.append([e])
        self.type_combo_field = gtk.ComboBox(model=self.type_field_store)
        #self.type_combo_field = gtk.ComboBox.new_with_model_and_entry(self.type_field_store)
        renderer = gtk.CellRendererText()
        self.type_combo_field.pack_start(renderer, True)
        self.type_combo_field.add_attribute(cell=renderer, attribute="text", column=0)
        #self.type_combo_field.set_entry_text_column(0)
        self.grid.attach(self.type_combo_field, 2,2,2,1)

        l = gtk.Label(margin_top=5, margin_start=5, margin_end=5, margin_bottom=5)
        l.set_text("Action (e.g., URL):")
        l.set_xalign(0.0)
        self.grid.attach(l, 1, 3, 1, 1)

        self.action_entry = gtk.Entry()
        self.grid.attach(self.action_entry, 2, 3, 2, 1)

        l = gtk.Label(margin_top=5, margin_start=5, margin_end=5, margin_bottom=5)
        l.set_text("Icon:")
        l.set_xalign(0.0)
        self.grid.attach(l, 1, 4, 1, 1)

        self.file_chooser = gtk.FileChooserDialog()
        self.file_chooser.add_buttons(
            gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL,
            gtk.STOCK_OPEN, gtk.ResponseType.OK)
        self.file_chooser.set_name("Add icon")

        filefilter = gtk.FileFilter()
        filefilter.set_name("Image files")
        filefilter.add_pattern("*.jpg")
        filefilter.add_pattern("*.jpeg")
        filefilter.add_pattern("*.png")
        filefilter.add_pattern("*.tif")
        filefilter.add_pattern("*.bmp")
        filefilter.add_pattern("*.gif")
        filefilter.add_pattern("*.tiff")
        self.file_chooser.set_filter(filefilter)

        self.icon_input = gtk.FileChooserButton.new_with_dialog(self.file_chooser)
        self.icon_input.set_current_folder(".")
        self.grid.attach(self.icon_input, 2, 4, 1, 1)

        l = gtk.Label(margin_top=5, margin_start=5, margin_end=5, margin_bottom=5)
        l.set_text("Entry location:")
        l.set_xalign(0.0)
        self.grid.attach(l, 1, 5, 1, 1)

        self.treeview = gtk.TreeView(headers_visible=False)
        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(title="Menu")
        col.pack_start(renderer, True)
        col.add_attribute(renderer, "text", 0)
        self.treeview.append_column(col)
        self.treeview.set_model(self.database.get_menu_hierarchy())
        self.treeview.expand_all()

        self.scrollable_treelist = gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.scrollable_treelist.add(self.treeview)
        self.grid.attach(self.scrollable_treelist, 1, 6, 3, 1)

        self.button_save = gtk.Button(label="Save", tooltip_text="Saves the entry")
        self.button_cancel = gtk.Button(label="Cancel", tooltip_text="Does not store the entry and closes this window.")
        self.button_save.connect("clicked", self.do_save_entry)
        self.button_cancel.connect("clicked", self.do_exit)
        self.grid.attach(self.button_save, 1, 8, 1, 1)
        self.grid.attach(self.button_cancel, 2, 8, 1, 1)

    def do_exit(self, source, callback_data = None):
        self.destroy()

    def do_save_entry(self, source, callback_data = None):
        title = self.name_entry.get_text()
        if len(title) < 3:
            parent = self
            md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                                   gtk.ButtonsType.CLOSE, "Title must contain at least 3 characters.")
            md.run()
            md.destroy()
            return

        type_iter = self.type_combo_field.get_active_iter()
        action_type = None
        if type_iter is not None:
            model = self.type_combo_field.get_model()
            action_type = model[type_iter][0]
        else:
            parent = self
            md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                                   gtk.ButtonsType.CLOSE, "Please select an entry type.")
            md.run()
            md.destroy()
            return

        action_text = self.action_entry.get_text()
        if action_type == "www" and len(action_text) < 11:
            parent = self
            md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                                   gtk.ButtonsType.CLOSE, "URL required.")
            md.run()
            md.destroy()
            return
        elif len(action_text) == 0:
            action_text = None

        menu_selection = self.treeview.get_selection().get_selected()
        if menu_selection is not None and menu_selection[1] is not None:
            menu_title = self.treeview.get_model().get_value(menu_selection[1], 0)
            menu_item_id = self.treeview.get_model().get_value(menu_selection[1], 1)
        else:
            parent = self
            md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                                   gtk.ButtonsType.CLOSE, "Please select a parent menu entry.")
            md.run()
            md.destroy()
            return

        # Copy icon to
        icon_path = self.file_chooser.get_filename()
        if icon_path == '':
            icon_path = None
        if icon_path is not None:
            try:
                shutil.copy(icon_path, config['general']['image_dir'])
            except shutil.SameFileError:
                pass # Okay in this case
            icon_path = os.path.basename(icon_path)

        item = Database.Item(text=title, action=action_text, type=action_type, icon=icon_path)
        if self.database.add_item(menu_item_id, item):
            try:
                self.database.save_data()
                self.do_exit(None)
            except Exception as e:
                parent = self
                md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                                       gtk.ButtonsType.CLOSE, "Error writing file. Message: "+str(e))
                md.run()
                md.destroy()
                return
        else:
            parent = self
            md = gtk.MessageDialog(parent, gtk.DialogFlags.DESTROY_WITH_PARENT, gtk.MessageType.ERROR,
                                   gtk.ButtonsType.CLOSE, "Parent not found. Something weird happend ...")
            md.run()
            md.destroy()
            return
