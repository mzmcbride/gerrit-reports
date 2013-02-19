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

report_title = root_page + 'Changesets by status'
report_template = u'''\
Changesets by status.

{| class="wikitable sortable"
|- style="white-space:nowrap;"
! Status
! Changesets
%s
|- class="sortbottom"
! Total
! %s
|}
'''

conn = sqlite3.connect(database_name)
cursor = conn.cursor()
cursor.execute('''
SELECT
  gc_status,
  COUNT(*)
FROM changesets
GROUP BY gc_status;
''')

total = 0
output = []
for row in cursor.fetchall():
    table_row = u"""\
|-
| %s
| %s""" % (row[0], row[1])
    total += int(row[1])
    output.append(table_row)

wiki = wikitools.Wiki(config.get('gerrit-reports', 'wiki_api_url'))
wiki.login(config.get('gerrit-reports', 'wiki_username'),
           config.get('gerrit-reports', 'wiki_password'))

report = wikitools.Page(wiki, report_title)
report_text = report_template % ('\n'.join(output), total)
report_text = report_text.encode('utf-8')
report.edit(report_text,
            summary=config.get('gerrit-reports', 'wiki_edit_summary'),
            bot=1)

cursor.close()
conn.close()
