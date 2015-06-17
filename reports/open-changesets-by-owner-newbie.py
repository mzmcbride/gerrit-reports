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

report_title = root_page + 'Open changesets by newbie owner'
report_template = u'''\
%s

{| class="wikitable sortable plainlinks"
|- style="white-space:nowrap;"
! Owner
! Changesets<br>(total)
! Changesets<br>(mediawiki/*)
! Changesets<br>(mediawiki/core)
! Changesets<br>(CR >= 0)
%s
|- class="sortbottom"
! Total
! %s
! %s
! %s
! %s
|}

%s
'''

conn = sqlite3.connect(database_name)
cursor = conn.cursor()
cursor.execute('''
SELECT
  gc_owner,
  COUNT(*) as open_total,
  SUM( gc_project LIKE 'mediawiki/%' ) as open_mediawiki,
  SUM( gc_project == 'mediawiki/core' ) as open_core,
  SUM( gc_labels > -1 ) as open_unreviewed
FROM changesets
WHERE gc_status = 'NEW'
AND gc_owner NOT IN (
  SELECT gc_owner
  FROM changesets
  WHERE gc_status = 'MERGED'
  GROUP BY gc_owner
  HAVING COUNT( gc_owner ) >= 5
)
GROUP BY gc_owner;
''')

output = []
open_total = 0
open_mediawiki = 0
open_core = 0
open_unreviewed = 0
for row in cursor.fetchall():
    table_row = u"""
|-
| %s
| [https://gerrit.wikimedia.org/r/#/q/{{urlencode:owner:"%s" status:open}},n,z %s]
| [https://gerrit.wikimedia.org/r/#/q/{{urlencode:owner:"%s" project:^mediawiki/.+ status:open}},n,z %s]
| [https://gerrit.wikimedia.org/r/#/q/{{urlencode:owner:"%s" project:mediawiki/core status:open}},n,z %s]
| [https://gerrit.wikimedia.org/r/#/q/{{urlencode:owner:"%s" status:open label:Code-Review>=0}},n,z %s]
""".strip() % (row[0],
               row[0], row[1],
               row[0], row[2],
               row[0], row[3],
               row[0], row[4])
    output.append(table_row)
    open_total += int(row[1])
    open_mediawiki += int(row[2])
    open_core += int(row[3])
    open_unreviewed += int(row[4])

wiki = wikitools.Wiki(config.get('gerrit-reports', 'wiki_api_url'))
wiki.login(config.get('gerrit-reports', 'wiki_username'),
           config.get('gerrit-reports', 'wiki_password'))

report = wikitools.Page(wiki, report_title)
report_text = report_template % (config.get('gerrit-reports',
                                            'wiki_header_template'),
                                 '\n'.join(output),
                                 open_total, open_mediawiki, open_core, open_unreviewed,
                                 config.get('gerrit-reports',
                                            'wiki_footer_template'))
report_text = report_text.encode('utf-8')
report.edit(report_text,
            summary=config.get('gerrit-reports', 'wiki_edit_summary'),
            bot=1)

cursor.close()
conn.close()
