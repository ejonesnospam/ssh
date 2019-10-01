# ssh
Home Assistant Component SSH - 'Switch' and 'Sensor' Entities


######### Still in work ################

## Future
-- Develop common ssh codebase for sensor and switch

## Based on the SSH Sensor, developed by John Chasey, 
https://github.com/custom-components/sensor.ssh
https://community.home-assistant.io/t/ssh-sensor/75229


## Sample Configuration.yaml entry

switch:
  - platform: ssh2
    host: 192.168.0.1
    name: 'SSH Switch 1'
    username: !secret username
    password: !secret password
    key: !secret debx64a-1-key
    command_on: 'touch "/tmp/junk.tmp"'
    command_off: 'rm "/tmp/junk.tmp"'
    command_status: '[ -e "/tmp/junk.tmp" ] && echo on || echo off'



##
