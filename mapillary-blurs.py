#!/usr/bin/python3

# Copyright (C) 2016 Nicolás Alvarez <nicolas.alvarez@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''
Removes all blurs from all photos in a Mapillary sequence.
'''

import requests
import sys, os
import json
import argparse
import configparser

CLIENT_ID="YW9aTEQ5NUN1Q3pFV05MWFdOaWlodzpiM2RkMTZmNmVjZjk1OTNk"
API_ROOT="https://a.mapillary.com/v2/"
CONFIG_PATH=os.path.expanduser('~/.config/mapillary-blur.conf')

config = configparser.ConfigParser()
config.optionxform = lambda option: option

def do_unblur_sequence(args):
    config.read(CONFIG_PATH)
    if 'Auth' not in config or 'AccessToken' not in config['Auth']:
        print("Not logged in! Please run '%s login' first." % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    access_token = config['Auth']['AccessToken']

    seq_key = args.seq

    session = requests.session()
    session.headers = {
        'User-Agent': 'MassBlurDelete/0.1 (by nicolas17) ' + requests.utils.default_user_agent()
    }

    print("Fetching sequence {}".format(seq_key), file=sys.stderr)
    req = session.get(API_ROOT + "s/%s" % seq_key, params={"client_id": CLIENT_ID})
    assert(req.status_code == 200)
    obj = req.json()

    skipped = 0
    pending = 0
    other_users = 0
    no_blurs = 0
    blurs_removed = 0
    failures = []

    total = len(obj['keys'])
    for im_num, im_key in enumerate(obj['keys'], 1):
        if im_key in args.skip:
            skipped += 1
            print("[%d/%d] [%s] Skipping image" % (im_num, total, im_key), file=sys.stderr)
            continue
        req = session.get(API_ROOT + "im/%s/b" % im_key, params={"client_id": CLIENT_ID})
        if req.status_code != 200:
            print("[%d/%d] [%s] Retrieving blurs failed with status %d" % (im_num, total, im_key, req.status_code), file=sys.stderr)
            failures.append(im_key)
            continue
        im_json = req.json()
        if im_json['requesting_user'] is not None:
            pending += 1
            print("[%d/%d] [%s] Image already has pending blur requests, can't submit" % (im_num, total, im_key))
        elif im_json['user'] is not None:
            other_users += 1
            print("[%d/%d] [%s] Image already blurred by human. Skipping" % (im_num, total, im_key))
        elif len(im_json['bs']) == 0:
            no_blurs += 1
            print("[%d/%d] [%s] Image has no blurs, nothing to do" % (im_num, total, im_key))
        else:
            blurs_removed += 1
            print("[%d/%d] [%s] Removing all blurs from image..." % (im_num, total, im_key), end='', flush=True)
            req_post = session.post(API_ROOT + "im/%s/b" % im_key,
                    headers={'Authorization':'Bearer %s' % access_token, 'Content-Type': 'application/json'},
                    params={"client_id": CLIENT_ID},
                    data=json.dumps({'bs':[]})
            )
            if req_post.status_code != 200:
                print("[%d/%d] [%s] Unblurring failed with status %d" % (im_num, total, im_key, req.status_code), file=sys.stderr)
                failures.append(im_key)
                continue
            print()
    print("skipped: %d, already pending: %d, blurred by others: %d, no blurs: %d, blurs removed %d" % (skipped, pending, other_users, no_blurs, blurs_removed))
    if failures:
        print("Unblurring failed on the following images:")
        print(*failures, sep="\n")

def do_login(args):
    import webbrowser
    import wsgiref.simple_server
    import cgi

    have_code=False

    class NonLoggingRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
        def log_request(self, *args, **kwargs):
            pass

    def oauth_app(environ, start_response):
        nonlocal have_code
        if environ['PATH_INFO'] != '/mapillary-blur-utils/auth':
            start_response("404 Not Found", [('Content-Type', 'text/plain')])
            return [b"Not Found"]

        query_args = cgi.parse_qs(environ['QUERY_STRING'])

        message = 'Something went wrong!'
        if 'error_description' in query_args:
            message = ''.join(query_args['error_description'])
        elif 'access_token' in query_args:
            token = query_args['access_token'][0]
            config['Auth']={'AccessToken': token}
            with open(CONFIG_PATH, 'w') as configfile:
                config.write(configfile)

            message = 'Authentication succeeded, you may now close this tab and use the script.'
            have_code=True

        start_response("200 OK", [('Content-Type','text/plain; charset=utf8')])
        return [(message+'\n').encode('utf8')]

    server = wsgiref.simple_server.make_server('127.0.0.1', 15133, oauth_app, handler_class=NonLoggingRequestHandler)

    webbrowser.open("https://www.mapillary.com/connect?client_id={}&response_type=token&scope=public:write&redirect_uri=http://localhost:15133/mapillary-blur-utils/auth".format(CLIENT_ID))
    print("Waiting for access token from the browser... (Ctrl-C to exit)")

    while not have_code:
        server.handle_request()
    del server
    print("Authenticated.")

parser = argparse.ArgumentParser(description=__doc__)
subparsers = parser.add_subparsers(title="subcommands", metavar='command')
unblur_parser = subparsers.add_parser('unblur-seq',
        help='unblur sequence',
        description="Removes all blurs from all photos in a Mapillary sequence."
)
unblur_parser.add_argument("seq", help="ID of the Mapillary sequence")
unblur_parser.add_argument("--skip",
        help="Skip the given image ID in the sequence, keeping its blurs (can be specified multiple times)",
        action="append",
        metavar="IMAGEID",
        default=[]
)
unblur_parser.set_defaults(func=do_unblur_sequence)

login_parser = subparsers.add_parser('login',
        help='request access token to use this script',
        description="Authorizes this script to access Mapillary on behalf of the user. " +
            "Will open the default web browser where you can authorize the script, " +
            "and then store the access token for future use."
)
login_parser.set_defaults(func=do_login)

args = parser.parse_args()

if hasattr(args,'func'):
    args.func(args)
else:
    parser.print_help()
