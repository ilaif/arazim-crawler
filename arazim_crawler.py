#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Arazim Crawler

Description: A script that crawls arazim website for summaries, if a new summary is found, sends an email notification.
Usage:
1. pip install requirements: requests, beautifulsoup4
2. place script in desired folder
3. put it in crontab (crontab -e) with the contents (*/15 represents every 15 minutes):
ARAZIM_CRAWLER_SENDER_EMAIL="<your-email>"
ARAZIM_CRAWLER_SENDER_PASSWORD="<your-email-password>"
ARAZIM_CRAWLER_RECIPIENTS="<comma,separated,emails>"
*/15 * * * * cd <script-folder> && ./<script-file-name> 2>> <error-file-log-name>
4. done - wait for an email!
"""

from __future__ import print_function

# This is needed for crontab's environment
PYTHON_MODULES_PATH = '/usr/local/lib/python2.7/site-packages'

import sys; sys.path.append(PYTHON_MODULES_PATH)
from bs4 import BeautifulSoup
import requests
import json
import os.path
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import urllib2

# Config params
base_url = 'http://www.arazim-project.com'
recipients = os.getenv('ARAZIM_CRAWLER_RECIPIENTS', '').split(',')
courses = [
    {'name': 'Numerical Analysis', 'url': base_url + '/node/386', 'key': 'numerical_analysis'},
    {'name': 'Complexity', 'url': base_url + '/node/369', 'key': 'complexity'},
]
saved_lectures_path = 'saved_lectures.json'
sender_email = os.getenv('ARAZIM_CRAWLER_SENDER_EMAIL')
sender_password = os.getenv('ARAZIM_CRAWLER_SENDER_PASSWORD')

def run():
    ''' Main running program: Crawling for wanted courses and sends an email for new ones to recipients '''
    
    if not internet_on():
        eprint('Failed: No internet connection')
        sys.exit(1)

    # Initialize saved_lectures_ds
    saved_lectures = {}
    for course in courses:
        saved_lectures[course['key']] = {}
    if not os.path.exists(saved_lectures_path):
        eprint('WARNING: %s not found' % saved_lectures_path)
    else:
        with open(saved_lectures_path, 'r') as f:
            saved_lectures = json.load(f)

    print('')
    new_lectures = [];
    for course in courses:
        log('Course Name: %s' % course['name'])
        log('--------------------------------')

        r  = requests.get(course['url'])  # Fetch course url html text
        soup = BeautifulSoup(r.text, 'lxml')  # Parse it with BeautifulSoup

        # Find the link of each lecture summary
        for link in soup.select('.field-name-field-lesson-sum .field-items .field-item .field-name-field-sum .file a'):
            lecture_name = link.text[::-1].encode('utf-8')
            lecture_url = link.get('href')
            log('%s : %s' % (lecture_name, lecture_url))
            if lecture_url not in saved_lectures[course['key']]:  # We don't have it then mark it as new and save it.
                new_lectures.append((course['name'], link.text.encode('utf-8'), lecture_url))
                saved_lectures[course['key']][lecture_url] = {'name': lecture_name, 'url': lecture_url}

        print('')

    if len(new_lectures) > 0:
        log('New Lectures:')
        log('--------------------------------')
        new_lectures_str = '\n'.join(map(lambda (course_name, lecture_name, lecture_url): '%s: %s, url: %s' % (course_name, lecture_name, lecture_url), new_lectures))
        log(new_lectures_str)
        print('')

        res = send_email(sender_email, sender_password, recipients, '[Arazim] New Lectures Are Here!', new_lectures_str)
        if res:  # Only if sent successfully then save the new lectures so we won't send them again.
            with open(saved_lectures_path, 'w') as f:
                json.dump(saved_lectures, f, 4)
    else:
        log('No new lectures, not sending an email.')


def internet_on():
    ''' Check if internet is on'''
    try:
        urllib2.urlopen('http://google.com', timeout=1)
        return True
    except urllib2.URLError as err: 
        return False


def log(msg):
    print('%s, %s' % (datetime.datetime.now(), msg))


def eprint(*args, **kwargs):
    ''' Print a message to stderr '''
    print('%s,' % datetime.datetime.now(), *args, file=sys.stderr, **kwargs)


def send_email(user, pwd, recipient, subject, body):
    ''' Send an email to a list of recipients '''
    gmail_user = user
    gmail_pwd = pwd
    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    part1 = MIMEText(body, 'plain', 'utf-8')
    msg.attach(part1)
    message = msg.as_string().encode('ascii')

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        log('Successfully sent email')
        return True
    except BaseException as e:
        eprint('Failed to send email, err: %s' % e)
        return False


if __name__ == '__main__':
    run()
