interface_monitor
=================

Description
-----------

Monitors an interface's throughput in bps/pps via SSH in loop until terminated.

Handy for very quick, single-interface logging. You probably already have
everything monitored via SNMP but this is for those cases where maybe you don't
for something but need or want to start collecting some data immediately and
have SSH available.

Example
-------

Default is to store data in a tab-delimited CSV is it collects. This way can
still be easy to port into SQLite or something if needed but also just open up
in your text editor of choice (cough.. ``vim`` ) and get a good idea.

I'm a fan of ASCII tables so unless toggled off with ``--no-tables`` every
iteration it'll print the current outlook of the data in pretty table form to
stdout. Table will also abbreviate to K, M, and G for human-reading.
Abbreviating for M and G start at 10,000 (9999K -> 10M, 9999M -> 10G).

Enough talking, this is what output looks like::

    $ interface_monitor -c router.site-a.example.com -i Gi0/1 -o 7206.csv --interval 5
    Username: test
    Password: 

    INFO: Connecting to device ...

    # Time passes...

    +------------------------------+-------------+-------------+-------------+--------------+--------------+
    |  Datetime                    |  Interface  |  Input bps  |  Input pps  |  Output bps  |  Output pps  |
    +------------------------------+-------------+-------------+-------------+--------------+--------------+
    |  2015-03-31 17:28:47.714777  |  Gi0/1      |  997K       |  170        |  942K        |  170         |
    |  2015-03-31 17:28:54.219905  |  Gi0/1      |  995K       |  170        |  944K        |  170         |
    |  2015-03-31 17:29:00.724480  |  Gi0/1      |  994K       |  169        |  945K        |  169         |
    |  2015-03-31 17:29:07.228105  |  Gi0/1      |  996K       |  170        |  946K        |  170         |
    |  2015-03-31 17:29:13.737130  |  Gi0/1      |  998K       |  170        |  950K        |  170         |
    |  2015-03-31 17:29:20.246513  |  Gi0/1      |  996K       |  169        |  949K        |  169         |
    +------------------------------+-------------+-------------+-------------+--------------+--------------+
    2015-03-31 17:29:26.758981: Added row to CSV

    ^C
    $ cat 7206.csv
    2015-03-31 17:28:41.697558      iface   in_bps  pps     out_bps pps
    2015-03-31 17:28:47.714777      Gi0/1   997000  170     942000  170
    2015-03-31 17:28:54.219905      Gi0/1   995000  170     944000  170
    2015-03-31 17:29:00.724480      Gi0/1   994000  169     945000  169
    2015-03-31 17:29:07.228105      Gi0/1   996000  170     946000  170
    2015-03-31 17:29:13.737130      Gi0/1   998000  170     950000  170
    2015-03-31 17:29:20.246513      Gi0/1   996000  169     949000  169
    2015-03-31 17:29:26.755766      Gi0/1   995000  168     950000  168

As you can see, CSV also has a header. Instead of naming the header for
datetime, I just insert the datetime there to make the width match off the
start and I was just writing this for something quick anyway.

Usage
-----

For full usage, use ``--help``::

    $ interface_monitor --help
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

Platforms
---------

Currently just works on Cisco IOS, but would be trivial to make it work on
something else. I wrote a driver-like facility into it for that reason.

In the source, under the ``Platform`` class, there are only two things that
need added:

1. In the primary class namespace, there's a dictionary ``supported``. Each key
   of this dictionary should be a string that matches a Netmiko supported 
   platform with a value of a dictionary containting the command to be ran. %s 
   in the command string will be substituted for the interface.

   .. code:: python

       class Platform(object):
           '''Driver-like facility for getting platform commands and parsing

           Dictionary ``supported`` should have keys of NetMiko platform strings with
           dict values containing command to run for interface rates.
           '''
           supported = {
               'cisco_ios': {'command': 'show interface %s | i put rate'}
               }

        # --- Redacted --- #

2. A new method of _parse_X needs added under the class where X is the platform
   string. This method will recieve the command result as a string as the only
   argument (other than ``self``). Then whatever magic needed needs done so
   that it returns a dictionary that looks like:

   .. code:: python

       # --- Under class Platform ... --- # 
           def _parse_cisco_ios(self, output):
               input_, output_ = output.splitlines()
               return {
                   'input_bps': input_.split()[4],
                   'input_pps': input_.split()[6],
                   'output_bps': output_.split()[4],
                   'output_pps': output_.split()[6],
                   }

   I should probably just use a tuple instead and if it ever bothers me enough I
   will. So far, though, python's dict hash seems to keep the order for those
   key names.

Installation
------------

Get repo contents either by clone or zip and install with pip::

    cat requirements.txt | xargs -n 1 -L 1 pip install

