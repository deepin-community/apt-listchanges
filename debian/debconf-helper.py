#!/usr/bin/python3
# vim:set fileencoding=utf-8 et ts=4 sts=4 sw=4:
# This file is shared between postinst and config

import configparser
import debconf
import os
import sys

PREFIX_SIZE=len('apt-listchannges')
DEFAULT_SEEN_DB='/var/lib/apt/listchanges.db'
SECTION='apt'

def _tmpl2Key(name):
    return name[PREFIX_SIZE:].replace('-', '_')

def _debug(*args):
    if 'APT_LISTCHANGES_DEBCONF_DEBUG' in os.environ:
        print(*args, file=sys.stderr)

def _handleString(cfgkey, config, template, db, fromConfig):
    _debug("handleString(", template, cfgkey, fromConfig, ")")
    if fromConfig:
        value = config.get(SECTION, cfgkey)
        if value == 'none': value = ''
        db.set(template, value)
    else:
        value = db.getString(template)
        if value == '': value = 'none'
        config.set(SECTION, cfgkey, value)

def _handleList(cfgkey, config, template, db, fromConfig):
    _debug("handleList(", template, cfgkey, fromConfig, ")")
    if fromConfig:
        value = config.get(SECTION, cfgkey)
        db.set(template, value.lower())
    else:
        value = db.getString(template)
        config.set(SECTION, cfgkey, value)

def _handleBoolean(cfgkey, config, template, db, fromConfig):
    value = config.getboolean(SECTION, cfgkey, fallback=None)
    _debug("handleBoolean(", template, cfgkey, fromConfig, "), old config value:", value)
    if fromConfig:
        db.set(template, str(value).lower())
    else:
        newvalue =  db.getBoolean(template)
        if value is None or value != newvalue:
            config.set(SECTION, cfgkey, str(newvalue).lower())

def _handleSeen(cfgkey, config, template, db, fromConfig):
    # The 'save-seen' is very special: a path in config file,
    # but in debconf is stored as boolean...
    value = config.get(SECTION, cfgkey, fallback=None)
    _debug("handleSeen(", template, cfgkey, fromConfig, "), old config value:", value)
    if fromConfig:
        db.set(template, str(value and value != 'none').lower())
    elif not db.getBoolean(template):
        value = 'none'
    elif not value or value == 'none':
        value = DEFAULT_SEEN_DB
    config.set(SECTION, cfgkey, value)



IDX_QUESTION_NUMBER = 0
IDX_PRIORITY        = 1
IDX_HANDLER         = 2
IDX_SKIP            = 3
IDX_CHECK           = 4

def _checkFrontend(frontend):
    if frontend == 'none':
        return True

    NAMES['apt-listchanges/confirm'][IDX_SKIP] = frontend == 'mail'
    return False

def _checkWhich(which):
    NAMES['apt-listchanges/no-network'][IDX_SKIP] = which == 'news'
    return False

def _checkEmailAddress(emailAddress):
    NAMES['apt-listchanges/email-format'][IDX_SKIP] = not emailAddress
    return False

NAMES = {'apt-listchanges/frontend'     : [1, debconf.MEDIUM, _handleList,    False, _checkFrontend],
         'apt-listchanges/which'        : [2, debconf.MEDIUM, _handleList,    False, _checkWhich],
         'apt-listchanges/no-network'   : [3, debconf.HIGH,   _handleBoolean, False, None],
         'apt-listchanges/email-address': [4, debconf.LOW,    _handleString,  False, _checkEmailAddress],
         'apt-listchanges/email-format' : [5, debconf.LOW,    _handleList,    False, None],
         'apt-listchanges/confirm'      : [6, debconf.LOW,    _handleBoolean, False, None],
         'apt-listchanges/headers'      : [7, debconf.LOW,    _handleBoolean, False, None],
         'apt-listchanges/reverse'      : [8, debconf.LOW,    _handleBoolean, False, None],
         'apt-listchanges/save-seen'    : [9, debconf.LOW,    _handleSeen,    False, None]
         }


def _updateDebconfFromConfig(config, db):
    _debug("updateDebconfFromConfig()")
    for tmpl, params in NAMES.items(): # don't need to be sorted
        cfgkey = _tmpl2Key(tmpl)
        if config.has_option(SECTION, cfgkey):
            params[IDX_HANDLER](cfgkey, config, tmpl, db, True)
            db.fset(tmpl, 'seen', 'true')

def _communicateWithDebconf(config, db, is_postinst):
    _debug("communicateWithDebconf(", is_postinst, ")")

    for tmpl, params in sorted(NAMES.items(), key = lambda x : x[1][IDX_QUESTION_NUMBER]):
        if params[IDX_SKIP]:
            _debug("skipping %s" % tmpl)
            continue

        if is_postinst: # store the value
            params[IDX_HANDLER](_tmpl2Key(tmpl), config, tmpl, db, False)
        else:  # ask for the value
            db.forceInput(params[IDX_PRIORITY], tmpl)
            if params[IDX_CHECK]:
                db.go()

        if params[IDX_CHECK]:
            value = db.get(tmpl)
            if params[IDX_CHECK](value):
                _debug("finishing on %s" % tmpl)
                return

    if not is_postinst:
        db.go()

def main(argv):
    if len(argv) < 3:
        print("Usage: script postinst|config config_file mainscript_params",
              file=sys.stderr)
        sys.exit(1)

    debconf.runFrontEnd()

    is_postinst = argv[1] == 'postinst' # otherwise it is config
    config_file = argv[2]
    _debug("apt-listchanges debconf script started(", is_postinst, config_file, ")")

    config = configparser.ConfigParser()
    config.read(config_file)

    if not config.has_section(SECTION):
        config.add_section(SECTION)

    try:
        output = os.fdopen(3, "wt")
    except Exception as ex:
        _debug("failed to open file descriptor 3", str(ex))
        output = sys.stdout

    db = debconf.Debconf(write=output)

    if not is_postinst:
        _updateDebconfFromConfig(config, db)

    _communicateWithDebconf(config, db, is_postinst)

    if is_postinst:
        with open(config_file + '.new', 'wt') as newfile:
            config.write(newfile, space_around_delimiters=False)
            os.fchmod(newfile.fileno(), 0o644)

if __name__ == "__main__":
    main(sys.argv)
    sys.exit(0)
