from machine import Pin, I2C
from picozero import RGBLED
import time
from time import sleep_ms
import network
import urequests
import ntptime
import ujson
import gc #garbage collector

### your data
ssid = 'your ssid here'
password = 'your wifi password here'
apiAuth = 'Basic your base 64 secret here - but leave the Basic at the start'

#### set up pins
rgbTdy = RGBLED(red = 13, green = 14, blue = 15)
rgbTmw = RGBLED(red = 2, green = 1, blue = 0)


#make some subroutines
def allOn():
    rgbTmw.cycle()
    rgbTdy.cycle()

    
def allOff():
    rgbTmw.off()
    rgbTdy.off()
    
def After  (s, want) : return s[s.find(want) + len(want):]
def Before (s, want) : return s[:s.find(want)]

#
gc.enable()

#Connecting to wifi
try:
    allOn() #Proof of life while we're connecting



    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    # Wait for connect or fail
    max_wait = 15
    while max_wait > 0:
      if wlan.status() < 0 or wlan.status() >= 3:
        break
      max_wait -= 1
      print('waiting for connection...')
      time.sleep_ms(500)

                 
    # Handle connection error: one purple, one orange means we can't connect.

    if wlan.status() != 3:
        allOff()
        rgbTdy.color = (125, 100, 0)
        rgbTmw.color = (125, 0, 125)
        raise RuntimeError('network connection failed')




    else:
        #two greens: we're all set
        rgbTdy.color = (0, 100, 0)
        rgbTmw.color = (0, 100, 0)    
        print("* * * * * * * * * * * *")
        print('* connected           *')
        status = wlan.ifconfig()
        ipLength = len(status[0])
    #This just gives the box more chance of being aligned - there's probs a better way to do this
        if ipLength == 12:
            print( '* ip = ' + status[0] +"   *" )
        else:
            print( '* ip = ' + status[0] +" *" )
except:
    
    print('rebooting in 30 secs')
    time.sleep(30)
    print('rebooting now!')
    time.sleep(1)
    machine.reset()
    
#Set time from NTP
ntptime.timeout = 2
ntptime.settime()
t = time.localtime()
print("* Date: %02d/%02d/%d    *" %(t[2],t[1],t[0]))
print("* Time: %02d:%02d:%02d      *" %(t[3],t[4],t[5]))
print("* * * * * * * * * * * *\n")


while True:
    try:
        try: #Get the credentials first. If this fails, don't bother doing the rest
            request_url = 'https://digital.iservices.rte-france.com/token/oauth/'
            res = urequests.post(request_url, headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': apiAuth})
            oauth2 = res.json()
            auth = 1
        except:
            print("Can't get Oauth")
            auth = 0
            
        if (auth == 1):            
    #Tomorrow first. We don't need to faf around : this is the default query for RTE's API
            print('\nTOMORROW\n')
            try:
                url = "https://digital.iservices.rte-france.com/open_api/tempo_like_supply_contract/v1/tempo_like_calendars"
                headers = {"Authorization": "Bearer {}".format(oauth2["access_token"])}
                print(url, headers)
                r = urequests.get(url, headers=headers)
                s = r.text
                print('going to parse json...')

                rteReturn = r.json()
                r.close()
                print("JSON")
     
                print(rteReturn)
                rteValues = rteReturn["tempo_like_calendars"]["values"]
                tmwDate = rteValues[0]["start_date"] #to work out when it changes
                tmwColor = rteValues[0]["value"]
                t = time.localtime(time.time()+60*60*2) #it's always summer in this program
                tmwInfo = str("%02d/%02d/%d" %(t[2],t[1],t[0]), "%02d:%02d:%02d" %(t[3],t[4],t[5]), rteReturn)


            except:
                try:
    #rte API has a fallback to XML - in French (BLEU, BLANC, ROUGE). Example format :
    #<Tempo><DateHeureCreation>2023-05-28</DateHeureCreation><DateApplication>2023-05-29</DateApplication><Couleur>BLEU</Couleur></Tempo>
    #So we'll try that before giving up...

                    print('JSON was not available, trying XML...')
                    t = After  (s, "<Couleur>")
                    t = Before (t, "</Couleur>")
                    frenchTmwColor = t
                    u = After  (s, "<DateApplication>")
                    u = Before (u, "</DateApplication>")
                    tmwDate = u
                    print("Tomorrow is {}, color is {}".format(tmwDate, frenchTmwColor))

                    if frenchTmwColor == 'BLEU':
                        tmwColor = 'BLUE'
                    elif frenchTmwColor == 'BLANC':
                        tmwColor = 'WHITE'
                    elif frenchTmwColor == 'ROUGE':
                        tmwColor = 'RED'
                    else:
                        tmwColor = 'DONT_KNOW_COLOUR_TOMORROW_XML'
                    print(tmwColor)
                    
                except:

                    t = time.localtime()
                    print("no data for tomorrow")
                    print("Date: %02d/%02d/%d" %(t[2],t[1],t[0]))
                    print("Time: %02d:%02d:%02d" %(t[3],t[4],t[5]))            
                    tmwColor = "DONT_KNOW_COLOUR_TOMORROW"
                    tmwDate = "DONT_KNOW_TOMORROW" #If the request does not succeed, we don't know what date we don't have. So tmwDate must not equal tdyDate.


    #today - we need to move the start date back to midnight, and the end date forwards to midnight. The API will do the rest.
            print("\nTODAY\n")    
            try:
                t = time.localtime()
                tTmw = time.localtime(time.time()+60*60*24) #This is always tomorrow. 
                dateYdy = ("%d-%02d-%02dT00:00:00+02:00" %(t[0], t[1], t[2]))
                dateTmw = ("%d-%02d-%02dT00:00:00+02:00" %(tTmw[0], tTmw[1], tTmw[2]))
                url = ("https://digital.iservices.rte-france.com/open_api/tempo_like_supply_contract/v1/tempo_like_calendars?start_date={}&end_date={}".format(dateYdy, dateTmw))
                headers = {"Authorization": "Bearer {}".format(oauth2["access_token"])}
                print(url, headers)
                r = urequests.get(url, headers=headers)
                s=r.text #We need this for the fallback option
                print('going to parse json...')

                rteReturnTdy = r.json()
                s=r.text
                r.close()
                print(s)
                rteValuesTdy = rteReturnTdy["tempo_like_calendars"]["values"]
                t = time.localtime()
                tdyDate = rteValuesTdy[0]["start_date"] #to work out when it changes
                tdyColor = rteValuesTdy[0]["value"]
                tdyInfo = str("%02d/%02d/%d" %(t[2],t[1],t[0]), "%02d:%02d:%02d" %(t[3],t[4],t[5]), rteReturnTdy)

                                    
            except:

                try: #No JSON, maybe the XML version is available.
                    t = After  (s, "<Couleur>")
                    t = Before (t, "</Couleur>")
                    frenchTdyColor = t
                    u = After  (s, "<DateApplication>")
                    u = Before (u, "</DateApplication>")
                    tdyDate = u
                    print("Today is {}, color is {}".format(tdyDate, frenchTdyColor))

                    if frenchTdyColor == 'BLEU':
                        tdyColor = 'BLUE'
                    elif frenchTdyColor == 'BLANC':
                        tdyColor = 'WHITE'
                    elif frenchTdyColor == 'ROUGE':
                        tdyColor = 'RED'
                    else:
                        tdyColor = 'DONT_KNOW_COLOUR_TODAY_XML'
                    print(tdyColor)
                except:
                    t = time.localtime()
                    print("no data for today")
                    print("Date: %02d/%02d/%d" %(t[2],t[1],t[0]))
                    print("Time: %02d:%02d:%02d" %(t[3],t[4],t[5]))            
                    tdyColor = "DONT_KNOW_COLOUR_TODAY"
                    tdyDate = "DONT_KNOW_TODAY"
    #RTE seem to change dates oddly during the night. A first roll-over happens at 2 AM GMT, at which point both dates become identical.
    #Then at a second point, apparently around 4:10 GMT , the new tomorrow is transmitted. So between those two points,
    #both dates are identical. tdyColor is right (or will be at 6 AM, when the electrical day starts) but tmwColor may not be
    #right, so we switch it off.
                
            if tdyDate == tmwDate:
                tmwColor = "UNDEFINED"
                
    #Print to console            
            t = time.localtime()
            print("Date: %02d/%02d/%d" %(t[2],t[1],t[0]))
            print("Time: %02d:%02d:%02d" %(t[3],t[4],t[5]))            
            print('today is', tdyDate)
            print('today is', tdyColor)
            print('tomorrow is', tmwDate)
            print('tomorrow is', tmwColor, '\n')
            
    #now we get the right lights to light up      
            if tdyColor == "BLUE":
                rgbTdy.color=(0,0,100)

            elif tdyColor == "WHITE":
                rgbTdy.color=(100,100,100)
                
            elif tdyColor == "RED":
                rgbTdy.color=(100,0,0)
                
            else: #This shouldn't happen : we always know what the current color is.
                   #So the light turns pink, there's a problem.
                rgbTdy.color=(125, 0, 125)
    ###        
            
            if tmwColor == "BLUE":
                rgbTmw.color=(0,0,255)

            elif tmwColor == "WHITE":
                rgbTmw.color=(200,200,200)

            elif tmwColor == "RED":
                rgbTmw.color=(255,0,0)
                
            elif tmwColor == "DONT_KNOW_COLOUR_TOMORROW":#This means the request did not get a valid response.
                                                         #So the light turns pink, there's a problem.
                rgbTmw.color=(125, 000, 125)
                

            else: #This happens every night - no worries, we don't have the data so we switch it off.
                rgbTmw.off()
                
        else:
            t = time.localtime()
            print("There's an OAuth problem...") #OAuth error code is rgbTmw pink, rgbTdy cycling
            print("Date: %02d/%02d/%d" %(t[2],t[1],t[0]))
            print("Time: %02d:%02d:%02d" %(t[3],t[4],t[5]))
            rgbTmw.color=(125, 000, 125)
            rgbTdy.cycle() 
            
    except:
        t = time.localtime()
        print("There's a problem - possibly no connection to the internet?")
        print("Date: %02d/%02d/%d" %(t[2],t[1],t[0]))
        print("Time: %02d:%02d:%02d" %(t[3],t[4],t[5]))     
        allOn() #it's all messed up and both lights cycle through RGB until next time.
        print('I\'ll try again in 15 minutes')
        time.sleep(960)
        machine.reset()

    gc.collect()
    time.sleep(960)

