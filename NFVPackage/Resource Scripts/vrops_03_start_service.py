# service "vRealize Operations Manager"


# start the service
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
adminUsername = attrs['vROPS admin Username']
#driver = webdriver.PhantomJS(executable_path=qualiroot() + '/phantomjs.exe', service_args=['--ignore-ssl-errors=true'])
driver = webdriver.Chrome(executable_path=qualiroot() + '/chromedriver.exe', service_args=['--ignore-certificate-errors'])
driver.set_window_size(1440,990)
driver.implicitly_wait(20)
wait = WebDriverWait(driver, 60)

#navigate to first page
driver.get("https://"+vromAddress+"/admin/login.action")

#login
driver.find_element_by_id('textfield-1009-inputEl').clear()
driver.find_element_by_id('textfield-1009-inputEl').send_keys(adminUsername)
driver.find_element_by_id('textfield-1011-inputEl').clear()
driver.find_element_by_id('textfield-1011-inputEl').send_keys(adminPassword)
#click on login
driver.find_element_by_id("loginBtn").click()
time.sleep(5)
#wait for the page to completly load - and hide the splash screen
wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='x-splash-icon']")))
time.sleep(5)

#start the service
wait.until(EC.element_to_be_clickable((By.ID, 'button-1108-btnIconEl')))
driver.find_element_by_id("button-1108-btnIconEl").click()
#confirm first application startup
# STEPS # Quit if it looks different

try:
    driver.find_element_by_xpath("//span[contains(@id,'yes_')]").click()
    time.sleep(2)
except Exception:
    pass

def find_login_page(driver1):
    url = driver1.current_url
    if url.find("vcops-web-ent/login.action") != -1:
        return True
    else:
        return False

#wait for online
time.sleep(20)
WebDriverWait(driver, 1200).until(EC.presence_of_element_located((By.XPATH, "//*[text()='Take Offline']")))

driver.quit()
