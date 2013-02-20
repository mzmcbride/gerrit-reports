#! /usr/bin/env python
# Public domain; MZMcBride; 2013

import ConfigParser
import operator
import os
import sqlite3

import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.gerrit-reports.ini')])

database_name = config.get('gerrit-reports', 'database_name')
wiki_api_url = config.get('gerrit-reports', 'wiki_api_url')
root_page = config.get('gerrit-reports', 'wiki_root_page')

report_title = root_page + 'Changesets by project'
report_template = u'''\
Changesets by project.

{| class="wikitable sortable plainlinks"
|- style="white-space:nowrap;"
! Project
! Abandoned
! New
! Merged
! Submitted
! Total
%s
|- class="sortbottom"
! Totals
! %s
! %s
! %s
! %s
! %s
|}
'''

conn = sqlite3.connect(database_name)
cursor = conn.cursor()
cursor.execute('''
SELECT
  gc_project,
  gc_status,
  COUNT(*)
FROM changesets
GROUP BY gc_project, gc_status
ORDER BY gc_project ASC;
''')

all_projects = set()
projects = {}
for row in cursor.fetchall():
    gc_project = row[0]
    gc_status = row[1]
    count = row[2]
    if gc_project not in all_projects:
        projects[gc_project] = {}
        projects[gc_project][gc_status] = count
    else:
        projects[gc_project][gc_status] = count
    all_projects.add(gc_project)

rows = []
grand_total = 0
for project, statuses in projects.iteritems():
    try:
        abandoned = statuses[u'ABANDONED']
    except KeyError:
        abandoned = 0
    try:
        new = statuses[u'NEW']
    except KeyError:
        new = 0
    try:
        merged = statuses[u'MERGED']
    except KeyError:
        merged = 0
    try:
        submitted = statuses[u'SUBMITTED']
    except KeyError:
        submitted = 0
    row_total = abandoned+new+merged+submitted
    grand_total += row_total
    rows.append([project,
                 abandoned,
                 new,
                 merged,
                 submitted,
                 row_total])

sorted_rows = sorted(rows, key=operator.itemgetter(0))

output = []
abandoned_total = 0
new_total = 0
merged_total = 0
submitted_total = 0
for row in sorted_rows:
    abandoned_total += row[1]
    new_total += row[2]
    merged_total += row[3]
    submitted_total += row[4]
    project_url = u'[https://gerrit.wikimedia.org/r/#/q/' + \
                  u'project:%s,n,z %s]' % (row[0], row[0])
    project_status_url = u'[https://gerrit.wikimedia.org/r/#/q/' + \
                         u'project:%s+status:%s,n,z %s]'
    table_row = u"""\
|-
| %s
| %s
| %s
| %s
| %s
| %s""" % (project_url,
           project_status_url % (row[0], 'abandoned', row[1]),
           project_status_url % (row[0], 'open', row[2]),
           project_status_url % (row[0], 'merged', row[3]),
           project_status_url % (row[0], 'submitted', row[4]),
           row[5])
    output.append(table_row)

wiki = wikitools.Wiki(config.get('gerrit-reports', 'wiki_api_url'))
wiki.login(config.get('gerrit-reports', 'wiki_username'),
           config.get('gerrit-reports', 'wiki_password'))

report = wikitools.Page(wiki, report_title)
report_text = report_template % ('\n'.join(output),
                                 abandoned_total,
                                 new_total,
                                 merged_total,
                                 submitted_total,
                                 grand_total)
report_text = report_text.encode('utf-8')
report.edit(report_text,
            summary=config.get('gerrit-reports', 'wiki_edit_summary'),
            bot=1)

cursor.close()
conn.close()
