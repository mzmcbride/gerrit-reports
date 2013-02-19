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

report_title = root_page + 'Open changesets by owner'
report_template = u'''\
Open changesets by owner.

{| class="wikitable sortable plainlinks"
|- style="white-space:nowrap;"
! Owner
! Changesets
%s
|}
'''

conn = sqlite3.connect(database_name)
cursor = conn.cursor()
cursor.execute('''
SELECT
  gc_owner,
  COUNT(*)
FROM changesets
WHERE gc_status = 'NEW'
GROUP BY gc_owner;
''')

output = []
for row in cursor.fetchall():
    table_row = u"""\
|-
| [https://gerrit.wikimedia.org/r/#/q/owner:%%22{{urlencode:%s}}%%22+status:open,n,z %s]
| %s""" % (row[0], row[0], row[1])
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
