import asyncio
from xml.dom.minidom import Document
from pyppeteer import launch, connect
import pyppeteer
import time
from lxml import html
import base64
import pandas as pd
from threading import Lock
import hashlib
from os import makedirs
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
from azcaptchaapi import AZCaptchaApi

api = AZCaptchaApi('pdnkdbkqgmflzcy64jwnxcbw2t9gzhmr')
start_time_step_one = '23:58:00'
start_time_step_two = '00:00:01'
number_browsers = 5

# global vars
success = []
success_lock = []
fails = []
fails_lock = []
unknown = []
unknown_lock = []

f = open('period.txt')
date_str, opening_period_id = f.read().splitlines()
f.close()
print(date_str, opening_period_id)
try:
	makedirs('captchas')
except:
	pass
try:
	makedirs('results')
except:
	pass


async def handle_step_one( page ):       
        await page.goto( "http://service2.diplo.de/rktermin/extern/appointment_showMonth.do?locationCode=pris&realmId=362&categoryId=591" ,  {'waitUntil': 'domcontentloaded'}  )   
        while True:
            content = await solve_captcha( page )            
            if  'captchaText' not in content:
                break
            
                

async def solve_captcha( page ):        
        content = await page.evaluate('() => document.body.innerHTML')        
        tree = html.fromstring( content )          
        captcha = tree.xpath( "//captcha/div/@style" )[0].split("'")[1].replace( "data:image/jpg;base64", "")
        path = hashlib.md5( captcha.encode() ).hexdigest()
        f = open( f'captchas/{path}.jpeg', 'wb' )
        f.write( base64.b64decode( captcha ))
        f.close()            

        captcha_file = open( f'captchas/{path}.jpeg', 'rb')
        captcha2 = api.solve(captcha_file)
        print( captcha2.await_result() )			
        captcha_file.close()
        code = captcha2.await_result()                
        await page.evaluate( f"""() => {{ document.getElementById("appointment_captcha_month_captchaText").value = '{code}'; }}""")
        time.sleep( 0.1 )
        element = await page.querySelector('#appointment_captcha_month_appointment_showMonth')
        navPromise = asyncio.ensure_future( page.waitForNavigation( {"timeout": 60000, "waitUntil": "networkidle0"} ))
        await element.click()        
        await navPromise        
        content = await page.evaluate('() => document.body.innerHTML')
        return content		

async def main():
        browser = await launch( headless=False, autoclose=False, executablePath='C:\Program Files\Google\Chrome\Application\chrome.exe' )
        
        page = await browser.newPage()        
        
        await handle_step_one( page )                
            
        await browser.close()
        # time.sleep(60)

asyncio.get_event_loop().run_until_complete(main())
# asyncio.run( main() )




