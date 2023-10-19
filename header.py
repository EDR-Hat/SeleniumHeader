from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import sys
import time
import re
import json
from datetime import date as curdate
import matcher

options = Options()
#had to send explicit path to the browser in my envirionment for some reason
#I also had to put the webdriver exe in the same location as this script, I couldn't figure out the default path
options.binary_location = r'C:\Users\EHatton\AppData\Local\Mozilla Firefox\firefox.exe'
browser = webdriver.Firefox(options=options)
wait = WebDriverWait(browser, 20)
f = ''
if len(sys.argv) == 3: #a link to an instance of relevant report or a file with links to those reports
     if sys.argv[1] == '-f':
          f = open(sys.argv[2])
          locations = f.read().split('\n')
else:
    locations = [sys.argv[1]]

# wrapper for using the wait condition
def getElems(way, identifier):
    elm = ''
    try:
        elm = wait.until(EC.presence_of_all_elements_located((way, identifier)))
    except:
        print("err timeout with: method(" + way + ") and value(" + identifier + ")")
        exit(1)
    return elm

def getElem(way, identifier):
    elm = ''
    try:
        elm = wait.until(EC.presence_of_element_located((way, identifier)))
    except:
        print("err timeout with: method(" + way + ") and value(" + identifier + ")")
        exit(1)
    return elm

#sign in once
browser.get("url to relevant healthcare signin page") #had to censor this link
time.sleep(3)

with open('relevant.cred','r') as f:
    cred = json.load(f)
f.close()

email = getElem('id', 'login-username')
pswd = getElem('id', 'login-password')
next = getElem('class name', 'btn-primary')
email.send_keys(cred['user_name'])
pswd.send_keys(cred['password'])
next.click()

for location in locations: #loop through the reports
    browser.get(location)
    time.sleep(3)   

    try:
        glyph = getElem('class name', 'info-glyph')
        glyph.click()
    except:
        pass

    time.sleep(5)
    code = getElem('class name', 'code-highlight').text
    next = getElem('class name', 'btn-primary')

    resources = matcher.getResources(code)
    code = code.split("*/")
    body = '' #the body of sql code
    info = {} #dictionary of header info

    #find the length of the header if it exists
    head = 0
    if len(code) > 1:
        head = code[0].count('\n')

    #parse header
    if head > 1:
        continue #skipping reports that already have headers
        body = code[1]
        delineated = code[0].split(sep="\n")
        info['Report Name: '] = [x[0] for x in [re.findall("Report Name: (.*)", x) for x in delineated] if x != [] ][0]
        info['Location: '] = location
        info['Code Edited By: '] = [x[0] for x in [re.findall("Code Edited By: (.*)", x) for x in delineated] if x != [] ][0]
        info['Description: '] = [x[0] for x in [re.findall("Description: (.*)", x) for x in delineated] if x != [] ][0]
        info['WCHC Started: '] = [x[0] for x in [re.findall("WCHC Started: (.*)", x) for x in delineated] if x != [] ][0]
        try:
            info['Version Date: '] = [x[0] for x in [re.findall("Version Date: (.*)", x) for x in delineated] if x != [] ][0]
        except:
            info['Version Date: '] = str(curdate.today())
        info['Revision History:'] = [x[0] for x in [re.findall("Revision History:(.*)", x) for x in delineated] if x != [] ][0]
        next.click()

    #otherwise grab header info from the webpage
    else:
        body = code[0]
        info['Report Name: '] = getElem('tag name', 'h1').text
        info['Location: '] = location
        info['Code Edited By: '] = getElem('xpath', "//div[@id='sql-section']/div[2]/div/div[2]/dd").text
        info['WCHC Started: '] = "?"
        info['Version Date: '] = str(curdate.today())
        info['Revision History:'] = " "
        next.click()
        info['Description: '] = getElem('id', "description").text

    #put resources in with correct header names
    for x in resources.split('\n'):
        data = re.findall("(^.*: )(.*)", x)
        if len(data) == 1:
            info[data[0][0]] = data[0][1]

    #turn the dictionary into a nicely formatted string
    #the info keys to the dictionary are used as the header names
    header = ["/*************************"] + [x + info[x] for x in info] + ["*************************/"]
    header = '\n\n'.join(header)

    #navigate to the main sql box, do control up and paste header
    def actions():
        try:
            sqlBox = getElems('tag name', 'textarea')[1]
            sqlBox.send_keys("a")
            sqlBox.send_keys(Keys.BACK_SPACE)
            #use the keyshortcut CTRL+HOME to navigate to the top of the textbox
            ActionChains(browser).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
            #select and erase old header
            ActionChains(browser).key_down(Keys.SHIFT).perform()
            if head != 0:
                for x in range(head + 1):
                    ActionChains(browser).send_keys(Keys.DOWN).perform()
                ActionChains(browser).send_keys(Keys.BACK_SPACE).perform()
            ActionChains(browser).key_up(Keys.SHIFT).perform()
            time.sleep(0.5)
            sqlBox.send_keys(header + "\n\n")
            return 0
        except:
            return 1

    #after using waits, the above block of code kept on failing the first attempt when it pasted on the header
    #this does a sane number of attempts at pasting the SQL if the textarea box is stale
    attempts = 0
    flag = False
    while(actions() == 1):
        attempts += 1
        if attempts > 10:
            flag = True
            break
    if flag:
        print('1')
        continue
    else:
        print('0')

    time.sleep(0.5)
    next = getElem('class name', 'btn-primary')
    next.click()

    time.sleep(1)
browser.close() #close after looping through all the links
