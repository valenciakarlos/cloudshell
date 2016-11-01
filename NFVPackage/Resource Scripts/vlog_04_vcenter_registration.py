# service "vRealize Log Insight"

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
from quali_remote import quali_enter, quali_exit, qs_trace, qs_info

quali_enter(__file__)

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']


vromAddress = attrs['Log Insight IP']
adminPassword = attrs['Log Insight Admin Password']


vcenterHostname = attrs['Cloud vCenter FQDN']
domain = attrs['Domain']
app_logi_vcenter_username = attrs['app_logi_vcenter Username']
app_logi_vcenter_password = attrs['app_logi_vcenter Password']

vcenterUsername = domain + '\\' + app_logi_vcenter_username
vcenterPassword = app_logi_vcenter_password

#driver = webdriver.PhantomJS(executable_path=qualiroot() + '/phantomjs.exe', service_args=['--ignore-ssl-errors=true'])
driver = webdriver.Chrome(executable_path=qualiroot() + '/chromedriver.exe', service_args=['--ignore-certificate-errors'])
driver.set_window_size(1440,990)
driver.implicitly_wait(20)
wait = WebDriverWait(driver, 250)

#navigate to first page
driver.get("https://"+vromAddress+"/admin/vsphere")

#login
#set username
driver.find_element_by_name('username').send_keys("admin")
#set password
driver.find_element_by_name('password').send_keys(adminPassword)
#click login
driver.find_element_by_id("login-button").click()
time.sleep(5)

#wait for the vsphere page
wait.until(EC.presence_of_element_located((By.NAME, 'vsphereConfig.credentials[0].hostname')))
# STEPS # Quit if vCenter already listed
#hostname
driver.find_element_by_name('vsphereConfig.credentials[0].hostname').send_keys(vcenterHostname)
#username
driver.find_element_by_name('vsphereConfig.credentials[0].username').send_keys(vcenterUsername)
#password
driver.find_element_by_name('vsphereConfig.credentials[0].password').send_keys(vcenterPassword)
#collect vcenter server events - marked automatically
#driver.find_element_by_name('vsphereConfig.credentials[0].vsphereEventsEnabled').click()
#config esxi hosts to send logs - marked automatically
#driver.find_element_by_xpath('//input[@class="vsphere-esxi-enable-checkbox"]').click()

#save
driver.find_element_by_id("save-button").click()

#wait for the configuration completed
time.sleep(150)
try:
    #wait.until(EC.element_to_be_clickable((By.XPATH, "//div[.//div[text()='Configuration completed successfully']]//button[text()='OK']")))
    driver.find_element_by_xpath("//div[.//div[text()='Configuration completed successfully']]//button[text()='OK']").click()
except Exception:
    #if some ESXis are disconnect
    driver.find_element_by_xpath("//*[contains(@class, 'normalbutton confirmbutton')]").click()
#OK



time.sleep(5)

driver.quit()

quali_exit(__file__)