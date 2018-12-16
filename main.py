from tkinter import *
from tkinter import filedialog, Entry, messagebox, Text, Scrollbar, Menu, OptionMenu
from tkinter.ttk import Frame, Button, Progressbar, Notebook
import csv
import os
import logging
from datetime import datetime
import traceback
from importlib import import_module


class TacoShell:
    """

    """

    def __init__(self):
        # ROOT
        self.root = Tk()
        self.root.title("Shell GUI")
        self.root.minsize(width=200, height=200)
        self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.__position_window(self.root, 300, 300)

        # Declarations
        self.DEBUG_MODE = False
        self.help_text = "This won't help you at all.."
        self.children = {}
        self._next_child_id = 0
        self.components = {}
        self.instance_changes = []
        self.config_file = 'shell.config'

        # Initializations
        self.__init_menu()
        self.__init_debug()
        self.__init_frame_source()
        self.__init_frame_generate()
        self.__init_frame_progress()
        self.__init_frame_tabs()
        self.__init_frame_search()
        self.__set_pack_order()
        self.__read_config_settings()
        self.__repack()
        self.__connect_to_users()
        self.root.mainloop()

    @staticmethod
    def __position_window(window, window_width, window_height, x=None, y=None):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        if x is None:
            x = int((screen_width / 2) - (window_width / 2))
        if y is None:
            y = int((screen_height / 2) - (window_height / 2))
        window.geometry("{}x{}+{}+{}".format(window_width, window_height,
                                             max(min(x, screen_width - 100), 20),
                                             max(min(y, screen_height - 100), 20)))

    def __set_pack_order(self):
        separator = Frame(height=2, borderwidth=1, relief=GROOVE)

        # Order in pack_list determines order in root
        # TODO look into using an ordered dict
        self.packing = {
            'list': [
                {'name': 'frame_progress', 'widget': self.components['frame_progress'],
                 'side': BOTTOM, 'fill': X, 'default': True, 'operable': True},
                {'name': 'separator', 'widget': separator,
                 'side': BOTTOM, 'fill': X, 'pady': (3, 0), 'default': True, 'operable': True},
                {'name': 'frame_generate', 'widget': self.components['frame_generate'],
                 'side': BOTTOM, 'fill': X, 'default': True, 'operable': True},
                {'name': 'frame_debug', 'widget': self.components['frame_debug'],
                 'side': TOP, 'fill': X, 'default': False, 'operable': True},
                {'name': 'frame_source', 'widget': self.components['frame_source'],
                 'side': TOP, 'fill': X, 'default': True, 'operable': True},
                {'name': 'frame_search', 'widget': self.components['frame_search'],
                 'side': TOP, 'fill': X, 'default': False, 'operable': True},
                {'name': 'frame_tabs', 'widget': self.components['frame_tabs'],
                 'side': TOP, 'fill': BOTH, 'expand': YES, 'default': True, 'operable': True}
            ],
            # Indices must match the order in the list
            'indices': {
                'frame_progress': 0,
                'separator': 1,
                'frame_generate': 2,
                'frame_debug': 3,
                'frame_source': 4,
                'frame_search': 5,
                'frame_tab': 6
            }
        }
        config = self.interpret_file(self.config_file, '=') if os.path.isfile(self.config_file) else []
        for w in self.packing['list']:
            val = self.__read_config_flags(config, w['name'])
            w['flag'] = val if val is not None else w['default']

    def __read_config_settings(self):
        config = self.interpret_file(self.config_file, '=') if os.path.isfile(self.config_file) else []
        # TODO whitelist which parameters can be set by configuration file
        for c in config:
            try:
                address = c[0].split('.')
                if len(address) == 1:
                    self.components[address[0]] = c[1]
                elif len(address) == 2:
                    # TODO flags should be set like this
                    # if address[1] == 'flag':
                    #     self.components[address[0]][address[1]] = c[1]
                    if address[1] == 'set':
                        self.components[address[0]].set(c[1])
                        if address[0] == 'entry_path_text':
                            if os.path.isfile(self.config_file):
                                self.components['btn_generate'].config(state='normal')

            except:  # TODO handle key errors
                pass

    @staticmethod
    def __read_config_flags(config, name):
        for line in config:
            if line[0] == name + '.flag':
                if line[1] == 'True':
                    return True
                elif line[1] == 'False':
                    return False

    def __on_closing(self):
        self.__save()
        if 'window_flags' in self.components.keys():
            self.components['window_flags'].destroy()
        self.root.destroy()

    def __save(self):
        file = open(self.config_file, 'w+')
        if self.instance_changes:
            for item in self.instance_changes:
                if item == 'flags_changed':
                    response = messagebox.askyesnocancel("Unsaved flag changes",
                                                         "Do you to save flag settings before quitting?")
                    if response is None:
                        return
                    elif response:
                        self.__save_flags(file)
        if os.path.isfile(self.components['entry_new_path'].get()):
            file.write('entry_path_text.set=' + self.components['entry_path_text'].get() + '\n')
        file.close()

    def __save_flags(self, file):
        for w in self.packing['list']:
            if w['flag'] != w['default']:
                file.write(w['name'] + '.flag=' + str(w['flag']) + '\n')

    def __init_menu(self):
        menubar = Menu(self.root)

        # Cascade options
        menu_options = Menu(menubar, tearoff=0)
        menu_options.add_command(label="debug", command=self.__toggle_debug)
        menu_options.add_command(label="help", command=self.menu_help)

        # Add to menubar
        menubar.add_cascade(label="options", menu=menu_options)
        menubar.add_command(label="flags", command=self.__open_flag_settings)
        menubar.add_command(label="addons")
        self.root.config(menu=menubar)

    def __open_flag_settings(self):
        if 'window_flags' not in self.components.keys():
            window_flags = Toplevel(self.root)
            window_flags.grab_set()
            window_flags.title("flags")
            self.__position_window(window_flags, 270, 350,
                                   self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)
            window_flags.minsize(width=200, height=200)
            window_flags.attributes('-toolwindow', True)
            window_flags.protocol("WM_DELETE_WINDOW", self.__window_flags_closing)

            v = []
            Button(window_flags, text='set', command=lambda: self.__set_flags(v)).pack(side=BOTTOM, anchor='e')
            for i, w in enumerate(self.packing['list']):
                if w['operable']:
                    row = Frame(window_flags)
                    Label(row, text=w['name']).pack(side=LEFT)
                    v.append({'idx': i, 'var': StringVar(row)})
                    val = 'True{}' if w['flag'] else 'False{}'
                    v[-1]['var'].set(val.format('(default)' if w['flag'] == w['default'] else ''))
                    choices = ['True(default)' if w['default'] else 'True',
                               'False(default)' if not w['default'] else 'False']
                    opt = OptionMenu(row, v[-1]['var'], *choices)
                    opt.config(width=12)
                    opt.pack(side=RIGHT)

                    row.pack(side=TOP, fill=X)
                    Frame(window_flags, height=2, borderwidth=1, relief=GROOVE).pack(side=TOP, fill=X)

            self.components['window_flags'] = window_flags
            window_flags.mainloop()

        elif not self.components['window_flags'].state() == 'normal':
            self.components['window_flags'].deiconify()
            self.components['window_flags'].grab_set()
            self.__position_window(self.components['window_flags'], 270, 350,
                                   self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)

    def __window_flags_closing(self):
        self.components['window_flags'].withdraw()
        self.components['window_flags'].grab_release()

    def __set_flags(self, v):
        for d in v:
            self.packing['list'][d['idx']]['flag'] = True if d['var'].get() in ('True', 'True(default)') else False
        self.__repack()
        if 'flags_changed' not in self.instance_changes:
            self.instance_changes.append('flags_changed')

    def __init_debug(self):
        frame_debug = Frame(self.root)
        lbl_debug = Label(frame_debug, text="DEBUG MODE", fg="red")

        lbl_debug.pack(side=RIGHT)

        self.components['frame_debug'] = frame_debug

    def __init_frame_source(self):
        frame_source = Frame(self.root)
        self.components['entry_path_text'] = StringVar()
        entry_new_path = Entry(frame_source,
                               textvariable=self.components['entry_path_text'])
        btn_set_directory = Button(frame_source,
                                   text="Set source",
                                   command=self.__set_directory)
        entry_new_path.bind(sequence='<KeyRelease>', func=self.__path_keypress)

        btn_set_directory.pack(side=LEFT, padx=5, pady=5)
        entry_new_path.pack(side=LEFT, fill=X, expand=YES, padx=5)

        self.components['frame_source'] = frame_source
        self.components['entry_new_path'] = entry_new_path
        self.components['btn_set_directory'] = btn_set_directory

    def __init_frame_generate(self):
        frame_generate = Frame(self.root)
        btn_generate = Button(frame_generate,
                              text="Generate",
                              state='disabled',
                              )
        btn_generate.pack(side=RIGHT, padx=5, pady=5, fill=X)

        self.components['frame_generate'] = frame_generate
        self.components['btn_generate'] = btn_generate

    def __init_frame_progress(self):
        frame_progress = Frame(self.root)
        progressbar = Progressbar(frame_progress, style='black.Horizontal.TProgressbar')
        lbl_progress = Label(frame_progress, text="Idle", width=10)

        lbl_progress.pack(side=LEFT)
        progressbar.pack(side=RIGHT, padx=5, pady=5, fill=X, expand=YES)

        self.components['frame_progress'] = frame_progress
        self.components['lbl_progress'] = lbl_progress

    def __init_frame_tabs(self):
        frame_tabs = Frame(self.root)
        tab_control = Notebook(frame_tabs)

        frame_log = Frame(tab_control)
        txt_log = Text(frame_log, wrap='none', state='disabled')
        scrollbar_hori = Scrollbar(frame_log, orient=HORIZONTAL, command=txt_log.xview)
        txt_log['xscrollcommand'] = scrollbar_hori.set
        scrollbar_vert = Scrollbar(frame_log, command=txt_log.yview)
        txt_log['yscrollcommand'] = scrollbar_vert.set
        txt_log.bind('<Control-f>', self.__tab_hotkeys)
        txt_log.tag_configure("blue", foreground="blue")

        scrollbar_vert.pack(side=RIGHT, fill=Y, pady=(5, 25))
        scrollbar_hori.pack(side=BOTTOM, fill=X, padx=(5, 5))
        txt_log.pack(side=LEFT, padx=5, pady=5, fill=BOTH, expand=YES)

        tab_control.add(frame_log, text='Log')
        tab_control.pack(fill=BOTH, expand=YES)

        self.components['frame_tabs'] = frame_tabs
        self.components['txt_log'] = txt_log

    def __init_frame_search(self):
        frame_search = Frame(self.root)
        entry_search = Entry(frame_search, width=10)
        entry_search.bind(sequence='<KeyRelease>', func=self.__search_keypress)
        lbl_search = Label(frame_search, text='Search')

        entry_search.pack(side=RIGHT, padx=(0, 25))
        lbl_search.pack(side=RIGHT)

        self.components['frame_search'] = frame_search
        self.components['entry_search'] = entry_search

    def __provide_child_id(self):
        self._next_child_id += 1
        return str(self._next_child_id)

    def __connect_to_users(self):
        child_id = self.__provide_child_id()
        module = import_module('blockgenerator')
        instance = module.make_taco()
        self.children[child_id] = instance  # BlockGenerator()  # TODO connect to user based on config
        self.children[child_id].connect_to_gui(self, child_id)

    def __set_flag(self, widget, state):
        self.packing['list'][self.packing['indices'][widget]]['flag'] = state

    def __toggle_debug(self):
        if self.DEBUG_MODE:
            self.DEBUG_MODE = False
            self.__set_flag('frame_debug', False)
            if not os.path.isfile(self.components['entry_new_path'].get()):
                self.components['btn_generate'].config(state='disabled')
            self.components['txt_log'].config(state='disabled')
            self.__repack(TOP)

        else:
            self.DEBUG_MODE = True
            self.__set_flag('frame_debug', True)
            self.components['btn_generate'].config(state='normal')
            self.components['txt_log'].config(state='normal')
            self.__repack(TOP)

    @staticmethod
    def __val(d, key):
        return d[key] if key in d.keys() else None

    def __repack(self, s=None):

        for w in self.packing['list']:
            if s is None or s == w['side']:
                w['widget'].pack_forget()

        for w in self.packing['list']:
            if (s is None or s == w['side']) and w['flag']:
                w['widget'].pack(side=self.__val(w, 'side'),
                                 fill=self.__val(w, 'fill'),
                                 expand=self.__val(w, 'expand'),
                                 padx=self.__val(w, 'padx'),
                                 pady=self.__val(w, 'pady')
                                 )

    def menu_help(self):
        messagebox.showinfo("Help", self.help_text)

    def __search_keypress(self, _):
        text: str = self.components['txt_log'].get('1.0', 'end-1c')
        text_array = text.splitlines()
        try:
            # TODO include column position
            index = [i for i, s in enumerate(text_array) if self.components['frame_search'].get() in s]
            self.components['txt_log'].see(str(index[0] + 1)+'.0')

        except:
            pass

    def __tab_hotkeys(self, _):
        if self.components['frame_search'].winfo_ismapped():
            self.__set_flag('frame_search', False)
            self.__repack()

        else:
            self.__set_flag('frame_search', True)
            self.__repack()

    def __path_keypress(self, _):
        self.components['btn_generate'].config(
            state='normal' if os.path.isfile(self.components['entry_new_path'].get()) else 'disabled')

    def __set_directory(self):
        """
        Select directory for files.

        :return:
        """
        response = filedialog.askopenfilename(
            title="Select file", filetypes=(("Taglist", "*.csv"), ("all files", "*.*")))
        if response != '':
            self.components['entry_path_text'].set(response)
            # widget.xview_moveto(1.0)
            self.components['btn_generate'].config(state='normal')

    @staticmethod
    def interpret_file(file, delimiter=None, quotechar=None):
        """

        :return:
        """
        raw_file = open(file, 'r', newline='')
        eval_buffer = []
        for line in raw_file.readlines():
            if line.strip(' \t\r\n') and line[0] != '@':
                eval_buffer.append(line)
        interpreted_file = csv.reader(eval_buffer, delimiter=delimiter, quotechar=quotechar, skipinitialspace=True)
        return interpreted_file

    @staticmethod
    def get_timestamp():
        return datetime.now().strftime('_%Y-%m-%d_%Hh%M')


def main():
    try:
        TacoShell()

    except:
        traceback.print_exc()
        logging.basicConfig(filename='log.txt',
                            level=logging.DEBUG,
                            format='%(asctime)s',
                            datefmt='%m-%d %H:%M')
        logging.exception("message")


if __name__ == '__main__':
    main()