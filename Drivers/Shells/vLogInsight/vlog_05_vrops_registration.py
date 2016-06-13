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
with open(r'c:\ProgramData\QualiSystems\Shells.log', 'a') as f:
    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + __file__.split('\\')[-1].replace('.py', '') + ': ' + str(os.environ) + '\r\n')

resource = json.loads(os.environ['RESOURCECONTEXT'])
resource_name = resource['name']
attrs = resource['attributes']


vromAddress = attrs['Log Insight IP']
adminPassword = attrs['Log Insight Admin Password']


vropsHostname = attrs['vROPS FQDN']
vropsUsername = attrs['vROPS admin Username']
vropsPassword = attrs['vROPS admin Password']


#driver = webdriver.PhantomJS(executable_path=qualiroot() + '/phantomjs.exe', service_args=['--ignore-ssl-errors=true'])
driver = webdriver.Chrome(executable_path=qualiroot() + '/chromedriver.exe', service_args=['--ignore-certificate-errors'])
driver.set_window_size(1440,990)
driver.implicitly_wait(20)
wait = WebDriverWait(driver, 180)

#navigate to first page
driver.get("https://"+vromAddress+"/admin/vrops")

#login
#set username
driver.find_element_by_name('username').send_keys("admin")
#set password
driver.find_element_by_name('password').send_keys(adminPassword)
#click login
driver.find_element_by_id("login-button").click()
time.sleep(5)

#wait for the vsphere page
wait.until(EC.presence_of_element_located((By.NAME, 'vcopsConfig.location')))

#hostname
driver.find_element_by_name('vcopsConfig.location').send_keys(vropsHostname)
#username
driver.find_element_by_name('vcopsConfig.username').send_keys(vropsUsername)
#password
driver.find_element_by_name('vcopsConfig.password').send_keys(vropsPassword)
#enable alerts integration - marked automatically
#driver.find_element_by_name('vcopsConfig.enabled').click()
#config esxi hosts to send logs - marked automatically
#driver.find_element_by_xpath('//input[@class="lic-enable-checkbox"]').click()

#save
driver.find_element_by_id("save-button").click()
time.sleep(60)
#wait for the configuration completed
wait.until(EC.element_to_be_clickable((By.XPATH, "//div[.//div[contains(text(),'Registration successful.')]]//button[text()='OK']")))
#OK
driver.find_element_by_xpath("//div[.//div[contains(text(),'Registration successful.')]]//button[text()='OK']").click()


time.sleep(5)

driver.quit()
