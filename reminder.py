# -*- coding: utf-8 -*-
__author__ = "winking324@gmail.com"
__copyright__ = "Copyright (c) 2014-2017 winking.io, Inc."


import bs4
import json
import rumps
import datetime
import requests
import subprocess
from dateutil import parser


SOURCE_URL = 'https://xclient.info/s/{page}/'


class Reminder(rumps.App):
    def __init__(self):
        super(Reminder, self).__init__('Apps Update Reminder', icon='icon.icns')
        self.menu = ['Apps', 'CheckUpdate']

        self.settings = {}
        self.read_settings()

    def read_settings(self):
        with open('settings.json') as f:
            self.settings = json.load(f)

    def write_settings(self):
        with open('settings.json', 'wt') as f:
            json.dump(self.settings, f)

    @rumps.clicked('Apps')
    def preferences(self, _):
        setting_window = rumps.Window(
            message='Set apps you want to monitor update',
            title='Preferences',
            default_text=','.join(self.settings.get('apps', '')),
            ok="Submit",
            cancel='Cancel'
        )

        resp = setting_window.run()
        if resp.clicked:
            self.settings['apps'] = resp.text.split(',')
            self.write_settings()

    @rumps.clicked('CheckUpdate')
    def check_update(self, _):
        last_update_date = self.settings.get('date', '')
        if not last_update_date:
            last_update_date = datetime.datetime.today()
        else:
            last_update_date = parser.parse(last_update_date)

        if not self.settings['apps']:
            return

        page = 1
        try:
            while page > 0:
                response = requests.get(SOURCE_URL.format(page=page), timeout=10)
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                apps = soup.find('ul', class_='post_list row').find_all('a', title=True)
                for app in apps:
                    update_date = app.find('span', class_='item date')
                    app_update_date = parser.parse(update_date.text)
                    if app_update_date < last_update_date:
                        page = 0
                        break

                    app_href = app.attrs['href']
                    app_name = app_href[app_href.rfind('/') + 1:app_href.rfind('.')]
                    if app_name not in self.settings['apps']:
                        continue

                    # app_data = json.dumps()
                    rumps.notification(app_name, 'xclient.info', '{} updated on {}.'.format(app_name, update_date.text),
                                       data={'name': app_name, 'date': update_date.text, 'href': app_href})
                page += 1 if page > 0 else 0
        except Exception as e:
            rumps.alert('Check update failed! Exception: {}'.format(repr(e)))
            return

    @rumps.notifications
    def notification_center(self, info):
        subprocess.Popen(['open', info.data['href']], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        self.settings['date'] = datetime.datetime.today().strftime('%Y.%m.%d')
        self.write_settings()


if __name__ == '__main__':
    Reminder().run()

