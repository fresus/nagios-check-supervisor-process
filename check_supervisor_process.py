#!/usr/bin/env python
# Copyright (C) 2015 - Jesús A. Rodríguez

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import xmlrpclib
import sys
from optparse import OptionParser

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

supervisor_states = {
    'RUNNING': 'OK',
    'STOPPED': 'WARNING',
    'STOPPING': 'WARNING',
    'STARTING': 'WARNING',
    'EXITED': 'CRITICAL',
    'BACKOFF': 'CRITICAL',
    'FATAL': 'CRITICAL',
    'UNKNOWN': 'CRITICAL'
}

warning_levels = []
not_ok_processes = {}

parser = OptionParser()
parser.add_option('-p', '--process')
parser.add_option('-H', '--host', default='localhost')
parser.add_option('-P', '--port', default='9001')
parser.add_option('-s', '--socket')
opts, args = parser.parse_args()

if opts.socket:
    import supervisor.xmlrpc
    xmlrpc_server = xmlrpclib.Server('http://127.0.0.1', transport=supervisor.xmlrpc.SupervisorTransport(None, None, serverurl = 'unix://' + opts.socket))
else: 
    xmlrpc_server = xmlrpclib.Server("http://%s:%s/RPC2" % (opts.host, opts.port))

try:
    process_info = xmlrpc_server.supervisor.getAllProcessInfo()
except:
    print 'Could not get process info'
    sys.exit(UNKNOWN)

for process in process_info:
    if opts.process:
        if process['name'].startswith(opts.process) and supervisor_states[process['statename']] != 'OK':
            not_ok_processes.setdefault(process['statename'],set()).add(process['name'].split('_')[0])
    else:
        if supervisor_states[process['statename']] != 'OK':
            not_ok_processes.setdefault(process['statename'],set()).add(process['name'].split('_')[0])

if len(not_ok_processes) > 0:
    warning_levels = [ supervisor_states[state] for state in not_ok_processes ]
    if 'CRITICAL' in warning_levels:
        exit_code = CRITICAL
    elif 'WARNING' in warning_levels:
        exit_code = WARNING
    else:
        exit_code = UNKNOWN
    exit_message = '; '.join("%s: %s" % (statename, ', '.join(name for name in names)) for (statename, names) in not_ok_processes.iteritems())
else:
    exit_code = OK
    exit_message = 'All processes OK'

print exit_message
sys.exit(exit_code)

