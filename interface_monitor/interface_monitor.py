#!/bin/env python2.7

"""
interface_monitor

Description: Monitors an interface's I/O by sending commands in loop via SSH

Usage:
  interface_monitor -c <host> -i <interface> [options]

Options:
  -h --help                     Show this screen.
  -v --verbose                  Verbose output.
  -u <username>                 Username to login
  -p <password>                 Password to login
  -e <enable>                   Set enable password. Defaults to password.
  -i <interface>                Interface to monitor
  -c <host>                     Host to connect to
  -o <output>                   CSV to output to
  --platform <platform>         Platform to run this on. [default: cisco_ios]
  --interval <seconds>          Time in seconds to wait between checking again
  --no-table                    Disable printing table of results every
                                iteration.

"""

import sys
import os
import netmiko
import time
import datetime
import csv
import getpass
from prettytable import PrettyTable
from docopt import docopt


def table(csv_file):
    '''Generates table.

    Puts '*' in last row, first column and converts bps to Kbps.
    Assumes the first row is header and thus ignores
    '''
    with open(csv_file) as f:
        contents = f.read()
    x = PrettyTable(['Datetime',
                     'Interface',
                     'Input bps',
                     'Input pps',
                     'Output bps',
                     'Output pps'])
    x.padding_width = 2
    x.align = "l"
    for row in contents.splitlines()[1:]:
        new_row = row.split('\t')
        # Enumerate through the metrics and abbreviate as needed
        for i, metric in enumerate(new_row):
            # First two fields are date and interface, but if were to enumerate
            # through [2:], the index enumerate() returns wouldn't match the
            # full list
            if i in (0, 1):
                continue
            # Abbreviate Mega and Giga at 10M and 10G.
            giga = 10000000000  # 10 bil
            mega = 10000000  # 10 Mil
            kilo = 1000
            if int(metric) > giga:
                new_row[i] = str(int(metric)/giga) + 'G'
            if int(metric) > mega:
                new_row[i] = str(int(metric)/mega) + 'M'
            if int(metric) > kilo:
                new_row[i] = str(int(metric)/kilo) + 'K'
        x.add_row(new_row)
    return x


def normalize_path(path):
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def setup():
    args = docopt(__doc__, version=1.0)

    # Prompt for username and password if not provided
    # Default enable to provided password if not unset
    if not args['-u']:
        args['-u'] = raw_input('Username: ')
    if not args['-p']:
        args['-p'] = getpass.getpass()
    if not args['-e']:
        args['e'] = args['-p']
    print "\n"

    # Set output file to ``data.csv``
    # Will normalize path by expanding any variables and user strings
    if not args['-o']:
        args['-o'] = normalize_path('data.csv')
    else:
        args['-o'] = normalize_path(args['-o'])
    if os.path.exists(args['-o']):
            print "WARNING: File '%s' exists; Data will be appended." % \
                args['-o']
    else:
        # If new file, start with header for CSV
        with open(args['-o'], 'w') as f:
            f.write('%s\t%s\t%s\t%s\t%s\t%s\r\n' %
                    (str(datetime.datetime.now()),
                        'iface',
                        'in_bps',
                        'pps',
                        'out_bps',
                        'pps'))
    return args


class Platform(object):
    '''Driver-like facility for getting platform commands and parsing

    Dictionary ``supported`` should have keys of NetMiko platform strings with
    dict values containing command to run for interface rates.
    '''
    supported = {
        'cisco_ios': {'command': 'show interface %s | i put rate'}
        }

    def __init__(self, platform):
        if platform in self.supported.keys():
            self.platform = platform
        else:
            raise NotImplementedError('Unsupported platform: %s' % platform)

    def get_command(self, interface):
        '''Dynamically returns platform command'''
        return self.supported[self.platform]['command'] % interface

    def parse(self, output):
        '''Dynamically runs the platforms output method

        Platform _parse methods should return a dictionary that contains the
        following::

            input_bps
            input_pps
            output_bps
            output_pps

        '''
        method = '_parse_' + self.platform
        return getattr(self, method)(output)

    def _parse_cisco_ios(self, output):
        input_, output_ = output.splitlines()
        return {
            'input_bps': input_.split()[4],
            'input_pps': input_.split()[6],
            'output_bps': output_.split()[4],
            'output_pps': output_.split()[6],
            }


def connect(args):
    '''Connects to host with NetMiko and gather monitor data

    Takes the docopt args (dict) as only argument. Relies on ``Platform`` class
    to handle more dynamic should more platforms be added in the future.
    '''

    device = {
        'device_type': args['--platform'],
        'ip': args['-c'],
        'username': args['-u'],
        'password': args['-p'],
        'secret': args['-e'],
        'verbose': args['--verbose']
    }

    print "INFO: Connecting to device ..."
    SSHClass = netmiko.ssh_dispatcher(device_type=device['device_type'])
    conn = SSHClass(**device)

    # Instantiate class for platform and get command for interface
    platform = Platform(args['--platform'])
    command = platform.get_command(args['-i'])

    while True:
        result = conn.send_command(command)
        parsed_result = platform.parse(result)
        # Create CSV row
        csv_row = [datetime.datetime.now(),
                   args['-i']]
        csv_row.extend(parsed_result.values())
        with open(args['-o'], 'ab') as f:
            csv_file = csv.writer(f, delimiter='\t')
            csv_file.writerow(csv_row)
            if not args['--no-table']:
                print table(args['-o'])
            print "%s: Added row to CSV" % datetime.datetime.now()
        time.sleep(int(args['--interval']))


def main():

    args = setup()
    connect(args)

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
