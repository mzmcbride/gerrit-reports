#! /usr/bin/env python
# Public domain; MZMcBride; 2013

import ConfigParser
import json
import os
import sqlite3
import urllib2

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.gerrit-reports.ini')])

database_name = config.get('gerrit-reports', 'database_name')
gerrit_api_url = config.get('gerrit-reports', 'gerrit_api_url')

def get_changes(gerrit_api_url, status, sortkey):
    next_iteration_sortkey = None
    changes = []
    if sortkey:
        sortkey_param = '+sortkey_before:%s' % sortkey
    else:
        sortkey_param = ''
    params = '?q=status:%s' % status + sortkey_param+'&n=500'
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
            next_iteration_sortkey = item['_sortkey']
        changes.append(item)
    return changes, next_iteration_sortkey

def get_cumulative_changes(gerrit_api_url, status):
    sortkey = None
    cumulative_changes = []
    while True:
        changes, returned_sortkey = get_changes(gerrit_api_url, status, sortkey)
        cumulative_changes += changes
        if not returned_sortkey:
            break
        else:
            sortkey = returned_sortkey
    return cumulative_changes

total_changes = []
for status in ['abandoned',
               'closed',
               'merged',
               'open',
               'reviewed',
               'submitted']:
    cumulative_changes = get_cumulative_changes(gerrit_api_url, status)
    total_changes += cumulative_changes

conn = sqlite3.connect(database_name)
cursor = conn.cursor()

for change in total_changes:
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
     gc_owner)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    ''', (change[u'_number'],
          change[u'change_id'],
          change[u'project'],
          change[u'branch'],
          change[u'status'],
          change[u'subject'],
          change[u'created'],
          change[u'updated'],
          change[u'owner'][u'name']))
    except KeyError:
        print(repr(change))

cursor.close()
conn.commit()
conn.close()
