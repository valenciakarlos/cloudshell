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
pakPath = attrs['Log Insight PAK Path']



#driver = webdriver.PhantomJS(executable_path=qualiroot() + '/phantomjs.exe', service_args=['--ignore-ssl-errors=true'])
driver = webdriver.Chrome(executable_path=qualiroot() + '/chromedriver.exe', service_args=['--ignore-certificate-errors'])
driver.set_window_size(1440,990)
driver.implicitly_wait(20)
wait = WebDriverWait(driver, 60)

#navigate to first page
driver.get("https://"+vromAddress+"/admin/appliance")

#login
#set username
driver.find_element_by_name('username').send_keys("admin")
#set password
driver.find_element_by_name('password').send_keys(adminPassword)
#click login
driver.find_element_by_id("login-button").click()
time.sleep(5)

#page2
#wait for the license field
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Upload PAK...']")))

#set file
driver.find_element_by_xpath("//div[contains(@class,'upgrade-uploader')]//input[@type='file']").send_keys(pakPath)



#upgrade
driver.find_element_by_xpath("//div[contains(@class,'upgrade-uploader')]//button[text()='Upgrade']").click()
#are you sure?
driver.find_element_by_xpath("//div[contains(@class,'upgrade-view-dialog')]//button[text()='Upgrade']").click()

#wait for upload to complete
WebDriverWait(driver, 900).until(EC.presence_of_element_located((By.XPATH, "//div[text()='End User License Agreement']")))

#accept the EULA
driver.find_element_by_xpath("//button[text()='Accept']").click()

#wait for upgrade to complete
def find_login_page(driver1):
    url = driver1.current_url
    if url.find("login") != -1:
        return True
    else:
        return False

#wait for login page
WebDriverWait(driver, 900).until(find_login_page)

time.sleep(5)

driver.quit()
