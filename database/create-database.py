#! /usr/bin/env python
# Public domain; MZMcBride; 2013

import ConfigParser
import os
import sqlite3

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.gerrit-reports.ini')])

database_name = config.get('gerrit-reports', 'database_name')

conn = sqlite3.connect(database_name)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE changesets (
  gc_number integer primary key,
  gc_change_id text,
  gc_project text,
  gc_branch text,
  gc_status text,
  gc_subject text,
  gc_created text,
  gc_updated text,
  gc_owner text,
  gc_labels integer
);
''')
cursor.close()
conn.commit()
conn.close()
