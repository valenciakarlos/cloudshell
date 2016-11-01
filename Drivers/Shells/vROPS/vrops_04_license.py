# service "vRealize Operations Manager"

# create new environment

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


vromAddress = attrs['vROPS IP']
adminPassword = attrs['vROPS admin Password']
productKey = attrs['vROPS Product Key']
adminUsername = attrs['vROPS admin Username']

#driver = webdriver.PhantomJS(executable_path=qualiroot() + '/phantomjs.exe', service_args=['--ignore-ssl-errors=true'])
driver = webdriver.Chrome(executable_path=qualiroot() + '/chromedriver.exe', service_args=['--ignore-certificate-errors'])
driver.set_window_size(1440, 990)
driver.implicitly_wait(20)
wait = WebDriverWait(driver, 60)

#navigate to first page
driver.get("https://"+vromAddress+"/vcops-web-ent/login.action")

#login
driver.find_element_by_id('userName-inputEl').clear()
driver.find_element_by_id('userName-inputEl').send_keys(adminUsername)
driver.find_element_by_id('password-inputEl').clear()
driver.find_element_by_id('password-inputEl').send_keys(adminPassword)
#click on login
driver.find_element_by_id("loginBtn-btnInnerEl").click()
time.sleep(5)
#wait for the page to completly load - and next button is clickable
wait.until(EC.element_to_be_clickable((By.ID, 'wizard-button-next-btnEl')))

# STEPS # Quit if it looks different

#next
driver.find_element_by_id("wizard-button-next-btnEl").click()
time.sleep(3)
#accept EULA
driver.find_element_by_id("checkbox-1062-inputEl").click()

#wait.until(EC.element_to_be_clickable((By.ID, 'checkbox-1050-inputEl')))
#driver.find_element_by_id("checkbox-1050-inputEl").click()
#click on next
driver.find_element_by_id("wizard-button-next-btnInnerEl").click()
#enter a license
time.sleep(2)
if productKey!="": #disable due to missing license to test with
    driver.find_element_by_xpath("//*[text()[contains(.,'Product Key:')]]").click()
    time.sleep(1)
    driver.find_element_by_xpath("//*[@id='textfield-1084-inputEl']").send_keys(productKey)
    #validate
    driver.find_element_by_xpath("//*[text()[contains(.,'Validate License Key')]]").click()
    time.sleep(5)
    try:
        #succses 
        driver.find_element_by_id("wizard-button-next-btnInnerEl").click()
    except Exception:
        driver.find_element_by_xpath("//*[text()[contains(.,'OK')]]").click()
        #clear license
        driver.find_element_by_id("radio-1082-inputEl").click()
        driver.find_element_by_id("wizard-button-next-btnInnerEl").click()
#driver.find_element_by_id("wizard-button-next-btnInnerEl").click()
else:
    driver.find_element_by_id("wizard-button-next-btnInnerEl").click()


#disbale VMware customer experience
driver.find_element_by_id("checkbox-1069-inputEl").click()
#click on next
driver.find_element_by_id("wizard-button-next-btnInnerEl").click()

#click on finish
driver.find_element_by_id("wizard-button-finish-btnInnerEl").click()


def find_solutions_page(driver1):
    url = driver1.current_url
    if url.find("ui/index.action#/administration/solutions") != -1:
        return True
    else:
        return False

#wait for online
WebDriverWait(driver, 900).until(find_solutions_page)

driver.quit()

quali_exit(__file__)