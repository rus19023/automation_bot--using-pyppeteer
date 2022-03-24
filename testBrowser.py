import asyncio
from pyppeteer import launch
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



def start_step_one():
	while True:
		current_time = datetime.now(pytz.timezone('CET')).strftime("%H:%M:%S")
		print(current_time)
		if current_time == start_time_step_one:
			break
		time.sleep(1)
def start_step_two():
	while True:
		current_time = datetime.now(pytz.timezone('CET')).strftime("%H:%M:%S")
		print(current_time)
		if current_time == start_time_step_two:
			break
		time.sleep(1)
async def handle_step_one( page ):       
        await page.goto( "https://service2.diplo.de/rktermin/extern/choose_categoryList.do?locationCode=pris&realmId=362" ,  {'waitUntil': 'domcontentloaded'}  )   
        print('current url 1 is ', await page.evaluate("() => window.location.href"))
        print( 'next link ')
        oneHref1 = await page.waitForXPath('//*[@id="content"]/div[1]/div[2]/a')
        navPromise1 = asyncio.ensure_future( page.waitForNavigation( {"timeout": 60000, "waitUntil": "networkidle0"} ))
        await oneHref1.click()      
        await navPromise1        
        print('current url 2 is ', await page.evaluate("() => window.location.href"))  
        print( 'next link ')

        oneHref2 = await page.waitForXPath('//*[@id="content"]/div[1]/h3[1]/a[2]')
        navPromise2 = asyncio.ensure_future( page.waitForNavigation( {"timeout": 60000, "waitUntil": "networkidle0"} ))
        await oneHref2.click()     
        await navPromise2
        print('current url 3 is ', await page.evaluate("() => window.location.href"))
        print( 'next link ')

        while True:
            content, page = await solve_captcha( page )                        
            if  ('captchaText' not in content) and ('<div' in content):
                return page 

async def handle_step_two( page, browser ):       
        await page.goto( "https://service2.diplo.de/rktermin/extern/appointment_showForm.do?action%3Aappointment_refreshCaptcha=Load+another+picture&locationCode=pris&realmId=362&categoryId=591" ,  {'waitUntil': 'domcontentloaded'}  )           
        print('current url is ', await page.evaluate("() => window.location.href"))
        time.sleep( 3 )   
        page = await browser.pages()     
        return page[1]
        
async def handle_step_three( page, line ):
        # start_step_two()
        print(' handle two')
        link = "https://service2.diplo.de/rktermin/extern/appointment_addAppointment.do?locationCode=pris&realmId=362&categoryId=591&dateStr="+ date_str + "&openingPeriodId="+opening_period_id
        
        await page.goto( link, {'waitUntil': 'domcontentloaded'} )
                
        print('current url is ', await page.evaluate("() => window.location.href"))

        await page.evaluate( f"""() => {{
            document.getElementById("appointment_newAppointmentForm_fields_3__content").checked=true;                        
            }}""" )
        await page.evaluate( f"""() => {{
            document.getElementById("appointment_newAppointmentForm_lastname").value = '{line[0]}';            
            }}""" )
        await page.evaluate( f"""() => {{
            document.getElementById("appointment_newAppointmentForm_firstname").value = '{line[1]}';            
            }}""" )
        await page.evaluate( f"""() => {{
            document.getElementById("appointment_newAppointmentForm_email").value = '{line[2]}';            
            }}""" )
        await page.evaluate( f"""() => {{
            document.getElementById("appointment_newAppointmentForm_emailrepeat").value = '{line[3]}';            
            }}""" )
        await page.evaluate( f"""() => {{
            document.getElementById("fields0content").value = '{line[4]}';            
            }}""" )            
        await page.evaluate( f"""() => {{
            document.getElementById("appointment_newAppointmentForm_fields_1__content").value = '{line[5]}';            
            }}""" )
        await page.evaluate( f"""() => {{
            document.getElementById("appointment_newAppointmentForm_fields_2__content").value = '{line[6]}';            
            }}""" )
        while True:
            content, page = await solve_captcha2( page )                        
            if  ('captchaText' not in content) and ('<div' in content):
                break                
        
        if 'appointment_thanx.do' in await page.evaluate("() => window.location.href"):            
            success.append( line )
            df = pd.DataFrame( success )
            df.to_csv('results/thanx.csv', index=False, header=['Last_Name', 'First_Name', 'Email', 'Repeat_email', 'Date_of_birth', 'Passport_number', 'Phone_number', 'Date_of_birth2'])            
            

        elif 'appointment_showDay.do' in await page.evaluate("() => window.location.href"):            
            failsDay.append( line )
            df = pd.DataFrame( failsDay )
            df.to_csv('results/showday.csv', index=False, header=['Last_Name', 'First_Name', 'Email', 'Repeat_email', 'Date_of_birth', 'Passport_number', 'Phone_number', 'Date_of_birth2'])
            

        elif 'The server is currently busy' in await page.evaluate("() => window.location.href"):
            # driver.refresh()
            failsBusy.append( line )
            df = pd.DataFrame( failsBusy )
            df.to_csv('results/serverbusy.csv', index=False, header=['Last_Name', 'First_Name', 'Email', 'Repeat_email', 'Date_of_birth', 'Passport_number', 'Phone_number', 'Date_of_birth2'])

        elif 'appointment_showMonth.do' in await page.evaluate("() => window.location.href"):            
            failsMonth.append( line )
            df = pd.DataFrame( failsMonth )
            df.to_csv('results/showmonth.csv', index=False, header=['Last_Name', 'First_Name', 'Email', 'Repeat_email', 'Date_of_birth', 'Passport_number', 'Phone_number', 'Date_of_birth2'])            

        else:            
            unknown.append( line )		
            df = pd.DataFrame( unknown )
            df.to_csv('results/unknown.csv', index=False, header=['Last_Name', 'First_Name', 'Email', 'Repeat_email', 'Date_of_birth', 'Passport_number', 'Phone_number', 'Date_of_birth2'])
            

async def solve_captcha( page ):        
        print( " soleve captch ")
        content = await page.evaluate('() => document.body.innerHTML')        
        # content = await page.content()
        print("content")
        print( content )
        tree = html.fromstring( content )          
        captcha = tree.xpath( "//captcha/div/@style" )[0].split("'")[1].replace( "data:image/jpg;base64", "")
        path = hashlib.md5( captcha.encode() ).hexdigest()
        f = open( f'captchas/{path}.jpeg', 'wb' )
        f.write( base64.b64decode( captcha ))
        f.close()            

        captcha_file = open( f'captchas/{path}.jpeg', 'rb')
        captcha2 = api.solve(captcha_file)
        print( " api soleve is")
        print( captcha2.await_result() )			
        captcha_file.close()
        code = captcha2.await_result()                
        await page.evaluate( f"""() => {{ document.getElementById("appointment_captcha_month_captchaText").value = '{code}'; }}""")
        time.sleep( 0.1 )
        element = await page.querySelector('#appointment_captcha_month_appointment_showMonth')
        
        navPromise = asyncio.ensure_future( page.waitForNavigation( {"timeout": 60000, "waitUntil": "networkidle0"} ))
        
        await element.click()        
        await navPromise        
        time.sleep( 4 )
        content = await page.evaluate('() => document.body.innerHTML')
        return content, page
async def solve_captcha2( page ):        
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
        await page.evaluate( f"""() => {{ document.getElementById("appointment_newAppointmentForm_captchaText").value = '{code}'; }}""")
        time.sleep( 0.1 )
        element = await page.querySelector('#appointment_newAppointmentForm_appointment_addAppointment')
        
        navPromise = asyncio.ensure_future( page.waitForNavigation( {"timeout": 60000, "waitUntil": "networkidle0"} ))
        
        await element.click()        
        time.sleep( 2 )
        await navPromise        
        content = await page.evaluate('() => document.body.innerHTML')
        return content, page        


# global vars
success = []
failsDay = []
failsMonth = []
failsBusy = []
unknown = []

f = open('period.txt')
date_str, opening_period_id, googlePath = f.read().splitlines()

f.close()
print(date_str, opening_period_id, googlePath)
try:
	makedirs('captchas')
except:
	pass
try:
	makedirs('results')
except:
	pass

# start_step_two()
data = pd.read_csv( 'diplo.de.csv', dtype=str).values.tolist()

async def main( line ):
        browser = await launch( headless=False, autoclose=False, executablePath=googlePath )                
        page = await browser.newPage()
        
        try:            
            resultPage = await handle_step_one( page )
            page2 = await handle_step_two( resultPage, browser )
            await handle_step_three( page2 , line )            
        except:
            await browser.close()           

loop = asyncio.get_event_loop()
loop.create_task( main(data[0]) )
# loop.create_task( main(data[1]) )
# loop.create_task( main(data[2]) )
# loop.create_task( main(data[3]) )

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass    





