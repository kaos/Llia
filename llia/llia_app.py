# llia.llia_app
# 2016.04.23
#

from __future__ import (print_function)
import abc, sys, thread

# import llia.gui.splash
from llia.proxy import LliaProxy
from llia.midi_receiver import get_midi_receiver
from llia.keytab.registry import KeyTableRegistry
from llia.gui.appwindow import create_application_window
from llia.lliascript.lliascript import lliascript_parser
import llia.constants as con


class LliaApp(object):

    def __init__(self, config, skip_mainloop=False):
        super(LliaApp, self).__init__()
        self.config = config
        self._main_window = create_application_window(self)
        logfile_name = config.log_file()
        self.logfile = None
        if logfile_name:
            try:
                self.logfile = open(logfile_name, 'w')
                print("Llia logfile: '%s'" % logfile_name)
            except IOError:
                msg = "Can not open log file '%s'" % logfile_name
                self.warning(msg)
        if not self.logfile:
            print("No log file specified")
        print(logfile_name)
        self.proxy = LliaProxy(config, self)
        midi_in_trace = config.trace_midi_reception_enabled()
        midi_in_port = config["midi-receiver-name"]
        self.midi_receiver = get_midi_receiver(midi_in_port,midi_in_trace)
        self.keytables = KeyTableRegistry()
        self._repl_thread = None
        self.ls_parser = lliascript_parser(self)
        if not skip_mainloop:
            self.start_main_loop()
        
    def global_osc_id(self):
        return self.config.global_osc_id()

    def log_event(self, msg):
        if self.logfile:
            self.logfile.write(msg+'\n')
    
    def exit_(self, xcode=0):
        if xcode != 0:
            self.status("Llia exits with code %s" % xcode)
        else:
            self.status("Exit...")
        if self.logfile:
            self.logfile.close()
        self._main_window.exit_gui()
        self.ls_parser.exit_repl = True
        sys.exit(xcode)

    def status(self, msg):
        lgmsg = "Status oscID %s : %s" % (self.global_osc_id(), msg)
        self.log_event(lgmsg)
        self._main_window.status(msg)
    
    def warning(self, msg):
        lgmsg = "WARNING /Llia/%s : %s" % (self.global_osc_id(), msg)
        self.log_event(lgmsg)
        self._main_window.warning(msg)
    
    def error(self, errnum, msg, exception=None):
        acc = "ERROR: errnum = %s\n" % errnum
        acc += "ERROR: global OSC ID is '%s'\n" % self.global_osc_id()
        for line in msg.split("\n"):
            acc += "ERROR: %s\n" % line
        if exception:
            acc += "%s %s" % (type(exception), exception.message)
        self.log_event(acc)
        print(acc)
        self.exit(errnum)

    # def start_main_loop(self):
    #     self._repl_thread = threading.Thread(target = self.ls_parser.repl)
    #     self._repl_thread.start()
    #     self._main_window.start_gui_loop()


    def start_main_loop(self):
        self._repl_thread = thread.start_new_thread(self.ls_parser.repl, ())
        #self._repl_thread.start()
        self._main_window.start_gui_loop()

    # ISSUE: FIX ME  update all GUI windows.
    def sync_all(self):
        self.proxy.sync_to_host()
        # print("LliaApp.sync_all is not compleatly implemented")