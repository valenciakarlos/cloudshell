# service "vRealize Operations Manager"
# -*- coding: utf-8 -*-

# configure cloud vcenter to monitor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from quali_remote import qualiroot

#
# # demo
# import time
# time.sleep(3)
# print 'Executed ' + __file__.split('\\')[-1].replace('.py', '')
# exit()
# # /demo

import os
import json
import time
with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']


vromAddress = attrs['vROPS IP']
adminPassword = attrs['vROPS admin Password']
#vropsHostname = attrs['vROPS Product Key']
domain = attrs['Domain']
username = attrs['Cloud vCenter Administrator Username']
displayName = "Cloud-vCenter"
vCenterServer = attrs['Cloud vCenter FQDN']
credentialPassword = attrs['Cloud vCenter Administrator Password']
#
vCenterRegUser = attrs['app_vrops_vcenter UPN']
vCenterRegPass = attrs['app_vrops_vcenter Password']
#monitoring goals inputs
alterObjects = 'All vSphere objects' #one of: 'All vSphere objects', 'Virtual Machines only', 'Infrastructure objects except for Virtual Machines'
health = attrs['Enable Health Alerts']
risk = attrs['Enable Risk Alerts']
efficiency = attrs['Enable Efficiency Alerts']
hardening = attrs['Enable vSphere Hardening']
overcommit_cpu = attrs['Enable CPU Overcommit']
overcommit_mem = attrs['Enable Memory Overcommit']
include_network_io = attrs['Include Network IO']
include_storage_io = attrs['Include Storage IO']

enableHealthAlerts = 1 if health.lower() in ['yes, true'] else 0
enableRiskAlerts = 1 if risk.lower() in ['yes, true'] else 0
enableEfficiencyAlerts = 1 if efficiency.lower() in ['yes, true'] else 0
credentialName = "vCenterCred"
credentialUsername = username + '@' + domain


#if overcommit_cpu:
#    if overcommit_mem:
#        overcommitCPUandMem = "Overcommit both CPU and Memory"
#    else:
#        overcommitCPUandMem = "Overcommit CPU and don’t overcommit Memory"
#else:
#    if overcommit_mem:
#        overcommitCPUandMem = "Overcommit Memory and don’t overcommit CPU"
#    else:
#        overcommitCPUandMem = "Don't Overcommit at all"
#
#
#includeNetworkAndStorage = "Do not include Network I/O or Storage I/O" #one of:
#if include_network_io:
#    if include_storage_io:
#        includeNetworkAndStorage = "Include both Network I/O and Storage I/O"
#    else:
#        includeNetworkAndStorage = "Include only Network I/O and don’t include Storage I/O"
#else:
#    if include_storage_io:
#        includeNetworkAndStorage = "Include only Storage I/O and don’t include Network I/O"
#    else:
#        includeNetworkAndStorage = "Do not include Network I/O or Storage I/O",

#driver = webdriver.PhantomJS(executable_path=qualiroot() + '/phantomjs.exe', service_args=['--ignore-ssl-errors=true'])
driver = webdriver.Chrome(executable_path=qualiroot() + '/chromedriver.exe', service_args=['--ignore-certificate-errors'])
driver.set_window_size(1440,990)
driver.implicitly_wait(20)
wait = WebDriverWait(driver, 60)

#navigate to first page
driver.get("https://"+vromAddress+"/vcops-web-ent/login.action#/administration/solutions/solutions")


#login
driver.find_element_by_id('userName-inputEl').clear()
driver.find_element_by_id('userName-inputEl').send_keys("admin")
driver.find_element_by_id('password-inputEl').clear()
driver.find_element_by_id('password-inputEl').send_keys(adminPassword)
#click on login
driver.find_element_by_id("loginBtn-btnInnerEl").click()
time.sleep(8)
#wait for the page to completly load - and configure button is clickable
wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@id,'configureBtn_')]")))
# STEPS # Quit if vSphere already listed

#choose VMware vSphere
driver.find_element_by_xpath("//td[text()='VMware vSphere']").click()
#click configure
driver.find_element_by_xpath("//span[contains(@id,'configureBtn_')]").click()


#enter display name
driver.find_element_by_xpath("//table/tbody/tr/td[text()='Display Name']/../td//input").send_keys(displayName)
#enter vcenter server address
driver.find_element_by_xpath("//table/tbody/tr/td[text()='vCenter Server']/../td//input").send_keys(vCenterServer)

#press on the plus button and add credentials
driver.find_element_by_xpath("//img[contains(@id,'btnAddCredential_')]").click()
#enter credentials name, user, pass
#enter display name
driver.find_element_by_name('credentialName').send_keys(credentialName)
#note: user must have administrator privileges on the vCenter Server system. The user needs to be added in vcenter directly as group membership will not suffice
driver.find_element_by_name('cred_::_003006019VMWAREPRINCIPALCREDENTIALUSER').send_keys(credentialUsername)
driver.find_element_by_name('cred_::_003006019VMWAREPRINCIPALCREDENTIALPASSWORD').send_keys(credentialPassword)
#ok
driver.find_element_by_xpath("//*[text()[contains(.,'OK')]]").click()
time.sleep(3)


#open advanced settings
driver.find_element_by_xpath("//img[contains(@id,'arrowBtnContainer_')]").click()
#update user/pass
driver.find_element_by_xpath("//table/tbody/tr/td[text()='Registration user']/../td//input").send_keys(vCenterRegUser)
driver.find_element_by_xpath("//table/tbody/tr/td[text()='Registration password']/../td//input").send_keys(vCenterRegPass)
#save settings
driver.find_element_by_xpath("//div[contains(@id,'toolbar')]//span[text()='Save Settings']").click()

#try:
##Review and Accept certificate
#    if driver.find_element_by_xpath("//div[.//span[text()='Review and Accept Certificate'] and contains(@class,'x-window-resizable')]"):
#        driver.find_element_by_xpath("//div[.//span[text()='Review and Accept Certificate'] and contains(@class,'x-window-resizable')]//a[.//span[text()='OK']]").click()
#except Exception:
#    pass
time.sleep(5)
try:
#Review and Accept certificate
    if driver.find_element_by_xpath("//div[contains(@id,'toolbar')]//span[text()='OK']"):
        driver.find_element_by_xpath("//div[contains(@id,'toolbar')]//span[text()='OK']").click()
except Exception:
    pass    
time.sleep(15)
#force confirmation
#try:
#    if driver.find_element_by_xpath("//div[.//span[text()='vRealize Operations Manager Registration Failed'] and contains (@class,'x-window-resizable')]"):
#        driver.find_element_by_xpath("//div[.//span[text()='vRealize Operations Manager Registration Failed'] and contains(@class,'x-window-resizable')]//a[.//span[text()='Yes']]").click()

try:
    if driver.find_element_by_xpath("//div[contains(@id,'toolbar')]//span[text()='OK']"):
        driver.find_element_by_xpath("//div[contains(@id,'toolbar')]//span[text()='OK']").click()

except Exception:
    try:
        #Info (Adapter instance creation succeeded)
        if driver.find_element_by_xpath("//div[.//span[text()='Info'] and contains(@class,'x-window-resizable')]"):
            driver.find_element_by_xpath("//div[.//span[text()='Info'] and contains(@class,'x-window-resizable')]//a[.//span[text()='OK']]").click()
    except Exception:
        #Confirmation (unable to establish a valid connection)
        try:
            #Warning (Adapter instance creation succeeded, but VC registration failed)
            if driver.find_element_by_xpath("//div[.//span[text()='Warning'] and contains(@class,'x-window-resizable')]"):
                driver.find_element_by_xpath("//div[.//span[text()='Warning'] and contains(@class,'x-window-resizable')]//a[.//span[text()='OK']]").click()
        except Exception:
            try:
                if driver.find_element_by_xpath("//div[.//span[text()='Confirmation'] and contains(@class,'x-window-resizable')]"):
                    driver.find_element_by_xpath("//div[.//span[text()='Confirmation'] and contains(@class,'x-window-resizable')]//a[.//span[text()='Yes']]").click()
            except Exception:
                raise 'Unable to connect to vCenter or bad credentials'





#click next to define monitoring goals
driver.find_element_by_id("wizard-button-next-btnEl").click()

#On the Define monitoring Goals screen choose your relevant options and click Next and then click Finish
#set alter objects (label must match the input text)
driver.find_element_by_xpath("//label[text()='" + alterObjects + "']").click()
#enable alerts - by default all are turned on, so just turn off what's needed
if enableHealthAlerts==1:
    driver.find_element_by_xpath("//label[text()='Health alerts that usually require immediate attention.']").click()

if enableRiskAlerts==1:
    driver.find_element_by_xpath("//label[text()='Risk alerts indicating that you should look into any problems in the near future']").click()

if enableEfficiencyAlerts==1:
    driver.find_element_by_xpath("//label[text()='Efficiency alerts indicating that you can reclaim resources.']").click()


def partialStringWithoutApos(s):
    return s[:s.find("'")]

#set overcommit
if overcommit_cpu == 'Yes':
    driver.find_element_by_xpath("//*[@id='radio-1132-boxLabelEl']").click()
else:
    driver.find_element_by_xpath("//*[@id='radio-1133-boxLabelEl']").click()
       
if overcommit_mem == 'True Demand':
    driver.find_element_by_xpath("//*[@id='radio-1136-boxLabelEl']").click()
elif overcommit_mem == 'Memory Consumed':
    driver.find_element_by_xpath("//*[@id='radio-1137-boxLabelEl']").click()
else:
    driver.find_element_by_xpath("//*[@id='radio-1138-boxLabelEl']").click()

if hardening == 'Yes':
    driver.find_element_by_xpath("//*[@id='radio-1141-boxLabelEl']").click()
else:
    driver.find_element_by_xpath("//*[@id='radio-1142-boxLabelEl']").click()

time.sleep(2)
#click next
driver.find_element_by_id("wizard-button-next-btnEl").click()
#click finish
driver.find_element_by_id("wizard-button-finish-btnInnerEl").click()

time.sleep(10)

driver.quit()
