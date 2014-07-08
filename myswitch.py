import subprocess
import urllib2
import re
import Tkinter as Tk
import time

mystring= "IP             \t\tProduct Number\tFirmware Version\t\tLatest Firmware Ver\n"
counter=0
version="1.7"


class MySwitch(object):
    def __init__(self, myid):
        self.ip = "99.999.99." + str(myid)
        self.latest_fver = ""
        #Below are for output cosmetics, making ugly snmp replies look beautiful a bit more
        #cropping data here
        self.cmp_pnum = re.compile('[J|j][0-9][0-9][0-9][0-9][A-Z|a-z]', re.MULTILINE)
        self.cmp_frmw = re.compile('(?<=revision.)[A-Z]\.[0-9][0-9]\.[0-9][0-9]*', re.MULTILINE)
        self.cmp_frmw2 = re.compile('(?<=revision.)[A-Z][A-Z]\.[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9][0-9][0-9]',
                                    re.MULTILINE)
        self.cmp_frmw3 = re.compile('(?<=revision.)[A-Z]\.[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9][0-9][0-9]', re.MULTILINE)
        self.cmp_rom = re.compile('(?<=ROM.)[A-Z]\.[0-9][0-9]\.[0-9][0-9]', re.MULTILINE)
        self.cmp_rom2 = re.compile('(?<=ROM.)[A-Z][A-Z]\.[0-9][0-9]\.[0-9][0-9]', re.MULTILINE)
        self.cmp_isAll = re.compile('Allied')     #Allied Telesyn
        self.cmp_isComw = re.compile('Comware')   #HP Comware
        self.cmp_isMS = re.compile('Microsoft')   #Microsoft
        self.cmp_latest_ver  = re.compile('[A-Z|a-z]\.[0-9][0-9]\.[0-9][0-9]*', re.MULTILINE) #R.11.98
        self.cmp_latest_ver2 = re.compile('[A-Z][A-Z]\.[0-9][0-9]\.[0-9][0-9]*\.[0-9][0-9][0-9][0-9]', re.MULTILINE)  # version RA.XX.XX
        self.cmp_latest_ver3 = re.compile('[A-Z]\.[0-9][0-9]\.[0-9][0-9]*\.[0-9][0-9][0-9][0-9]', re.MULTILINE)       #    W.15.10.0015

    def printnice(self, output):
        global mystring,counter
        for line in output:         # just one line expected, but comware has 3 lines so we break there
            if self.cmp_isAll.findall(line.strip()):     #is it AlliedTelesyn
                self.pnum = "Allied Telesyn"
                self.frmw = "N/A"
            elif self.cmp_isComw.findall(line.strip()):   #is it Comware
                self.pnum = "Comware"
                self.frmw = "N/A"
                self.romv = "N/A"
                self.pnum, self.frmw= self.cosmetics(self.pnum, self.frmw)
                break
            elif self.cmp_isMS.findall(line.strip()): #is it Microsoft
                self.pnum = "Microsoft"
                self.frmw = "N/A"
                self.romv = "N/A"
                break
            else:
                if  self.cmp_frmw3.findall(line.strip()):              #    W.15.10.0015 format , i=3
                    self.pnum = self.cmp_pnum.findall(line.rstrip())
                    self.frmw = self.cmp_frmw3.findall(line.strip())
                    i=3
                else:                                                  #    either R.11.98 (i=1) or RA.XX.XX (i=2)
                    i = 1
                    self.pnum = self.cmp_pnum.findall(line.rstrip())
                    self.frmw = self.cmp_frmw.findall(line.strip())
                    if (len(str(self.frmw)) < 5 ):                     # version RA.XX.XX
                        self.frmw = self.cmp_frmw2.findall(line.rstrip())
                        i = 2
                self.pnum, self.frmw = self.cosmetics(self.pnum, self.frmw)
                self.latest_fver = self.latestfrm(self.pnum, i)
                if (self.checkver()):
                    counter +=1
                    if i==2 or i==3:
                        mystring += self.ip+ "\t\t"+ self.pnum+ "\t\t\t"+ self.frmw.strip()+ "\t\t\t"+ self.latest_fver.strip()+ \
                                '\t\t'+ "\n"
                    else:
                        mystring += self.ip+ "\t\t"+ self.pnum+ "\t\t\t"+ self.frmw.strip()+ "\t\t\t\t"+ self.latest_fver.strip()+ \
                                '\t\t\t'+ "\n"
    def snmp_send_rec(self):
        self.command = "snmpget -v 2c -c snmpkey " + self.ip + " sysDescr.0"
        proc = subprocess.Popen(self.command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        self.return_code = proc.wait()
        if self.return_code == 1:
            print 130 * "*", ">>", self.ip, "<<does not give snmp response"
        else:
            self.printnice(proc.stdout)


    def cosmetics(self, pnum, frmw):
        crop_1 = re.compile('\[\'')
        crop_2 = re.compile('\'\]')
        self.pnum = re.sub(crop_2, '', re.sub(crop_1, '', str(pnum)))
        self.frmw = re.sub(crop_2, '', re.sub(crop_1, '', str(frmw)))
        return self.pnum, self.frmw

    def latestfrm(self, mypnum, i):     #i=1 indicates R.11.98 . .  =2 indicates RA.11.22
        self.my_url = "https://h10145.www1.hp.com/downloads/SoftwareReleases.aspx?ProductNumber=" + mypnum
        self.mypage = urllib2.urlopen(self.my_url).read()
        if len(self.cmp_latest_ver.findall(self.mypage)) != 0:
            if i == 1: #short version like H.03.43
                return self.cmp_latest_ver.findall(self.mypage)[0]
            elif i==2: # long version like HA.32.34
                return self.cmp_latest_ver2.findall(self.mypage)[0]
            elif i==3: # another long like W.15.10.0015
                return self.cmp_latest_ver3.findall(self.mypage)[0]
        else:
            return "N/A"



    def checkver(self):

        for element in range(0, 3):
            if self.latest_fver.split('.', 3)[element].upper() != self.frmw.split('.', 3)[element].upper():
                if int(self.frmw.split('.', 3)[element]) < int(self.latest_fver.split('.', 3)[element]):
                    return True
                if element == 0:
                    print "Version comparison N/A"
                    return False
                else:
                    return False
            else:
                if element ==0 or element ==1:
                    pass # do nothing
                else:
                    return False



def notifyme(stringy):
    import smtplib
    global version
    recipients =['mymail@mymail.com','mymail1@mymail.com','mymail2@mymail.com']
    to =", ".join(recipients)
    gmail_user = 'korgios42@gmail.com'
    gmail_pwd ="password_deleted"  
    smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(gmail_user, gmail_pwd)
    header = 'To:' + to + '\n' + 'From: ' + gmail_user + '\n' + 'Subject: Korgios Firmware Update Notification Service \n'
    print header
    msg = header +str(counter)+ " HP Procurve Switches need Firmware Update\n "+stringy+"\n"+version
    smtpserver.sendmail(gmail_user,recipients, msg)
    print 'done!'
    smtpserver.close()

if __name__ == "__main__":
    for octet in range(20,180):
        currswitch = MySwitch(octet)
        currswitch.snmp_send_rec()
        notifyme(mystring)
#version=1.7 ( 12/30/2013)

