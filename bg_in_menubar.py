import os
from ConfigParser import ConfigParser
from datetime import datetime
from dateutil.parser import parser
from dateutil.tz import tzlocal

import requests
import rumps

date_parser = parser()

NIGHTSCOUT_URL = '/api/v1/entries.json'
UPDATE_FREQUENCY = 20
MAX_SECONDS_TO_SHOW_DELTA = 600
HISTORY_LENGTH = 3

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

def get_bg_history_json():
    return filter(
        lambda e: e['type'] == 'sgv',
        requests.get(config.get_host() + NIGHTSCOUT_URL).json()
    )

def get_menubar_text(bgs):
    last, second_to_last = bgs[0:2]
    if (date_parser.parse(last['dateString']) - date_parser.parse(second_to_last['dateString'])).seconds <= MAX_SECONDS_TO_SHOW_DELTA:
        direction = ('+' if last['sgv'] >= second_to_last['sgv'] else '') + str(last['sgv'] - second_to_last['sgv'])
    else:
        direction = '?'
    return "{sgv} ({direction}) [{time_ago}]".format(
        sgv=last['sgv'],
        direction=direction,
        time_ago=pretty_time_ago(last['dateString']),
    )

def get_history_menu_items(bgs):
    return [
        '{sgv} [{time_ago}]'.format(
            sgv=e['sgv'],
            time_ago=pretty_time_ago(e['dateString'],
        ))
        for e in bgs[1:HISTORY_LENGTH + 1]
    ]

def pretty_time_ago(date_str):
    seconds = (datetime.now().replace(tzinfo=tzlocal()) - date_parser.parse(date_str)).seconds
    if seconds >= 3600:
        return "%s hr" % (seconds / 3600)
    elif seconds >= 60:
        return "%s min" % (seconds / 60)
    else:
        return "%s sec" % seconds

@rumps.timer(UPDATE_FREQUENCY)
def update_data(sender):
    try:
        bgs = get_bg_history_json()
        app.title = get_menubar_text(bgs)
        app.menu.clear()
        app.menu.update(get_history_menu_items(bgs) + post_history_menu_options() + [app.quit_button])
    except requests.exceptions.RequestException:
        app.title = "<Can't reach nightscout!>"
        app.menu.clear()
        app.menu.update(post_history_menu_options() + [app.quit_button])

def post_history_menu_options():
    return [
        None,
        rumps.MenuItem('Configuration', callback=configuration_window),
        None,
    ]

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
    app = rumps.App('Nightscout Menubar', title='loading...')
    app.menu = ['loading...'] + post_history_menu_options()
    config = NightscoutConfig(app.name)
    app.run()
