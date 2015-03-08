# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys, tempfile, png, os, webbrowser

try:
    import Tkinter as Tk_
    import ttk
    import tkMessageBox
    from urllib import pathname2url
except ImportError:
    import tkinter as Tk_
    from tkinter import ttk
    import tkinter.messagebox as tkMessageBox
    from urllib.request import pathname2url

from snappy import filedialog, __file__ as snappy_dir

from infodialog import about_snappy
    
OSX_shortcuts = {'Open...'    : 'Command-o',
                 'Save'       : 'Command-s',
                 'Save as...' : 'Command-Shift-s',
                 'Cut'        : 'Command-x',
                 'Copy'       : 'Command-c',
                 'Paste'      : 'Command-v',
                 'Close'      : 'Command-w', 
                 'Left'       : '←',
                 'Up'         : '↑',
                 'Right'      : '→',
                 'Down'       : '↓'}

OSX_shortcut_events = {'Open...'     : '<Command-o>',
                       'Save'        : '<Command-s>',
                       'Save as...'  : '<Command-S>',
                       'Cut'         : '<Command-x>',
                       'Copy'        : '<Command-c>',
                       'Paste'       : '<Command-v>',
                       'Close'       : '<Command-w>'
                   }
                 
Linux_shortcuts = {'Open...'    : 'Cntl+O',
                   'Save'       : 'Cntl+S',
                   'Save as...' : 'Cntl+Shift+S',
                   'Cut'        : 'Cntl+X',
                   'Copy'       : 'Cntl+W',
                   'Paste'      : 'Cntl+V',
                   'Left'       : '←',
                   'Up'         : '↑',
                   'Right'      : '→',
                   'Down'       : '↓'}

Linux_shortcut_events = {'Open...'    : '<Control-o>',
                         'Save'       : '<Control-s>',
                         'Save as...' : '<Control-S>',
                         'Cut'        : '<Control-x>',
                         'Copy'       : '<Control-w>',
                         'Paste'      : '<Control-v>',
                          }

if sys.platform == 'darwin' :
    scut = OSX_shortcuts
    scut_events = OSX_shortcut_events
elif sys.platform == 'linux2' :
    scut = Linux_shortcuts
    scut_events = Linux_shortcut_events
else: # fall back choice
    scut = Linux_shortcuts
    scut_events = Linux_shortcut_events

def add_menu(root, menu, label, command, state='active'):
    accelerator = scut.get(label, '')
    menu.add_command(label=label, accelerator=accelerator,
                     command=command, state=state)
    if scut_events.get(label, None) and state != 'disabled':
        root.bind(scut_events[label], command)

class EditMenu(Tk_.Menu):
    """Edit Menu cascade containing Cut, Copy, Paste and Delete. To use,
    provide a callback function which returns a dict specifying which
    editing functions should be enabled.  The keys should be chosen
    from the list ['Cut', 'Copy', 'Paste, 'Delete'] and the values
    should be functions to be call for the corresponding actions.  If
    a key is missing, the corresponding menu entry will be disabled.

    """
    entries = ['Cut', 'Copy', 'Paste', 'Delete']

    def __init__(self, menubar, callback):
        Tk_.Menu.__init__(self, menubar, name='edit', postcommand=self.configure)
        self.get_actions = callback
        self.add_entry('Cut', lambda event=None: self.actions['Cut']())
        self.add_entry('Copy', lambda event=None: self.actions['Copy']())
        self.add_entry('Paste', lambda event=None: self.actions['Paste']())
        self.add_entry('Delete', lambda event=None: self.actions['Delete']())
        self.actions = {}

    def add_entry(self, label, command):
        accelerator = scut.get(label, '')
        self.add_command(label=label, accelerator=accelerator,
                         command=command, state='disabled')
    
    def configure(self):
        """Called before the menu is opened."""
        self.actions = self.get_actions()
        for entry in self.entries:
            if self.actions.get(entry, None):
                self.entryconfig(entry, state='normal')
            else:
                self.entryconfig(entry, state='disabled')
                                
class HelpMenu(Tk_.Menu):
    """Help Menu cascade.  Always contains the main SnapPy help entry.
    Additional help entries for specific tools, such as a Dirichlet
    viewer, may be added or removed.

    """
    def __init__(self, menubar):
        # on OS X setting name='help' makes this a system help menu.
        Tk_.Menu.__init__(self, menubar, name='help')
        self.add_command(label='Help on SnapPy ...', command=self.show_SnapPy_help)
        self.extra_commands = {}
        path = os.path.join(os.path.dirname(snappy_dir), 'doc', 'index.html')
        self.doc_path = os.path.abspath(path)

    def show_SnapPy_help(self):
        if os.path.exists(self.doc_path):
            url = 'file:' + pathname2url(self.doc_path)
            try:
                webbrowser.open_new_tab(url)
            except webbrowser.Error:
                tkMessageBox.showwarning('Error', 'Failed to open the documentation file.')
        else:
            tkMessageBox.showwarning('Not found!', 'The file %s does not exist.'%doc_path)

    def extra_command(self, label, command):
        self.extra_commands[label] = command

    def activate(self, labels):
        """Manage extra help entries.
        Pass the labels of the extra commands to be activated."""
        end = self.index(Tk_.END)
        if end > 0:
            self.delete(1, self.index(Tk_.END))
        for label in labels:
            if label in self.extra_commands:
                self.add_command(label=label, command=self.extra_commands[label])

def really_disable_menu_items(menu):
    """
    On OS X, menu items aren't greying out as they should.
    """
    for label, entry in menu.children.items():
        try:
            for i in range(menu.index('end') + 1):
                if entry.type(i) == 'command':
                    if menu.entrycget(i, 'state') == 'disabled':
                        menu.entryconfig(i, state='disabled')
        except:
            pass

def add_edit_menu_with_disabled_items(menubar, window):
    edit_menu = Tk_.Menu(menubar, name='edit')
    add_menu(window, edit_menu, 'Cut', None, state='disabled')
    add_menu(window, edit_menu, 'Copy', None, state='disabled')
    add_menu(window, edit_menu, 'Paste', None, state='disabled')
    add_menu(window, edit_menu, 'Delete', None, state='disabled')
    menubar.add_cascade(label='Edit', menu=edit_menu)

def add_window_menu(self):
    if self.window_master is not None:
        if sys.platform != 'darwin':
            window_menu = self.window_master.menubar.children['window']
            self.menubar.add_cascade(label='Window', menu=window_menu)
        else:
            self.window_menu = Tk_.Menu(self.menubar, name='window')
            self.menubar.add_cascade(label='Window', menu=self.window_menu)

def togl_save_image(self):
    savefile = filedialog.asksaveasfile(
        mode='wb',
        title='Save Image As PNG Image File',
        defaultextension = '.png',
        filetypes = [
            ("PNG image files", "*.png *.PNG", ""),
            ("All files", "")])
    self.window.update()
    self.widget.redraw()
    self.window.update()
    self.widget.redraw()
    if savefile:
        ppm_file = tempfile.mktemp() + ".ppm"
        PI = Tk_.PhotoImage()
        self.widget.tk.call(self.widget._w, 'takephoto', PI.name)
        PI.write(ppm_file, format='ppm')
        infile = open(ppm_file, 'rb')
        format, width, height, depth, maxval = \
                png.read_pnm_header(infile, ('P5','P6','P7'))
        greyscale = depth <= 2
        pamalpha = depth in (2,4)
        supported = [2**x-1 for x in range(1,17)]
        mi = supported.index(maxval)
        bitdepth = mi+1
        writer = png.Writer(width, height,
                        greyscale=greyscale,
                        bitdepth=bitdepth,
                        alpha=pamalpha)
        writer.convert_pnm(infile, savefile)
        savefile.close()
        infile.close()
        os.remove(ppm_file)

def browser_menus(self):
    """Menus for the browser window.  Used as Browser.build_menus.
    Creates a menubar attribute for the browser.

    """
    window = self.window
    self.menubar = menubar = Tk_.Menu(window)
    Python_menu = Tk_.Menu(menubar, name="apple")
    Python_menu.add_command(label='About SnapPy ...',
                            command=lambda : about_snappy(window))
    Python_menu.add_separator()
    Python_menu.add_command(label='SnapPy Preferences ...', state='disabled')
    Python_menu.add_separator()
    if sys.platform == 'linux2' and self.window_master is not None:
        Python_menu.add_command(label='Quit SnapPy', command=self.window_master.close)
    menubar.add_cascade(label='SnapPy', menu=Python_menu)
    File_menu = Tk_.Menu(menubar, name='file')
    add_menu(window, File_menu, 'Open...', None, 'disabled')
    add_menu(window, File_menu, 'Save as...', self.save)
    File_menu.add_separator()
    add_menu(window, File_menu, 'Close', self.close)
    menubar.add_cascade(label='File', menu=File_menu)
    edit_menu = Tk_.Menu(menubar, name='edit')
    add_menu(window, edit_menu, 'Cut', None, state='disabled')
    add_menu(window, edit_menu, 'Copy', None, state='normal')
    add_menu(window, edit_menu, 'Paste', None, state='disabled')
    add_menu(window, edit_menu, 'Delete', None, state='disabled')
    menubar.add_cascade(label='Edit', menu=edit_menu)
    add_window_menu(self)
    help_menu = HelpMenu(menubar)
    help_menu.extra_command(label='Help on Polyhedron Viewer ...',
                       command=self.dirichlet_viewer.widget.help)
    help_menu.extra_command(label='Help on Horoball Viewer ...',
                       command=self.horoball_viewer.widget.help)
    menubar.add_cascade(label='Help', menu=help_menu)

def plink_menus(self):
    """Menus for the SnapPyLinkEditor."""

    self.menubar = menubar = Tk_.Menu(self.window)
    Python_menu = Tk_.Menu(menubar, name="apple")
    Python_menu.add_command(label='About PLink...', command=self.about)
    Python_menu.add_separator()
    Python_menu.add_command(label='Preferences...', state='disabled')
    Python_menu.add_separator()
    if sys.platform == 'linux2' and self.window_master is not None:
        Python_menu.add_command(label='Quit SnapPy', command=self.window_master.close)
    menubar.add_cascade(label='SnapPy', menu=Python_menu)
    File_menu = Tk_.Menu(menubar, name='file')
    add_menu(self.window, File_menu, 'Open...', self.load)
    add_menu(self.window, File_menu, 'Save as...', self.save)
    self.build_save_image_menu(menubar, File_menu) # Add image save menu
    File_menu.add_separator()
    if self.callback:
        add_menu(self.window, File_menu, 'Close', self.done)
    else:
        add_menu(self.window, File_menu, 'Exit', self.done)
    menubar.add_cascade(label='File', menu=File_menu)
    Edit_menu = Tk_.Menu(menubar, name='edit')
    add_menu(self.window, Edit_menu, 'Cut', None, state='disabled')
    add_menu(self.window, Edit_menu, 'Copy', None, state='disabled')
    add_menu(self.window, Edit_menu, 'Paste', None, state='disabled')
    add_menu(self.window, Edit_menu, 'Delete', None, state='disabled')
    menubar.add_cascade(label='Edit', menu=Edit_menu)
    self.build_plink_menus() # Application Specific Menus
    Window_menu = self.window_master.menubar.children['window']
    menubar.add_cascade(label='Window', menu=Window_menu)
    Help_menu = Tk_.Menu(menubar, name="help")
    menubar.add_cascade(label='Help', menu=HelpMenu(menubar))
    Help_menu.add_command(label='Help on PLink ...', command=self.howto)
    self.window.config(menu=menubar)

def dirichlet_menus(self):
    """Menus for the standalone Dirichlet viewer."""
    self.menubar = menubar = Tk_.Menu(self.window)
    Python_menu = Tk_.Menu(menubar, name="apple")
    Python_menu.add_command(label='About SnapPy ...',
                            command=lambda : about_snappy(self.window))
    Python_menu.add_separator()
    Python_menu.add_command(label='SnapPy Preferences ...', state='disabled')
    Python_menu.add_separator()
    if sys.platform == 'linux2' and self.window_master is not None:
        Python_menu.add_command(label='Quit SnapPy', command=
                                self.window_master.close)
    menubar.add_cascade(label='SnapPy', menu=Python_menu)
    File_menu = Tk_.Menu(menubar, name='file')
    add_menu(self.window, File_menu, 'Open...', None, 'disabled')
    add_menu(self.window, File_menu, 'Save as...', None, 'disabled')
    File_menu.add_command(label='Save Image...', command=self.save_image)
    File_menu.add_separator()
    add_menu(self.window, File_menu, 'Close', command=self.close)
    menubar.add_cascade(label='File', menu=File_menu)
    add_browser_edit_menu(menubar, self.window)
    add_window_menu(self)
    help_menu = HelpMenu(menubar)
    help_menu.extra_command(label='Help on Polyhedron Viewer ...', command=self.widget.help)
    help_menu.activate('Help on PolyhedronViewer ...')
    self.menubar.add_cascade(label='Help', menu=help_menu)

def horoball_menus(self):
    """Menus for the standalone Horoball viewer."""
    self.menubar = menubar = Tk_.Menu(self.window)
    Python_menu = Tk_.Menu(menubar, name="apple")
    Python_menu.add_command(label='About SnapPy ...',
                            command=lambda : about_snappy(self.window))
    Python_menu.add_separator()
    Python_menu.add_command(label='SnapPy Preferences ...',  state='disabled')
    Python_menu.add_separator()
    if sys.platform == 'linux2' and self.window_master is not None:
        Python_menu.add_command(label='Quit SnapPy',
                                command=self.window_master.close)
    menubar.add_cascade(label='SnapPy', menu=Python_menu)
    File_menu = Tk_.Menu(menubar, name='file')
    File_menu.add_command(
        label='Open...', accelerator=scut['Open...'], state='disabled')
    File_menu.add_command(
        label='Save as...', accelerator=scut['Save as...'], state='disabled')
    Print_menu = Tk_.Menu(menubar, name='print')
    File_menu.add_command(label='Save Image...', command=self.save_image)
    File_menu.add_separator()
    File_menu.add_command(label='Close', command=self.close)
    menubar.add_cascade(label='File', menu=File_menu)
    menubar.add_cascade(lable='Edit', menu=EditMenu(menubar, self.edit_actions))
    add_window_menu(self)
    help_menu = HelpMenu(menubar)
    help_menu.extra_command(label='Help on Horoball Viewer ...', command=self.widget.help)
    help_menu.activate('Help on HoroballViewer ...')
    self.menubar.add_cascade(label='Help', menu=help_menu)



# def link_menus(self):
#     self.menubar = menubar = Tk_.Menu(self.window)
#     Python_menu = Tk_.Menu(menubar, name="apple")
#     Python_menu.add_command(label='About SnapPy ...',
#                             command=lambda : about_snappy(self.window))
#     Python_menu.add_separator()
#     Python_menu.add_command(label='SnapPy Preferences ...', state='disabled')
#     Python_menu.add_separator()
#     if sys.platform == 'linux2' and self.window_master is not None:
#         Python_menu.add_command(label='Quit SnapPy', command=
#                                 self.window_master.close)
#     menubar.add_cascade(label='SnapPy', menu=Python_menu)
#     File_menu = Tk_.Menu(menubar, name='file')
#     add_menu(self.window, File_menu, 'Open...', None, 'disabled')
#     add_menu(self.window, File_menu, 'Save as...', None, 'disabled')
#     self.build_save_image_menu(menubar, File_menu)
#     File_menu.add_separator()
#     add_menu(self.window, File_menu, 'Close', command=self.close)
#     menubar.add_cascade(label='File', menu=File_menu)
#     add_edit_menu_with_disabled_items(menubar, self.window)
#     add_window_menu(self)
