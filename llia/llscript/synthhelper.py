# llia.llscript.synthhelper
# 2016.05.10
#

from __future__ import print_function

import llia.constants as con
from llia.llerrors import LliascriptParseError
from llia.llscript.lsutil import parse_positional_args, parse_keyword_args

class SynthHelper(object):

    def __init__(self, parser):
        self.parser = parser
        self.dispatch_table = parser.dispatch_table
        self.proxy = parser.proxy
        self._init_dispatch_table()
        self.current_synth = ""

    def _init_dispatch_table(self):
        self.dispatch_table["efx"] = self.add_efx
        self.dispatch_table["synth"] = self.add_synth
        self.dispatch_table["with-synth"] = self.with_synth
        self.dispatch_table["ping-synth"] = self.ping_synth
        self.dispatch_table["abus>"] = self.assign_audio_bus
        self.dispatch_table["cbus>"] = self.assign_control_bus
    
    def status(self, msg):
        self.parser.status(msg)

    def warning(self, msg):
        self.parser.warning(msg)
        
    def update_prompt(self):
        self.parser.update_prompt()

    def assert_current_synth(self):
        if not self.current_synth:
            msg = "No current synth selected."
            self.warning(msg)
            return False
        else:
            return True
        
    # Split synth_Id string in form "stype_n" into components (stype, n)
    # 
    def parse_sid(self, sid=None):
        sid = sid or self.current_synth
        pos = sid.rfind('_')
        if pos > -1:
            haed, tail = sid[:pos], sid[pos+1:]
        else:
            head, tail = sid, ""
        return (head, tail)

    def get_synth(self, sid=None):
        sid = sid or self.current_synth
        rs = self.proxy.get_synth(sid or self.current_synth)
        return rs
    
    def synth_exists(self, sid):
        return self.proxy.synth_exists(nil, nil, sid)

    def synth_proxy(self, sid=None):
        sid = sid or self.current_synth
        return self.proxy.synth_proxy[sid]
    
    def audio_bus_exists(self, bname):
        return self.proxy.audio_bus_exists(bname)

    def control_bus_exists(self, bname):
        return self.proxy.control_bus_exists(bname)
        
    def buffer_exists(self, bname):
        return self.proxy.buffer_exists(bname)

    
    # synth stype id_ [:keymode km][:voice-count vc]
    #                 [:outbus busName][:outbus-offset n][:outbus-param param]
    def add_synth(self, tokens):
        args = parse_keyword_args(tokens,
                                             ["str", "str", "int"],
                                             [":keymode", ":voice-count",
                                              ":outbus", ":outbus-offset",
                                              ":outbus-param"],
                                             {":keymode" : ["str", "Poly1"],
                                              ":voice-count" : ["int", 8],
                                              ":outbus" : ["str", "out_0"],
                                              ":outbus-offset" : ["int", 0],
                                              ":outbus-param" : ["str", "outbus"]})
        cmd, stype, id_, keymode, voice_count, obusName, obusOffset, obusParam = args
        sid = "%s_%d" % (stype, id_)
        if stype not in con.SYNTH_TYPES:
            msg = "Unknown synth type: '%s'" % stype
            self.warning(msg)
            return False
        if keymode not in con.KEY_MODES:
            msg = "Invalid keymode: '%s'" % keymode
            self.warning(msg)
            return False
        if self.proxy.synth_exists(stype, id_):
            msg = "Synth %s already exists" % sid
            self.warning(msg)
            return False
        if not self.proxy.audio_bus_exists(obusName):
            msg = "Audio bus '%s' does not exists" % obusName
            self.warning(msg)
            return False
        rs = self.proxy.add_synth(stype, id_, keymode, voice_count)
        if rs:
            self.proxy.assign_synth_audio_bus(stype, id_, obusParam, obusName, obusOffset)
            self.current_synth = sid
            self.update_prompt()
        return rs
    
    # efx stype id_ inbus [:outbus name][:outbus-offset n][:outbus-param p]
    #                     [:inbus-offset n][:inbus-param p]
    def add_efx(self, tokens):
        req_args = ["str", "str", "int", "str"]
        key_arg_order =  [":outbus", ":outbus-offset",":outbus-param", 
                          ":inbus-offset",":inbus-param"]
        key_args = {":outbus" : ["str", "out_0"],
                    ":outbus-offset" : ["int", 0],
                    ":outbus-param" : ["str", "outbus"],
                    ":inbus-offset" : ["int", 0],
                    ":inbus-param" : ["str", "inbus"]}
        args = parse_keyword_args(tokens,
                                             req_args,
                                             key_arg_order,
                                             key_args)
        cmd, stype, id_, ibs, obs, oboff, obprm, iboff, ibprm = args
        sid = "%s_%d" % (stype, id_)
        if stype not in con.EFFECT_TYPES:
            msg = "Unknown EFX synth type: '%s'" % stype
            self.warning(msg)
            return False
        if self.proxy.synth_exists(stype, id_):
            msg = "Synth %s already exists" % sid
            self.warning(msg)
            return False
        for bs in (obs, ibs):
            if not self.proxy.audio_bus_exists(bs):
                msg = "Audio bus '%s' does not exists" % bs
                self.warning(msg)
                return False
        rs = self.proxy.add_efx(stype, id_)
        if rs:
            self.proxy.assign_synth_audio_bus(stype, id_, obprm, obs, oboff)
            self.proxy.assign_synth_audio_bus(stype, id_, ibprm, ibs, iboff)
            self.current_synth = sid
            self.update_prompt()
        return rs

    # with stype id_
    # Select synth for editing.
    #
    def with_synth(self, tokens):
        args = parse_positional_args(tokens,["str", "str", "int"])
        cmd, stype, id_ = args
        sid = "%s_%d" % (stype, id_)
        if self.proxy.synth_exists(stype, id_):
            self.current_synth = sid
            msg = "Using synth '%s'" % sid
            self.status(msg)
            self.update_prompt()
            return True
        else:
            msg = "Synth '%s' does not exists" % sid
            self.warning(msg)
            return False

    def ping_synth(self, *_):
        if self.assert_current_synth():
            sp = self.get_synth()
            if sp:
                sp.x_ping()
                return True
            else:
                return False
        else:
            return False
        
    def dump_synth(self, *_):
        rs = self.ping_synth()
        if rs:
            sp = self.get_synth()
            sp.x_dump()
            sp.dump()
        return rs

    # cmd bus-name param [offset]
    #
    def assign_audio_bus(self, tokens):
        if self.assert_current_synth():
            req = ["str", "str", "str"]
            opt = [["int", 0]]
            args = parse_positional_args(tokens, req, opt)
            cmd, bname, param, offset = args
            if not self.proxy.audio_bus_exists(bname):
                msg = "Audio bus '%s' does not exists." % bname
                self.warning(msg)
                return False
            sp = self.get_synth()
            stype, id_ = sp.synth_format, sp.id_
            self.proxy.assign_synth_audio_bus(stype, id_, param, bname, offset)
            return True
        else:
            return False
            
    # cmd bus-name param [offset]
    #
    def assign_control_bus(self, tokens):
        if self.assert_current_synth():
            req = ["str", "str", "str"]
            opt = [["int", 0]]
            args = parse_positional_args(tokens, req, opt)
            cmd, bname, param, offset = args
            if not self.proxy.control_bus_exists(bname):
                msg = "Control bus '%s' does not exists." % bname
                self.warning(msg)
                return False
            sp = self.get_synth()
            stype, id_ = sp.synth_format, sp.id_
            self.proxy.assign_synth_control_bus(stype, id_, param, bname, offset)
            return True
        else:
            return False
