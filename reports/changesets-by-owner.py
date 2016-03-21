#! /usr/bin/env python
# Public domain; MZMcBride; 2015

import ConfigParser
import os
import sqlite3

import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.gerrit-reports.ini')])

database_name = config.get('gerrit-reports', 'database_name')
wiki_api_url = config.get('gerrit-reports', 'wiki_api_url')
root_page = config.get('gerrit-reports', 'wiki_root_page')

report_title = root_page + 'Changesets by owner'
report_template = u'''\
%s

{| class="wikitable sortable plainlinks"
|- style="white-space:nowrap;"
! Owner
! Changesets<br>(total)
! Changesets<br>(mediawiki/*)
! Changesets<br>(mediawiki/core)
%s
|- class="sortbottom"
! Total
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
  COUNT(*) as total,
  SUM( gc_project LIKE 'mediawiki/%' ) as open_mediawiki,
  SUM( gc_project == 'mediawiki/core' ) as open_core
FROM changesets
GROUP BY gc_owner
ORDER BY total DESC;
''')

output = []
open_total = 0
open_mediawiki = 0
open_core = 0
for row in cursor.fetchall():
    table_row = u"""
|-
| <span id="{{anchorencode:%s}}">%s</span>
| [https://gerrit.wikimedia.org/r/#/q/{{urlencode:owner:"%s"}},n,z %s]
| [https://gerrit.wikimedia.org/r/#/q/{{urlencode:owner:"%s" project:^mediawiki/.+}},n,z %s]
| [https://gerrit.wikimedia.org/r/#/q/{{urlencode:owner:"%s" project:mediawiki/core}},n,z %s]
""".strip() % (row[0], row[0],
               row[0], row[1],
               row[0], row[2],
               row[0], row[3])
    output.append(table_row)
    open_total += int(row[1])
    open_mediawiki += int(row[2])
    open_core += int(row[3])

wiki = wikitools.Wiki(config.get('gerrit-reports', 'wiki_api_url'))
wiki.login(config.get('gerrit-reports', 'wiki_username'),
           config.get('gerrit-reports', 'wiki_password'))

report = wikitools.Page(wiki, report_title)
report_text = report_template % (config.get('gerrit-reports',
                                            'wiki_header_template'),
                                 '\n'.join(output),
                                 open_total, open_mediawiki, open_core,
                                 config.get('gerrit-reports',
                                            'wiki_footer_template'))
report_text = report_text.encode('utf-8')
report.edit(report_text,
            summary=config.get('gerrit-reports', 'wiki_edit_summary'),
            bot=1)

cursor.close()
conn.close()
