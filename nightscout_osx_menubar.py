# -*- coding: utf-8 -*-
import os
import sys
import traceback
import webbrowser
from ConfigParser import ConfigParser
from datetime import datetime

import requests
import rumps
import simplejson

VERSION = '0.3.1'
APP_NAME = 'Nightscout Menubar'
PROJECT_HOMEPAGE = 'https://github.com/mddub/nightscout-osx-menubar'

NIGHTSCOUT_URL = '/api/v1/entries.json?count=100'
UPDATE_FREQUENCY_SECONDS = 20
MAX_SECONDS_TO_SHOW_DELTA = 600
HISTORY_LENGTH = 5
MAX_BAD_REQUEST_ATTEMPTS = 3
REQUEST_TIMEOUT_SECONDS = 2

################################################################################
# Display options

MENUBAR_TEXT = u"{sgv} {direction} {delta} [{time_ago}]"
MENU_ITEM_TEXT = u"{sgv} {direction} {delta} [{time_ago}]"

def time_ago(seconds):
    if seconds >= 3600:
        return "%s hr" % (seconds / 3600)
    elif seconds >= 60:
        return "%s min" % (seconds / 60)
    else:
        return "%s sec" % seconds

################################################################################

class NightscoutException(Exception): pass

class NightscoutConfig(object):
    FILENAME = 'config'
    SECTION = 'NightscoutMenubar'
    HOST = 'nightscout_host'
    USE_MMOL = 'use_mmol'

    def __init__(self, app_name):
        self.config_path = os.path.join(rumps.application_support(app_name), self.FILENAME)
        self.config = ConfigParser()
        self.config.read([self.config_path])
        if not self.config.has_section(self.SECTION):
            self.config.add_section(self.SECTION)
        if not self.config.has_option(self.SECTION, self.HOST):
            self.set_host('')
        if not self.config.has_option(self.SECTION, self.USE_MMOL):
            self.set_use_mmol(False)

    def get_host(self):
        return self.config.get(self.SECTION, self.HOST)

    def set_host(self, host):
        self.config.set(self.SECTION, self.HOST, host)
        with open(self.config_path, 'w') as f:
            self.config.write(f)

    def get_use_mmol(self):
        return bool(self.config.get(self.SECTION, self.USE_MMOL))

    def set_use_mmol(self, mmol):
        self.config.set(self.SECTION, self.USE_MMOL, 'true' if mmol else '')
        with open(self.config_path, 'w') as f:
            self.config.write(f)

config = NightscoutConfig(APP_NAME)

def maybe_convert_units(mgdl):
    return round(mgdl / 18.0, 1) if config.get_use_mmol() else mgdl

def update_menu(title, items):
    app.title = title
    app.menu.clear()
    app.menu.update(items + last_updated_menu_items() + post_history_menu_options() + [app.quit_button])

def last_updated_menu_items():
    return [
        None,
        "Updated %s" % datetime.now().strftime("%a %-I:%M %p"),
    ]

def post_history_menu_options():
    mgdl = rumps.MenuItem('mg/dL', callback=choose_units_mgdl)
    mgdl.state = not config.get_use_mmol()
    mmol = rumps.MenuItem('mmol/L', callback=choose_units_mmol)
    mmol.state = config.get_use_mmol()
    items = [
        None,
        [
            'Settings',
            [
                mgdl,
                mmol,
                None,
                rumps.MenuItem('Set Nightscout URL...', callback=configuration_window),
                rumps.MenuItem('Help...', callback=open_project_homepage),
                None,
                "Version {}".format(VERSION)
            ],
        ],
        None,
    ]
    return items

def get_entries(retries=0, last_exception=None):
    if retries >= MAX_BAD_REQUEST_ATTEMPTS:
        print "Retried too many times: %s" % last_exception
        raise NightscoutException(last_exception)

    try:
        resp = requests.get(
            config.get_host() + NIGHTSCOUT_URL,
            # For the sake of keeping this portable without adding a lot of complexity, don't verify SSL certificates.
            # https://github.com/kennethreitz/requests/issues/557
            verify=False,
            # Don't let bad connectivity cause the app to freeze
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout, e:
        # Don't retry timeouts, since the app is unresponsive while a request is in progress,
        # and a new request will be made in UPDATE_FREQUENCY_SECONDS seconds anyway.
        print "Timed out: %s" % repr(e)
        raise NightscoutException(repr(e))
    except requests.exceptions.RequestException, e:
        return get_entries(retries + 1, repr(e))

    if resp.status_code != 200:
        return get_entries(retries + 1, "Nightscout returned status %s" % resp.status_code)

    try:
        arr = resp.json()
        if type(arr) == list and (len(arr) == 0 or type(arr[0]) == dict):
            return arr
        else:
            return get_entries(retries + 1, "Nightscout returned bad data")
    except simplejson.scanner.JSONDecodeError:
        return get_entries(retries + 1, "Nightscout returned bad JSON")

def filter_bgs(entries):
    bgs = [e.copy() for e in entries if 'sgv' in e]
    for bg in bgs:
        bg['sgv'] = int(bg['sgv'])
    return bgs

def seconds_ago(timestamp):
    return int(datetime.now().strftime('%s')) - timestamp / 1000

def get_direction(entry):
    return {
        'DoubleUp': u'⇈',
        'SingleUp': u'↑',
        'FortyFiveUp': u'↗',
        'Flat': u'→',
        'FortyFiveDown': u'↘',
        'SingleDown': u'↓',
        'DoubleDown': u'⇊',
    }.get(entry.get('direction'), '-')

def get_delta(last, second_to_last):
    return ('+' if last['sgv'] >= second_to_last['sgv'] else u'−') + str(abs(maybe_convert_units(last['sgv'] - second_to_last['sgv'])))

def get_menubar_text(entries):
    bgs = filter_bgs(entries)
    last, second_to_last = bgs[0:2]
    if (last['date'] - second_to_last['date']) / 1000 <= MAX_SECONDS_TO_SHOW_DELTA:
        delta = get_delta(last, second_to_last)
    else:
        delta = '?'
    return MENUBAR_TEXT.format(
        sgv=maybe_convert_units(last['sgv']),
        delta=delta,
        direction=get_direction(last),
        time_ago=time_ago(seconds_ago(last['date'])),
    )

def get_history_menu_items(entries):
    bgs = filter_bgs(entries)
    return [
        MENU_ITEM_TEXT.format(
            sgv=maybe_convert_units(e['sgv']),
            delta=get_delta(e, bgs[i + 1]) if i + 1 < len(bgs) else '?',
            direction=get_direction(e),
            time_ago=time_ago(seconds_ago(e['date'])),
        )
        for i, e in enumerate(bgs)
    ][1:HISTORY_LENGTH + 1]

@rumps.timer(UPDATE_FREQUENCY_SECONDS)
def update_data(sender):
    entries = None
    try:
        try:
            entries = get_entries()
        except NightscoutException, e:
            if config.get_host():
                update_menu("<Can't connect to Nightscout!>", [e.message[:100]])
            else:
                update_menu("<Set Nightscout URL!>", [])
        else:
            update_menu(get_menubar_text(entries), get_history_menu_items(entries))
    except Exception, e:
        print "Nightscout data: " + simplejson.dumps(entries)
        print repr(e)
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb)
        update_menu("<Error>", [repr(e)[:100]])

def configuration_window(sender):
    window = rumps.Window(
        title='Nightscout Menubar Configuration',
        message='Enter your nightscout URL below.\n\nIt probably looks like:\nhttps://SOMETHING.azurewebsites.net',
    )
    window.default_text = config.get_host()
    window.add_buttons('Cancel')

    response = window.run()
    if response.clicked == 1:
        config.set_host(response.text.strip())
        update_data(None)

def open_project_homepage(sender):
    webbrowser.open_new(PROJECT_HOMEPAGE)

def choose_units_mgdl(sender):
    config.set_use_mmol(False)
    update_data(None)

def choose_units_mmol(sender):
    config.set_use_mmol(True)
    update_data(None)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--debug':
        rumps.debug_mode(True)
    app = rumps.App(APP_NAME, title='<Connecting to Nightscout...>')
    app.menu = ['connecting...'] + post_history_menu_options()
    app.run()
