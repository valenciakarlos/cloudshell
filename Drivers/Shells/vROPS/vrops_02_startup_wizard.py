# service "vRealize Operations Manager"

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
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

vropsHostname = attrs['vROPS FQDN']
vropsUsername = attrs['vROPS admin Username']
vropsPassword = attrs['vROPS admin Password']

clusterName = attrs['vROPS Cluster Master FQDN']
ntpServer = attrs['vROPS NTP Server IP']


#driver = webdriver.PhantomJS(executable_path=qualiroot() + '/phantomjs.exe', service_args=['--ignore-ssl-errors=true'])
driver = webdriver.Chrome(executable_path=qualiroot() + '/chromedriver.exe', service_args=['--ignore-certificate-errors'])
driver.set_window_size(1440,990)
driver.implicitly_wait(20)
wait = WebDriverWait(driver, 60)

#navigate to first page
driver.get("https://"+vromAddress+"/admin/newCluster.action")

#wait for the new installation button
wait.until(EC.presence_of_element_located((By.ID, 'button-1177-btnIconEl')))
#click on new installation
driver.find_element_by_id("button-1177-btnIconEl").click()

#wait for the Next button
wait.until(EC.presence_of_element_located((By.ID, 'button-1013-btnIconEl')))
#click on next
driver.find_element_by_id("button-1013-btnIconEl").click()

#set new admin password
driver.find_element_by_id('textfield-1020-inputEl').send_keys(adminPassword)
driver.find_element_by_id('textfield-1021-inputEl').send_keys(adminPassword)
#click on next
driver.find_element_by_id("button-1013-btnIconEl").click()

#select license (default one)
driver.find_element_by_id("radiofield-1027-boxLabelEl").click()
driver.find_element_by_id("radiofield-1027-inputEl").click()
#click on next
driver.find_element_by_id("button-1013-btnIconEl").click()

#set cluster node name
driver.find_element_by_id('textfield-1040-inputEl').send_keys(clusterName)
#add ntp server
driver.find_element_by_xpath("//input[contains(@id,'newNTP_')]").send_keys(ntpServer)
#add the ntp server
time.sleep(2)
driver.find_element_by_xpath("//span[contains(@id,'newNTPBtn_')]").click()
#wait for the remove button to appear
time.sleep(8)
wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@name,'removeNtp_')]")))

#click on next
driver.find_element_by_id("button-1013-btnIconEl").click()

#click on finish
driver.find_element_by_id("button-1014-btnIconEl").click()

#wait for the finish to happen, we should be redirected to the index page
time.sleep(50)

driver.quit()