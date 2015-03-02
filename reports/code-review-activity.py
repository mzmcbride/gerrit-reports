#! /usr/bin/env python
# CC-0; 2015

import ConfigParser
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.gerrit-reports.ini')])

database_name = config.get('gerrit-reports', 'database_name')
wiki_api_url = config.get('gerrit-reports', 'wiki_api_url')
root_page = config.get('gerrit-reports', 'wiki_root_page')

report_title = root_page + 'Code review activity'
report_template = u'''\
%s

<pre>
%s
</pre>

%s'''

output = os.system('curl -s ' + \
         # Fetch the logs of the gerrit and wikibugs feed
         'http://bots.wmflabs.org/~wm-bot/logs/%23mediawiki-feed/%23mediawiki-feed.tar.gz | ' + \
         # Extract everything
         'tar xzf - -O | ' + \
         # Filter gerrit lines from gr+rit-wm2?
         'grep "rit-wm" | ' + \
         # Exclude self-reviews, where the reviewer is after a control character and "10"
         'grep -Ev "CR.{0,3}[[:cntrl:]]10([^:]+):.+owner.+\1" | ' + \
         # Include only the name of the reviewer (and a little garbage)
         'grep -Eo "CR.+C:[^]]+" | ' + \
         # Do the ranking
         'sort | uniq -c | sort -nr | head -500 | ' + \
         # Make some of the labels easier to read
         'sed "s/03/+/" | sed "s/04-/-/"')

# TODO: Use subprocess
"""
output = subprocess.Popen(['curl', '-s', \
         # Fetch the logs of the gerrit and wikibugs feed
         '"http://bots.wmflabs.org/~wm-bot/logs/%23mediawiki-feed/%23mediawiki-feed.tar.gz"', \
         # Extract everything
         '|', 'tar', 'xzf', '-', '-O', \
         # Filter gerrit lines from gr+rit-wm2?
         '|', 'grep', 'rit-wm', \
         # Exclude self-reviews, where the reviewer is after a control character and "10"
         '|', 'grep', '-Ev', '"CR.{0,3}[[:cntrl:]]10([^:]+):.+owner.+\1"', \
         # Include only the name of the reviewer (and a little garbage)
         '|', 'grep', '-Eo', '"CR.+C:[^]]+"', \
         # Do the ranking
         '|', 'sort', '|', 'uniq', '-c', '|', 'sort', '-nr', '|', 'head', '-500', \
         # Make some of the labels easier to read
         '|', 'sed', '"s/03/+/"', '|', 'sed', '"s/04-/-/"'], shell=True)
"""

wiki = wikitools.Wiki(config.get('gerrit-reports', 'wiki_api_url'))
wiki.login(config.get('gerrit-reports', 'wiki_username'),
           config.get('gerrit-reports', 'wiki_password'))

report = wikitools.Page(wiki, report_title)
report_text = report_template % (config.get('gerrit-reports',
                                            'wiki_header_template'),
                                 output,
                                 config.get('gerrit-reports',
                                            'wiki_footer_template'))
report_text = report_text.encode('utf-8')
report.edit(report_text,
            summary=config.get('gerrit-reports', 'wiki_edit_summary'),
            bot=1)

cursor.close()
conn.close()
