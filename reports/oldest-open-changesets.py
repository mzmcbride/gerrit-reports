#! /usr/bin/env python
# Public domain; MZMcBride; 2013

import ConfigParser
import os
import sqlite3

import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.gerrit-reports.ini')])

database_name = config.get('gerrit-reports', 'database_name')
wiki_api_url = config.get('gerrit-reports', 'wiki_api_url')
root_page = config.get('gerrit-reports', 'wiki_root_page')

report_title = root_page + 'Oldest open changesets'
report_template = u'''\
Oldest open changesets.

{| class="wikitable sortable"
|- style="white-space:nowrap;"
! Changeset
! Project
! Created
! Owner
%s
|}
'''

conn = sqlite3.connect(database_name)
cursor = conn.cursor()
cursor.execute('''
SELECT
  gc_number,
  gc_project,
  gc_created,
  gc_owner
FROM changesets
WHERE gc_status = 'NEW'
ORDER BY gc_created ASC
LIMIT 200;
''')

output = []
for row in cursor.fetchall():
    table_row = u"""\
|-
| [[gerrit:%s|%s]]
| %s
| %s
| %s""" % (row[0], row[0], row[1], row[2].split(' ', 1)[0], row[3])
    output.append(table_row)

wiki = wikitools.Wiki(config.get('gerrit-reports', 'wiki_api_url'))
wiki.login(config.get('gerrit-reports', 'wiki_username'),
           config.get('gerrit-reports', 'wiki_password'))

report = wikitools.Page(wiki, report_title)
report_text = report_template % ('\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text,
            summary=config.get('gerrit-reports', 'wiki_edit_summary'),
            bot=1)

cursor.close()
conn.close()
