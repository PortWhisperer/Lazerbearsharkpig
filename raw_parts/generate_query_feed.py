#!/usr/bin/env python

import os
import csv
import sys
import time
import urllib
import json
import hashlib
import argparse

sys.path.insert(0, "../../")
from cbfeeds.feed import CbReport
from cbfeeds.feed import CbFeed
from cbfeeds.feed import CbFeedInfo
from urlencode import query_encoder


# parses queries from CSV file & raw_input
def get_queries(query_src, datatype):
    queries = []
    if datatype == 'csv':
        print "[*] Queries:\n-----------"
        try:
            with open(query_src) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    print row['query']
                    queries.append(row)
        except Exception:
            sys.stderr.write("[-] Error! Could not open %s\n" % query_src)
            exit(0)

    elif datatype == 'raw':
        print '\n[*] Query information:\n--------------------'
        q = {}
        q['query'] = query_src
        q['index_type'] = raw_input("Query Type (modules|events) :> ")
        q['title'] = raw_input("Report Title :> ")
        q['score'] = raw_input("Score (0-100) :> ")
        q['link'] = raw_input("Report Link :> ")
        queries.append(q)

    return queries


# takes parsed data and generates reports
def build_reports(queries):
    # generates one "report" per query
    reports = []

    for q in queries:
        m = hashlib.md5()
        m.update(q['link'] + q['title'])
        report_id = m.hexdigest()
        fields = {'iocs': {
                'query': [
                {
                    'index_type': q['index_type'],
                    'search_query': query_encoder(q['query'])
                }
            ]
        },
                'score': int(q['score']),
                'timestamp': int(time.mktime(time.gmtime())),
                'link': q['link'],
                'id': report_id,
                'title': q['title']
        }
        reports.append(CbReport(**fields))

    return reports

def get_feedhdr(feedhdrsrc):
    feedinfo = []
    print "[*] feedinfo:\n-----------"
    try:
        with open(feedhdrsrc) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print row['name']
                feedinfo.append(row)
    except Exception:
        sys.stderr.write("[-] Error! Could not open %s\n" % feedhdrsrc)
        exit(0)
    return feedinfo

# initializes and orchestrates query feed generation
def create(query_file, datatype,feedinfosrc=''):
    queries = get_queries(query_file, datatype)
    reports = build_reports(queries)
    if feedinfosrc:
    	feedhdrinfo = get_feedhdr(feedinfosrc)
        for q in feedhdrinfo:
            print q
            feedinfo = {'name': q['name'],
                    'category': q['category'],
                    'display_name': q['display_name'],
                    'provider_url': q['provider_url'],
                    'summary': q['summary'],
                    'tech_data': q['tech_data'],
                    'icon': q['icon'],
                    'icon_small': q['icon_small'],
		   }
    else:
    	feedinfo = {'name': 'queryfeed',
                'display_name': "Custom Query Feed",
                'provider_url': 'https://github.com/carbonblack/community',
                'summary': "This feed is a collection of custom search queries",
                'tech_data': "There are no requirements to share any data to receive this feed.",
                'icon': '',
                'icon_small': ''}

    # lazy way out to get right icon path.  sorry.
    old_cwd = os.getcwd()
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    print "got here",feedinfo

    feedinfo = CbFeedInfo(**feedinfo)
    feed = CbFeed(feedinfo, reports)
    created_feed = feed.dump()
    os.chdir(old_cwd)

    return created_feed

# boilerplate main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--feedinfosrc", '-f', type=str, help="Parses CSV for Intel feed information")
    parser.add_argument("--csv", '-c', type=str, help="Parses CSV for query feed information")
    parser.add_argument('--output', '-o', type=str, default="query_feed.txt", help="Specify output file. Default is query_feed.txt")
    args = parser.parse_args()

    if args.output:
        ofile = args.output

    if args.csv:
        datatype = 'csv'
        query_src = args.csv
	feed_src = args.feedinfosrc
    else:
        datatype = 'raw'
        query_src = raw_input('[*] Query:> ')

    # begin feed generation process
    reports = create(query_src, datatype,feed_src)
    # store generated feed in output file
    with open(ofile, 'w+') as out:
        out.write(reports)
    # relay success to user
    print "\n[+] Query Feed:\n---------------\n" + reports
    print "\n[+] Feed was written to %s" % ofile
