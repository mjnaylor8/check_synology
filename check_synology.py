#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import math
import easysnmp

AUTHOR = "Frederic Werner"
VERSION = 0.2
#0.2  Changes made to allow SNMP v2 access. Michael Naylor - 31 March 2020

parser = argparse.ArgumentParser()
parser.add_argument("hostname", help="the hostname", type=str)
#parser.add_argument("username", help="the snmp user name", type=str)
#parser.add_argument("authkey", help="the auth key", type=str)
#parser.add_argument("privkey", help="the priv key", type=str)
parser.add_argument("community", help="the community name", type=str)
parser.add_argument("mode", help="the mode", type=str, choices=["load", "real_memory", "swap_memory", "disk", "storage", "update", "status"])
parser.add_argument("-w", help="warning value for selected mode", type=int)
parser.add_argument("-c", help="critical value for selected mode", type=int)
args = parser.parse_args()

hostname = args.hostname
#user_name = args.username
#auth_key = args.authkey
#priv_key = args.privkey
community = args.community
mode = args.mode
warning = args.w
critical = args.c
state = 'OK'

try:

    session = easysnmp.Session(
        hostname=hostname,
        community=community,
        version=2)
#        version=3,
#        security_level="auth_with_privacy",
#        security_level="auth_without_privacy",
#        security_username=user_name,
#        auth_password=auth_key,
#        auth_protocol="MD5",
#        privacy_password=priv_key,
#        privacy_protocol="AES128")

except easysnmp.EasySNMPError as e:
    print(e)
    exit(-1)

def snmpget(oid):
    try:
        res = session.get(oid)
        return res.value
    except easysnmp.EasySNMPError as e:
        print(e)

# Walk the given OID and return all child OIDs as a list of tuples of OID and value
def snmpwalk(oid):
    res = []
    try:
        res = session.walk(oid)
    except easysnmp.EasySNMPError as e:
        print(e)
    return res


def exitCode():
    if state == 'OK':
        sys.exit(0)
    if state == 'WARNING':
        sys.exit(1)
    if state == 'CRITICAL':
        sys.exit(2)
    if state == 'UNKNOWN':
        sys.exit(3)

if mode == 'load':
    #set up variables for output and icinga performance
    #see performance rules here https://icinga.com/docs/icinga1/latest/en/perfdata.html
    output = ''
    perfdata = ' | '
    #get load data for 1, 5 and 15 mins
    load1 = str(float(snmpget('1.3.6.1.4.1.2021.10.1.5.1'))/100)
    load5 = str(float(snmpget('1.3.6.1.4.1.2021.10.1.5.2'))/100)
    load15 = str(float(snmpget('1.3.6.1.4.1.2021.10.1.5.3'))/100)

    if warning and warning < int(math.ceil(float(load1))):
        state = 'WARNING'
    if critical and critical < int(math.ceil(float(load1))):
        state = 'CRITICAL'

    output = (state + ' - Load average (1 min {:0.0f}% , 5 min {:0.0f}% , 15 min {:0.0f}% )'.format((float(load1)*100), (float(load5)*100), (float(load15)*100)))
    perfdata += ('Load_1min={:0.1f}% Load_5min={:0.1f}% Load_15min={:0.1f}%'.format((float(load1)*100), (float(load5)*100), (float(load15)*100)))

    #print(state + ' - load average (1 min, 5 min, 15 min): %s, %s, %s' % (load1, load5, load15), '| load1=%s' % load1, 'load5=%s' % load5, 'load15=%s' % load15)
    #print(state + ' - Load average (1 min, 5 min, 15 min): {:0.0f}% {:0.0f}% {:0.0f}%'.format((float(load1)*100), (float(load5)*100), (float(load15)*100)))
#          ' | load1=%s' % load1, 'load5=%s' % load5, 'load15=%s' % load15)
    print(output, perfdata)
    exitCode()

if mode == 'real_memory':
    #set up variables for output and icinga performance
    output = ''
    perfdata = '| '
    #get memory data  for real memory (note some memory is reserved and so percentage not based on total physical memory)
    #formatting of data changed to be similar to that of Synology Disk Manager software
    memory_total_real = float(snmpget('1.3.6.1.4.1.2021.4.5.0'))
    memory_free_real = float(snmpget('1.3.6.1.4.1.2021.4.6.0'))
    memory_total_free = float(snmpget('1.3.6.1.4.1.2021.4.11.0'))
    memory_shared = float(snmpget('1.3.6.1.4.1.2021.4.13.0'))
    memory_buffer = float(snmpget('1.3.6.1.4.1.2021.4.14.0'))
    memory_cached = float(snmpget('1.3.6.1.4.1.2021.4.15.0'))
    memory_used_real = memory_total_real - memory_buffer - memory_cached - memory_free_real
    memory_used_percent_real = memory_used_real / memory_total_real * 100

#    print(memory_total_real / 1024)
#    print('Free - ' + str(memory_total_free / 1024))
#    print('Total Real - ' + str(memory_total_real / 1024))
#    print('Total Free - ' + str(memory_free_real / 1024))
#    print('Shared - ' + str(memory_shared / 1024))
#    print('Buffer - ' + str(memory_buffer / 1024))
#    print('Cached - '  + str(memory_cached / 1024))

    if warning and int(memory_used_percent_real) > warning:
        state = 'WARNING'
    if critical and int(memory_used_percent_real) > critical:
        state = 'CRITICAL'

    output = (state + ' - {:0.1f}% '.format(memory_used_percent_real) + 'Used ({0:0.1f} MB out of {1:0.1f} MB)'.format((memory_used_real / 1024), (memory_total_real / 1024)))
    perfdata += ('Memory_Total={:0.1f}MB Memory_Used={:0.1f}MB Memory_Percent={:0.1f}%'.format((memory_total_real / 1024), (memory_used_real / 1024), memory_used_percent_real))
    print (output, perfdata)
    exitCode()

if mode == 'swap_memory':
    #set up variables for output and icinga performance
    output = ''
    perfdata = ' | '
    #get memory data  for swap memory
    memory_total_swap = float(snmpget('1.3.6.1.4.1.2021.4.3.0'))
    memory_free_swap = float(snmpget('1.3.6.1.4.1.2021.4.4.0'))

    memory_used_swap = memory_total_swap - memory_free_swap
    memory_used_percent_swap = memory_used_swap / memory_total_swap * 100

    if warning and int(memory_used_percent_swap) > warning:
        state = 'WARNING'
    if critical and int(memory_used_percent_swap) > critical:
        state = 'CRITICAL'

    output = (state + ' - {:0.1f}% '.format(memory_used_percent_swap) + 'Used ({0:0.1f} MB out of {1:0.1f} MB)'.format((memory_used_swap / 1024), (memory_total_swap / 1024)))
    perfdata += ('Memory_Total={:0.1f}MB Memory_Used={:0.1f}MB Memory_Percent={:0.1f}%'.format((memory_total_swap / 1024), (memory_used_swap / 1024), memory_used_percent_swap))

    print(output, perfdata)

    exitCode()

if mode == 'disk':
    maxDisk = 0
    output = ''
    perfdata = '| '
    for item in snmpwalk('1.3.6.1.4.1.6574.2.1.1.2'):
        i = item.oid.split('.')[-1]
        #fetched some additonal items for interest
        disk_name = item.value
        disk_id = snmpget('1.3.6.1.4.1.6574.2.1.1.2.' + str(i))
        disk_model = snmpget('1.3.6.1.4.1.6574.2.1.1.3.' + str(i))
        disk_type = snmpget('1.3.6.1.4.1.6574.2.1.1.4.' + str(i))
        disk_status_nr = snmpget('1.3.6.1.4.1.6574.2.1.1.5.' + str(i))
        disk_temp = snmpget('1.3.6.1.4.1.6574.2.1.1.6.' + str(i))
        status_translation = {
            '1': "Normal",
            '2': "Initialized",
            '3': "NotInitialized",
            '4': "SystemPartitionFailed",
            '5': "Crashed"
        }
        disk_status = status_translation.get(disk_status_nr)
        #disk_name = disk_name.replace(" ", "")

        if warning and warning < int(disk_temp):
            if state != 'CRITICAL':
                state = 'WARNING'
        if critical and critical < int(disk_temp) or int(disk_status_nr) == (4 or 5):
            state = 'CRITICAL'

        output += disk_name + ' - Status: ' + disk_status + ', Temperature: ' + disk_temp + 'C' + ', ID: ' +  disk_id + ', Model: ' + disk_model.strip() + ', Type: ' + disk_type + '\r'
        #Remove spaces from disk name for performance data
        disk_name = disk_name.replace(" ", "")
        perfdata += ' temperature_' + disk_name + '=' + disk_temp + 'C '
    print('%s\r %s %s' % (state, output, perfdata))
    exitCode()

if mode == 'storage':
    output = ''
    perfdata = '| '
    for item in snmpwalk('1.3.6.1.2.1.25.2.3.1.3'):
        i = item.oid.split('.')[-1]
        storage_name = item.value
        if storage_name.startswith("/volume"):
            allocation_units = snmpget('1.3.6.1.2.1.25.2.3.1.4.' + str(i))
            size = snmpget('1.3.6.1.2.1.25.2.3.1.5.' + str(i))
            used = snmpget('1.3.6.1.2.1.25.2.3.1.6.' + str(i))

            storage_size = int((int(allocation_units) * int(size)) / 1000000000)
            storage_used = int((int(used) * int(allocation_units)) / 1000000000)
            storage_free = int(storage_size - storage_used)
            storage_used_percent = int(storage_used * 100 / storage_size)

            if warning and warning < int(storage_used_percent):
                if state != 'CRITICAL':
                    state = 'WARNING'
            if critical and critical < int(storage_used_percent):
                state = 'CRITICAL'

            output += ' -  free space: ' + storage_name + ' ' + str(storage_free) + ' GB (' + str(storage_used) + ' GB of ' + str(storage_size) + ' GB used, ' + str(storage_used_percent) + '%)'
            perfdata += storage_name + '=' + str(storage_used) + 'GB ' + 'Used=' + str(storage_used_percent) + '%'
    print('%s %s %s' % (state, output, perfdata))
    exitCode()

if mode == 'update':
    output = ''
    perfdata = '| '
    update_status_nr = snmpget('1.3.6.1.4.1.6574.1.5.4.0')
    update_dsm_verison = snmpget('1.3.6.1.4.1.6574.1.5.3.0')
    status_translation = {
            '1': "Available",
            '2': "Unavailable",
            '3': "Connecting",
            '4': "Disconnected",
            '5': "Others"
        }

    if warning and 1 == int(update_status_nr):
        state = 'WARNING'
    if critical and [4|5] == int(update_status_nr):
        state = 'CRITICAL'

    update_status = status_translation.get(update_status_nr)
    output = (state + ' - DSM Version: %s, DSM Update: %s' % (update_dsm_verison, update_status))
    perfdata += 'DSM_update={}'.format(update_status_nr)
    print(output, perfdata)
    exitCode()

if mode == 'status':
    output = ''
    perfdata = '| '
    status_model = snmpget('1.3.6.1.4.1.6574.1.5.1.0')
    status_serial = snmpget('1.3.6.1.4.1.6574.1.5.2.0')
 #   status_temperature = snmpget('1.3.6.1.4.1.6574.1.2.0')

    status_system_nr = snmpget('1.3.6.1.4.1.6574.1.1.0')
    status_system_fan_nr = snmpget('1.3.6.1.4.1.6574.1.4.1.0')
    status_cpu_fan_nr = snmpget('1.3.6.1.4.1.6574.1.4.2.0')
    status_power_nr = snmpget('1.3.6.1.4.1.6574.1.3.0')

    status_translation = {
            '1': "Normal",
            '2': "Failed"
        }

    status_system = status_translation.get(status_system_nr)
    status_system_fan = status_translation.get(status_system_fan_nr)
    status_cpu_fan = status_translation.get(status_cpu_fan_nr)
    status_power = status_translation.get(status_power_nr)

  #  if warning and warning < int(status_temperature):
  #      state = 'WARNING'
  #  if critical and critical < int(status_temperature):
  #      state = 'CRITICAL'
  #  print(state + ' - Model: %s, S/N: %s, System Temperature: %s C, System Status: %s, System Fan: %s, CPU Fan: %s, Powersupply : %s' % (status_model, status_serial, status_temperature, status_system, status_system_fan, status_cpu_fan, status_power) )
    output = (state + ' - Model: %s, S/N: %s, System Status: %s, System Fan: %s, CPU Fan: %s, Powersupply: %s' % (status_model, status_serial, status_system, status_system_fan, status_cpu_fan, status_power) )
    print(output)

          #+ ' | system_temp=%sc' % status_temperature)
    exitCode()
