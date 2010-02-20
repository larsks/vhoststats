=======================
Virtual Host Statistics
=======================

Overview
========

``vhoststats`` reads an Apache log file with virtual host information (the
``%v`` token in your ``CustomLog`` directive) and displays a dynamic bar
graph showing the activity of the busiest hosts (sorted by number of
requests or bytes transferred).

The output might look something like this::

  [2010/02/19 20:21:32] Hosts: 7 [Displayed: 7] Requests: 104                                                                                                     

  host1.companyA.com   [R:1         ]  #                                          
                       [B:3         ]                                             
  devel.internal       [R:1         ]  #                                          
                       [B:208       ]                                             
  host2.companyA.com   [R:1         ]  #                                          
                       [B:4499      ]                                             
  A-truncated-host-nam [R:10        ]  ############                               
                       [B:65380     ]  #                                          
  host1.companyB.com   [R:21        ]  ##########################                 
                       [B:166715    ]  ####                                       
  www.google.com       [R:32        ]  #################################
                       [B:1566614   ]  ####################################

Usage
=====

::

  Usage: vhoststats [options]

  Options:
    -h, --help            show this help message and exit
    -v VHOST_FIELD, --vhost-field=VHOST_FIELD
    -t TIME_FIELD, --time-field=TIME_FIELD
    -s SIZE_FIELD, --size-field=SIZE_FIELD
    -w WINDOW_SIZE, --window-size=WINDOW_SIZE
    -B, --bytes           
    -R, --requests        

*vhoststats* can read Apache log files in a variety of formats.  The
default configuration assumes you're using the standard ``combined``
format with the addition of the virtual host name at the beginning of each
log entry.  If your log is formatted differently, you can specify three
options to help *vhoststats* find the information it needs:

- ``-v``, ``--vhost-field`` -- The field index of the virtual host name.
- ``-t``, ``--time-field`` -- The field index of the datestamp.
- ``-s``, ``--size-field`` -- The field index of the byte count.

In the default log format::

  hostA.company.com0 10.10.100.100 - - [19/Feb/2010:15:24:56 -0500]
    "GET /publications/liu2002b.pdf HTTP/1.1" 404 223 "-"
    "msnbot/2.0b (+http://search.msn.com/msnbot.htm)" mod_deflate:-

The virtual host name is index 0, the datestamp is index 4, and the bytes
field is index 7.  Hopefully that makes it clear how we count fields.

By default, *vhoststats* keeps a five-minute running total of number of
requests and bytes transferred for reach virtual host.  You can change the
window size with the ``--window-size`` (``-w``) option.

You can sort hosts by bytes (``--bytes``, ``-B``), the default, or by
number of requests (``--requests``, ``-R``).

For more information
====================

- The vhostats project page on github:
  | http://github.com/larsks/vhoststats/
- My blog:
  | http://blog.oddbit.com/

