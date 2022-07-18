#!/bin/bash
uwsgi --daemonize2 /tmp/nodes_uwsgi.log --need-app --ini nodes_uwsgi.ini
/bin/bash

