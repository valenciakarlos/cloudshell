# service "vRealize Log Insight"

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
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']


vLogAddress = attrs['Log Insight IP']
adminPassword = attrs['Log Insight Admin Password']
adminEmail = attrs['Log Insight Admin Email']
licenseKey = attrs['Log Insight License Key']
emailSysNotifTo = attrs['Log Insight Notification Emails CSV']

wt = attrs['Log Insight Send Weekly Trace']
sendWeeklyTrace = 1 if wt.lower() in ['yes', 'true'] else 0

nt = attrs['Log Insight Sync Time With NTP']
syncTimeWithNTP = 1 if nt.lower() in ['yes', 'true'] else 0

ntpServers = attrs['Log Insight NTP Servers CSV']
smtpServer = attrs['Log Insight SMTP Server']
smtpPort = attrs['Log Insight SMTP Port']

ss = attrs['Log Insight SMTP SSL']
smtpSSL = 1 if ss.lower() in ['yes', 'true'] else 0

tl = attrs['Log Insight SMTP STARTTLS']
smtpSTARTLS = 1 if tl.lower() in ['yes', 'true'] else 0

smtpSender = attrs['Log Insight SMTP Sender']
smtpUsername = attrs['Log Insight SMTP Username']
smtpPassword = attrs['Log Insight SMTP Password']


#driver = webdriver.PhantomJS(executable_path=qualiroot() + '/phantomjs.exe', service_args=['--ignore-ssl-errors=true'])
driver = webdriver.Chrome(executable_path=qualiroot() + '/chromedriver.exe', service_args=['--ignore-certificate-errors'])
driver.set_window_size(1440, 990)
driver.implicitly_wait(20)
wait = WebDriverWait(driver, 60)

#navigate to first page
driver.get("https://" + vLogAddress + "/admin/startup")
# STEPS # Quit if startup page no longer appears
#wait for the next button
wait.until(EC.element_to_be_clickable((By.ID, 'skip-button')))
#click on next button
driver.find_element_by_id("skip-button").click()

#wait for the start new deployment button
wait.until(EC.element_to_be_clickable((By.ID, 'new-deployment-button')))
#click on start new deployment
driver.find_element_by_id("new-deployment-button").click()

#page 1
#wait for the email field
WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.NAME, 'user.email')))
wait.until(EC.presence_of_element_located((By.NAME, 'newPassword')))

#set admin email
driver.find_element_by_name('user.email').clear()
driver.find_element_by_name('user.email').send_keys(adminEmail)

#set new admin password
driver.find_element_by_name('newPassword').send_keys(adminPassword)
driver.find_element_by_name('newPasswordConfirm').send_keys(adminPassword)
#save and continue
driver.find_element_by_id("save-button").click()

#page2
#wait for the license field
wait.until(EC.presence_of_element_located((By.ID, 'license-key')))

#set license
if licenseKey!='':
    driver.find_element_by_id('license-key').send_keys(licenseKey)
    driver.find_element_by_id("add-new-license-button").click()
    time.sleep(10)
    #save and continue
    driver.find_element_by_id("skip-button").click()
else:
    #click on next\
    time.sleep(2)
    driver.find_element_by_id("skip-button").click()


#page3
#wait for the emails field
wait.until(EC.presence_of_element_located((By.ID, 'alert-system-emails-textbox')))

#set admin email
driver.find_element_by_id('alert-system-emails-textbox').clear()
driver.find_element_by_id('alert-system-emails-textbox').send_keys(emailSysNotifTo)

if sendWeeklyTrace==0:
    driver.find_element_by_id("phone-home-feedback-checkbox").click()

#save and continue
driver.find_element_by_id("save-button").click()


#page4
#wait for the ntp servers field
wait.until(EC.presence_of_element_located((By.ID, 'ntp-servers-textbox')))
time.sleep(2)

if syncTimeWithNTP==0:
    driver.find_element_by_xpath("//select[@id='ntp-mode-dropdown']/option[@value='HOST']").click()
else:
    #set ntp servers
    driver.find_element_by_id('ntp-servers-textbox').clear()
    driver.find_element_by_id('ntp-servers-textbox').send_keys(ntpServers)


#save and continue
driver.find_element_by_id("save-button").click()


#page5
#wait for the smtp field
wait.until(EC.presence_of_element_located((By.NAME, 'smtpConfig.server')))
time.sleep(2)
#set smtp server
driver.find_element_by_name('smtpConfig.server').clear()
driver.find_element_by_name('smtpConfig.server').send_keys(smtpServer)

#set smtp server port
driver.find_element_by_name('smtpConfig.port').clear()
driver.find_element_by_name('smtpConfig.port').send_keys(smtpPort)

#set smtp ssl
if smtpSSL==1:
    driver.find_element_by_name('smtpConfig.sslAuth').click()

#set smtp tls
if smtpSTARTLS==1:
    driver.find_element_by_name('smtpConfig.tls').click()

#set smtp default sender
driver.find_element_by_name('smtpConfig.defaultSender').clear()
driver.find_element_by_name('smtpConfig.defaultSender').send_keys(smtpSender)

#set smtp username
driver.find_element_by_name('smtpConfig.login').send_keys(smtpUsername)

#set smtp password
driver.find_element_by_name('smtpConfig.password').send_keys(smtpPassword)


#save and continue
driver.find_element_by_id("save-button").click()


#page5
#wait for all done
wait.until(EC.presence_of_element_located((By.XPATH, '//p[text()="All done!"]')))
time.sleep(2)

#click on finish
driver.find_element_by_id("skip-button").click()

time.sleep(5)

driver.quit()

quali_exit(__file__)