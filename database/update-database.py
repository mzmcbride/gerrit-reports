#! /usr/bin/env python
# Public domain; MZMcBride; 2013

import ConfigParser
import json
import os
import sqlite3
import urllib2

statuses = ['abandoned',
            'closed',
            'merged',
            'open',
            'reviewed',
            'submitted']

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.gerrit-reports.ini')])

database_name = config.get('gerrit-reports', 'database_name')
gerrit_api_url = config.get('gerrit-reports', 'gerrit_api_url')

def get_changes(gerrit_api_url, status, sortkey):
    changes = []
    if sortkey:
        sortkey_param = '&start=%d' % (sortkey * 500)
    else:
        sortkey_param = ''
    params = '?q=status:%s' % status + sortkey_param+'&n=500&o=LABELS'
    opener = urllib2.build_opener()
    # Set a user agent to avoid an "Authentication required" error
    opener.addheaders = [('User-Agent', 'gerrit-reports')]
    url = gerrit_api_url+'changes/'+params
    url_contents = opener.open(url).read()
    # Strip first five bytes to avoid an XSSI protection
    valid_json = url_contents[5:]
    loaded_json = json.loads(valid_json)
    for item in loaded_json:
        if '_more_changes' in item:
            next_iteration_sortkey += 1
        else:
            next_iteration_sortkey = False
        changes.append(item)
    return changes, next_iteration_sortkey

def write_changes(database_name, changes):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    for change in changes:
        try:
            label = change[u'labels'][u'Code-Review'][u'value']
        except:
            label = 0

        try:
            cursor.execute('''
        INSERT OR REPLACE INTO changesets
        (gc_number,
         gc_change_id,
         gc_project,
         gc_branch,
         gc_status,
         gc_subject,
         gc_created,
         gc_updated,
         gc_owner,
         gc_labels)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''', (change[u'_number'],
              change[u'change_id'],
              change[u'project'],
              change[u'branch'],
              change[u'status'],
              change[u'subject'],
              change[u'created'],
              change[u'updated'],
              change[u'owner'][u'name'],
              label))
        except KeyError:
            print(repr(change))

    cursor.close()
    conn.commit()
    conn.close()
    return

for status in statuses:
    sortkey = False
    while True:
        changes, returned_sortkey = get_changes(gerrit_api_url, status, sortkey)
        write_changes(database_name, changes)
        if not returned_sortkey:
            break
        else:
            sortkey = returned_sortkey
