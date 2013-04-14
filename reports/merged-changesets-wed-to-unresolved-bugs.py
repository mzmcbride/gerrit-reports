#! /usr/bin/env python
# Public domain; MZMcBride; 2013

import ConfigParser
import os
import re
import sqlite3
import urllib

import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.gerrit-reports.ini')])

database_name = config.get('gerrit-reports', 'database_name')
wiki_api_url = config.get('gerrit-reports', 'wiki_api_url')
root_page = config.get('gerrit-reports', 'wiki_root_page')

report_title = root_page + 'Merged changesets wed to unresolved bugs'
report_template = u'''\
%s

{| class="wikitable sortable plainlinks"
|- style="white-space:nowrap;"
! Bug
! Subject
! Changeset
%s
|}

%s
'''

def get_open_bugs():
    open_bugs = set()
    # This function is an abomination. The Bugzilla API is a monster, though.
    html_re = re.compile(r'<input type="hidden" name="id" value="(\d+?)"')
    base_bugzilla_url = 'https://bugzilla.wikimedia.org/buglist.cgi'
    # Params can't be passed as a dictionary due to duplicate keys.
    params = ['bug_status=UNCONFIRMED',
              'bug_status=NEW',
              'bug_status=ASSIGNED',
              'bug_status=REOPENED',
              'limit=0']
    url_contents = urllib.urlopen(base_bugzilla_url+
                                  '?'+'&'.join(params)).read()
    for line in url_contents.split('\n'):
        match = html_re.search(line)
        if match:
            open_bugs.add(int(match.group(1)))
    return open_bugs

open_bugs = get_open_bugs()

conn = sqlite3.connect(database_name)
cursor = conn.cursor()
cursor.execute('''
SELECT
  gc_number,
  gc_subject
FROM changesets
WHERE gc_status = 'MERGED'
AND gc_subject LIKE '%bug%';
''')

db_query_results = cursor.fetchall()

output = []
bug_re = re.compile(r'bug(\s+|#|:)?(\d{1,5})', re.I)

subject_bugs = set()
for row in db_query_results:
    gc_number = row[0]
    gc_subject = row[1]
    match = bug_re.search(gc_subject)
    if match:
        subject_bugs.add(int(match.group(2)))

for row in db_query_results:
    gc_number = row[0]
    gc_subject = row[1]
    match = bug_re.search(gc_subject)
    if match:
        if int(match.group(2)) in open_bugs:
            table_row = u"""\
|-
| [[bugzilla:%s|%s]]
| <nowiki>%s</nowiki>
| [[gerrit:%s|%s]]""" % (match.group(2),
                         match.group(2),
                         gc_subject,
                         gc_number,
                         gc_number)
            output.append(table_row)

wiki = wikitools.Wiki(config.get('gerrit-reports', 'wiki_api_url'))
wiki.login(config.get('gerrit-reports', 'wiki_username'),
           config.get('gerrit-reports', 'wiki_password'))

report = wikitools.Page(wiki, report_title)
report_text = report_template % (config.get('gerrit-reports',
                                            'wiki_header_template'),
                                 '\n'.join(output),
                                 config.get('gerrit-reports',
                                            'wiki_footer_template'))
report_text = report_text.encode('utf-8')
report.edit(report_text,
            summary=config.get('gerrit-reports', 'wiki_edit_summary'),
            bot=1)

cursor.close()
conn.close()
