
########## [+] Upgrade software packages and install necessary packages [+] ##########
apt-get update
apt-get dist-upgrade -y
apt-get install git screen python3 python3-pip -y
########## [-] Upgrade software packages and install necessary packages [-] ##########

########## [+] Clone source [+] ##########
git clone https://github.com/sht2017/AutoVPSDeploy.git
########## [-] Clone source [-] ##########

########## [+] Initialization [+] ##########
cd AutoVPSDeploy
########## [-] Initialization [-] ##########

########## [+] Install necessary python libs [+] ##########
pip3 install -r core_requirements.txt
########## [-] Install necessary python libs [-] ##########

########## [+] Run Setup [+] ##########
chmod +x deploy.py
./deploy.py
########## [-] Run Setup [-] ##########