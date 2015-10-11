import os
import sys
from ConfigParser import ConfigParser
from datetime import datetime

import requests
import rumps
import simplejson
from dateutil.parser import parser
from dateutil.tz import tzlocal

date_parser = parser()

NIGHTSCOUT_URL = '/api/v1/entries.json?count=100'
UPDATE_FREQUENCY_SECONDS = 20
MAX_SECONDS_TO_SHOW_DELTA = 600
HISTORY_LENGTH = 3
MAX_BAD_REQUEST_ATTEMPTS = 3

################################################################################
# Display options

MENUBAR_TEXT = "{sgv} ({direction}) [{time_ago}]"
MENU_ITEM_TEXT = "{sgv} [{time_ago}]"

def time_ago(date_str):
    seconds = int((datetime.now().replace(tzinfo=tzlocal()) - date_parser.parse(date_str)).total_seconds())
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

    def __init__(self, app_name):
        self.config_path = os.path.join(rumps.application_support(app_name), self.FILENAME)
        self.config = ConfigParser()
        self.config.read([self.config_path])
        if not self.config.has_section(self.SECTION):
            self.config.add_section(self.SECTION)
        if not self.config.has_option(self.SECTION, self.HOST):
            self.set_host('')

    def get_host(self):
        return self.config.get(self.SECTION, self.HOST)

    def set_host(self, host):
        self.config.set(self.SECTION, self.HOST, host)
        with open(self.config_path, 'w') as f:
            self.config.write(f)

def update_menu(title, items):
    app.title = title
    app.menu.clear()
    app.menu.update(items + last_updated_menu_items() + post_history_menu_options() + [app.quit_button])

def last_updated_menu_items():
    return [
        None,
        "Updated %s" % datetime.now().strftime("%a %H:%M %p"),
    ]

def post_history_menu_options():
    return [
        None,
        rumps.MenuItem('Configuration', callback=configuration_window),
        None,
    ]

def get_entries(retries=0, last_exception=None):
    if retries >= MAX_BAD_REQUEST_ATTEMPTS:
        print "Retried too many times: %s" % last_exception
        raise NightscoutException(last_exception)

    try:
        resp = requests.get(config.get_host() + NIGHTSCOUT_URL)
    except requests.exceptions.ConnectionError, e:
        return get_entries(retries + 1, "Connection error")

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
    return filter(lambda e: e['type'] == 'sgv', entries)

def get_menubar_text(entries):
    bgs = filter_bgs(entries)
    last, second_to_last = bgs[0:2]
    if (date_parser.parse(last['dateString']) - date_parser.parse(second_to_last['dateString'])).total_seconds() <= MAX_SECONDS_TO_SHOW_DELTA:
        direction = ('+' if last['sgv'] >= second_to_last['sgv'] else '') + str(last['sgv'] - second_to_last['sgv'])
    else:
        direction = '?'
    return MENUBAR_TEXT.format(
        sgv=last['sgv'],
        direction=direction,
        time_ago=time_ago(last['dateString']),
    )

def get_history_menu_items(entries):
    return [
        MENU_ITEM_TEXT.format(
            sgv=e['sgv'],
            time_ago=time_ago(e['dateString'],
        ))
        for e in filter_bgs(entries)[1:HISTORY_LENGTH + 1]
    ]

@rumps.timer(UPDATE_FREQUENCY_SECONDS)
def update_data(sender):
    try:
        entries = get_entries()
    except NightscoutException, e:
        update_menu("<Can't connect to Nightscout!>", [e.message])
    else:
        try:
            update_menu(get_menubar_text(entries), get_history_menu_items(entries))
        except Exception, e:
            print "Error parsing Nightscout data: %s %s " % (e, simplejson.dumps(entries))
            update_menu("<Bad Nightscout data!>", [])

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

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--debug':
        rumps.debug_mode(True)
    app = rumps.App('Nightscout Menubar', title='<Connecting to Nightscout...>')
    app.menu = ['connecting...'] + post_history_menu_options()
    config = NightscoutConfig(app.name)
    app.run()
