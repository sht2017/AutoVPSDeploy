#!/usr/bin/env python3
import requests  # Web lib
import os
import sys
import random
import string
import shutil
import socket
import subprocess
import logging
import re

logging.basicConfig(
    #format="\033[34m%(asctime)s\033[0m [%(levelname)s] %(message)s",
    format="\033[34m[%(levelname)s]\033[0m %(message)s",
    #datefmt="%Y-%m-%d %I:%M:%S",
    #datefmt="%I:%M:%S",
    level=logging.DEBUG)



class DeployKit:
    def __init__(self, domain_name: str) -> None:
        self.domain_name = domain_name
        self.ip = requests.get('https://checkip.amazonaws.com').text.strip()
        if socket.gethostbyname(self.domain_name) != self.ip:
            raise LookupError('The ip is not resolved to the address inputted. Try again in few minutes?')

    def shell(self, command) -> str:
        _process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8"
        )
        _result = []
        while _process.poll() == None:
            EMPTY_LINE = ["\n", " ", ""]
            #_stdout = _process.stdout.readline()
            _stdout = re.sub("\\n$", "", _process.stdout.readline())
            if _stdout not in EMPTY_LINE:
                _result.append(_stdout)
                logging.debug("\033[46;37m"+_stdout+"\033[0m")
                sys.stdout.write('\r')
        return _result

    def chmod(self,path:str):
        os.chmod(path, os.stat(path).st_mode | 0o111)

    def remove(self,path:str):
        try:
            os.remove(path)
        except:
            logging.warning('\033[33mRemove Failed\033[0m')
            pass

    def sys_update(self):
        logging.info("Updating system...")
        self.shell("apt-get update && apt-get dist-upgrade -y")

    def rc_local_enable(self):
        _RC_LOCAL_PATH = "/etc/rc.local"
        logging.info("Enabling rc.local")
        if not os.path.isfile(_RC_LOCAL_PATH):
            logging.debug("No rc.local found")
            with open(_RC_LOCAL_PATH, "w") as file:
                file.write("#!/bin/bash\nexit 0")
            self.chmod(_RC_LOCAL_PATH)
            logging.debug("rc-local file generated")
        else:
            logging.debug("rc-local file existed")
        self.shell("systemctl start rc-local && systemctl enable rc-local")
        logging.info("Enabled rc.local")
    
    def deploy_otp(self):
        _OTP_PATH = "/etc/otp"
        _RC_LOCAL_PATH = "/etc/rc.local"
        logging.info("Installing OTP service")
        try:
            shutil.rmtree(_OTP_PATH)
        except:
            pass
        shutil.copytree("scripts/otp", _OTP_PATH)
        self.chmod(f"{_OTP_PATH}/setup.py")
        self.chmod(f"{_OTP_PATH}/otp.py")
        logging.debug("Copied and inited OTP core files")
        self.shell(f"python3 -m venv {_OTP_PATH}/.venv")
        self.shell(f"{_OTP_PATH}/.venv/bin/pip3 install -r {_OTP_PATH}/otp_requirements.txt")
        logging.debug("Required python lib installed")
        self.shell(f"{_OTP_PATH}/.venv/bin/python3 {_OTP_PATH}/setup.py")
        with open(_RC_LOCAL_PATH, "r+") as file:
            _content = file.read()
            _content = _content.replace("\nexit 0", "")
            _content = _content.replace(f"\nscreen -dmS otp-service {_OTP_PATH}/.venv/bin/python3 {_OTP_PATH}/otp.py","")
            file.seek(0)
            file.write(f"{_content}\nscreen -dmS otp-service {_OTP_PATH}/.venv/bin/python3 {_OTP_PATH}/otp.py\nexit 0")
        logging.debug("rc.local is fine")
        self.shell("screen -dmS otp-service "+_OTP_PATH+"otp.py")
        logging.info("OTP service installed")

    def deploy_ssr(self):
        logging.info("Installing SSR")
        self.shell("apt-get install unzip libsodium-dev -y")
        # self.shell("update-alternatives --install /usr/bin/python python /usr/bin/python2")
        logging.debug("Requirements installed")
        with open("ssrpwd","w") as file:
            file.write(''.join(random.choice(string.ascii_letters+string.punctuation.replace("\"","").replace("\'","").replace("\\","")).replace(":","") for _ in range(128)))
        with open("domain","w") as file:
            file.write(self.domain_name)
        logging.debug("Config generated")
        self.chmod("./scripts/ssr/install.sh")
        logging.debug("Executing installation script")
        self.shell("./scripts/ssr/install.sh")
        logging.debug("Installation script finished processing")
        self.remove("ssrpwd")
        self.remove("domain")
        logging.debug("Config temporary files removed")
        shutil.copyfile("./scripts/ssr/.ssr.sh","/usr/local/bin/ssr")
        os.chmod("/usr/local/bin/ssr",751)
        logging.debug("Script copied")
        logging.info("SSR installed")

    def deploy_nginx(self):
        _SITES_AVAILABLE_PATH="/etc/nginx/sites-available/"
        _SITES_ENABLED_PATH="/etc/nginx/sites-enabled/"
        _CERTBOT_PATH="/snap/bin/certbot"
        _CERTBOT_LINK_PATH="/usr/bin/certbot"
        logging.info("Installing and configuring nginx and certbot")
        # self.shell("apt-get install libc6 libcrypt1 libpcre2-8-0 libssl3 zlib1g iproute2 nginx-common -y")
        # self.shell("apt-get --purge remove nginx-core nginx-extras nginx-light -y")
        # self.shell("dpkg -i nginx_1.24.0-2_amd64-stontymod.deb")
        self.shell("apt-get install nginx nginx-full snapd -y")
        logging.debug("Installing certbot")
        self.shell("snap install core && snap refresh core && snap install --classic certbot")
        self.remove(_CERTBOT_LINK_PATH)
        os.symlink(_CERTBOT_PATH,_CERTBOT_LINK_PATH)
        logging.debug("Certbot softlink created")
        self.remove(_SITES_AVAILABLE_PATH+self.domain_name)
        shutil.copyfile("./configs/nginx/nginx.conf",_SITES_AVAILABLE_PATH+self.domain_name)
        with open(_SITES_AVAILABLE_PATH+self.domain_name,"r+") as file:
            _content=file.read().replace("$HOSTNAME$",self.domain_name)
            file.seek(0)
            file.write(_content)
        self.remove(_SITES_ENABLED_PATH+self.domain_name)
        os.symlink(_SITES_AVAILABLE_PATH+self.domain_name,_SITES_ENABLED_PATH+self.domain_name)
        self.remove(_SITES_ENABLED_PATH+"default")
        self.remove(_SITES_AVAILABLE_PATH+"default")
        self.shell("ufw disable")
        self.shell("systemctl restart nginx.service && certbot certonly --nginx --non-interactive --agree-tos -m admin@stonty.com -d "+self.domain_name)
        with open(_SITES_AVAILABLE_PATH+self.domain_name,"r+") as file:
            _content=file.read().replace("default_server http2","default_server ssl http2").replace("#ssl_certificate","ssl_certificate").replace("listen 80","listen 20080").replace("listen 443","listen 20443")
            file.seek(0)
            file.write(_content)
        self.shell("systemctl restart nginx.service")

def inputInterrupt() -> None:
    print("Press Enter to the next step.")
    if input()!="":
        exit()

if __name__ == "__main__":
    print("Please enter the hostname (Eg. test.google.com):")
    dk=DeployKit(domain_name=input())
    inputInterrupt()
    dk.sys_update()
    inputInterrupt()
    dk.rc_local_enable()
    inputInterrupt()
    dk.deploy_otp()
    inputInterrupt()
    dk.deploy_nginx()
    inputInterrupt()
    dk.deploy_ssr()
    