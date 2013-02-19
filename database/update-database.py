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
    changes = []
    more_changes = False
    if sortkey:
        sortkey_param = '+sortkey_before:%s' % sortkey
    else:
        sortkey_param = ''
    params = '?q=status:%s' % status + sortkey_param+'&n=500'
    opener = urllib2.build_opener()
    # Set a user agent to avoid an "Authentication required" error
    opener.addheaders = [('User-Agent', 'gerrit-reports')]
    url_contents = opener.open(gerrit_api_url+'changes/' + params).read()
    # Strip first five bytes to avoid an XSSI protection
    valid_json = url_contents[5:]
    loaded_json = json.loads(valid_json)
    for i in loaded_json:
        try:
            i['_more_changes']
            more_changes = True
            sortkey = i['_sortkey']
        except KeyError:
            pass
        changes.append(i)
    return changes, sortkey

def get_cumulative_changes(gerrit_api_url, status):
    sortkey = ''
    sortkeys = []
    cumulative_changes = []
    while True:
        changes, sortkey = get_changes(gerrit_api_url, status, sortkey)
        cumulative_changes += changes
        if sortkey in sortkeys:
            break
        if not changes:
            break
        else:
            sortkey = sortkey
            sortkeys.append(sortkey)
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
    ''' , (change[u'_number'],
           change[u'change_id'],
           change[u'project'],
           change[u'branch'],
           change[u'status'],
           change[u'subject'],
           change[u'created'],
           change[u'updated'],
           change[u'owner'][u'name']))

cursor.close()
conn.commit()
conn.close()
