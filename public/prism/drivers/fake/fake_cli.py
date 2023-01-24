#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023
Martin Guthrie

This CLI provides a linux CLI interface to Fake.
Use this CLI to test your hardware driver.

Example:  (note the starting folder)
martin@martin-staric2:~/git/scripts/public/prism/drivers/fake$ python3 fake_cli.py version
         fake_cli.py   INFO   57 version: Namespace(verbose=0, _cmd='version')
         fake_cli.py   INFO   59 0.2.0
         fake_cli.py   INFO   81 Success
             Fake.py   INFO   78 closing
martin@martin-staric2:~/git/scripts/public/prism/drivers/fake$ python3 fake_cli.py uid
         fake_cli.py   INFO   50 uid: Namespace(verbose=0, _cmd='uid')
         fake_cli.py   INFO   52 0878
         fake_cli.py   INFO   81 Success
             Fake.py   INFO   78 closing

"""
import logging
import argparse
from Fake import Fake

# global Fake object
fake = None


def parse_args():
    epilog = """
    Usage examples:
       python3 fake_cli.py version

    Getting Help for a command:
    $ python3 fake_cli.py version --help
      
    """
    parser = argparse.ArgumentParser(description='teensy4_cli',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-v", '--verbose', dest='verbose', default=0, action='count', help='Increase verbosity')

    subp = parser.add_subparsers(dest="_cmd", help='commands')

    uid_parser = subp.add_parser('uid')

    version_parser = subp.add_parser('version')

    # add new commands here...

    args = parser.parse_args()
    return args


def uid(args):
    logging.info("uid: {}".format(args))
    response = fake.unique_id()
    logging.info("{}".format(response))
    return True


def version(args):
    logging.info("version: {}".format(args))
    response = fake.version()
    logging.info("{}".format(response))
    return True


if __name__ == '__main__':
    args = parse_args()
    exit_code = 0

    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(filename)20s %(levelname)6s %(lineno)4s %(message)s')

    fake = Fake(loggerIn=logging)

    if args._cmd == 'uid':
        success = uid(args)

    elif args._cmd == 'version':
        success = version(args)

    if success:
        logging.info("Success")

    else:
        logging.error("Failed")
        exit_code = 1

    if fake:
        fake.close()

    exit(exit_code)
