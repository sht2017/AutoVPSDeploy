#!/usr/bin/env bash

########## [+] Upgrade software packages and install necessary packages [+] ##########
apt-get update
apt-get dist-upgrade -y
apt-get install git screen python3 python3-pip python3-venv -y
########## [-] Upgrade software packages and install necessary packages [-] ##########

########## [+] Clone source [+] ##########
git clone https://github.com/sht2017/AutoVPSDeploy.git
########## [-] Clone source [-] ##########

########## [+] Initialization [+] ##########
cd AutoVPSDeploy
########## [-] Initialization [-] ##########

########## [+] Install necessary python libs [+] ##########
python3 -m venv .venv
.venv/bin/pip3 install -r core_requirements.txt
########## [-] Install necessary python libs [-] ##########

########## [+] Run Setup [+] ##########
.venv/bin/python3 ./deploy.py
########## [-] Run Setup [-] ##########