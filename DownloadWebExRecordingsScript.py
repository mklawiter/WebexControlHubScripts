#!/usr/bin/env python
""" Python Script to Download all Recordings from a WebEx site
    
This script is intended to download all recordings from a WebEx site for the purposes of backing up, transferring, or distributing recordings by authorized personnel only.
    
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
__author__ = "Matt Klawiter"
__contact__ = "mklawite@cisco.com"
__copyright__ = "Copyright 2018 by Matt Klawiter, Cisco Systems, Inc"
__date__ = "2018/2/28"
__version__ = "2.2"

#############  Imports  #############
import requests
import xml.etree.ElementTree as ET
import os
import time
import csv
import decimal

#############  Functions  #############
def xstr(s):
    return '' if s is None else str(s.text)

#############  DEFINITIONS THAT YOU MUST UPDATE  #############
url = 'https://sitename.webex.com/WBXService/XMLService'                #Update to your WebEx site
siteName = 'sitename'                                                   #Update to your WebEx site
siteID = '4444444'                                                      #Update to your WebEx site ID
apiUser = 'username'                                                    #Update to an admin username
apiPassword = 'password'                                                #Update to an admin password
soapURL = 'https://nsj1wss.webex.com/nbr/services/NBRStorageService'    #Update to your WebEx Services Site
csvFilePath = '/Recordings/'                                            #Update folder in which to save files
csvFileName = 'Recordings.csv'                                          #Update the CSV File Name as desired

#############  Definitions  #############
x = 1
delimiter = '","'
D = decimal.Decimal
TWOPLACES = D('0.01')
recordingIDs = []
recordingSizes = []
recordingFormats = []
hostIDs = []

#############   Create/Update CSV  File  #############
with open(csvFilePath + csvFileName,'w') as csvfile:
    csvfile.write('"Recording ID","Host ID","Creation Date/Time","Time Zone","File Size","Streaming URL","Download URL","Recording Type","Duration","Format","WebEx Center","Password Required","Password","Conference ID","Name"\n')
rawxml = '<?xml version="1.0" encoding="UTF-8"?><serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:serv="http://www.webex.com/schemas/2002/06/service"><header><securityContext><webExID>' + apiUser + '</webExID><password>' + apiPassword + '</password><siteName>' + siteName + '</siteName></securityContext></header><body><bodyContent xsi:type="java:com.webex.service.binding.ep.LstRecording"><listControl><startFrom>1</startFrom></listControl></bodyContent></body></serv:message>'
response = requests.post(url, data=rawxml)
if response.status_code != 200:
    # This means something went wrong.
    print('API Call Error!')
    print(response.status_code)
# Parse response into tree and find the total recordings
data = ET.fromstring(response.text)
totalRecordings = int(data[1][0][0][0].text)
print('Recording API Call:', data[0][0][0].text)
print('Total Recordings:  ', totalRecordings)
#  Loop to create CSV file of all recordings
while (x < totalRecordings):
    rawxml = '<?xml version="1.0" encoding="UTF-8"?><serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:serv="http://www.webex.com/schemas/2002/06/service"><header><securityContext><webExID>' + apiUser + '</webExID><password>' + apiPassword + '</password><siteName>' + siteName + '</siteName></securityContext></header><body><bodyContent xsi:type="java:com.webex.service.binding.ep.LstRecording"><listControl><startFrom>' + str(x) + '</startFrom></listControl></bodyContent></body></serv:message>'
    response = requests.post(url, data=rawxml)
    if response.status_code != 200:
        # This means something went wrong.
        print('API Error!')
        print(response.status_code)
    data = ET.fromstring(response.text)
    # print('Pulling ' + data[1][0][0][1].text + ' recordings starting with #', data[1][0][0][2].text)
    # Get recordings info and write to CSV File
    for child in data.iter('{http://www.webex.com/schemas/2002/06/service/ep}recording'):
        recordingID = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}recordingID'))
        hostID = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}hostWebExID'))
        recordingName = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}name'))
        recordingDate = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}createTime'))
        timeZone = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}timeZoneID'))
        recordingSize = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}size'))
        streamURL = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}streamURL'))
        downloadURL = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}fileURL'))
        recordingType = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}recordingType'))
        recordingLength = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}duration'))
        recordingFormat = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}format'))
        webexCenter = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}serviceType'))
        password = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}password'))
        passwordReq = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}passwordReq'))
        conferenceID = xstr(child.find('{http://www.webex.com/schemas/2002/06/service/ep}confID'))
        with open(csvFilePath + csvFileName,'a') as csvfile:
            csvfile.write('"' + recordingID + delimiter + hostID + delimiter + recordingDate + delimiter + timeZone + delimiter + recordingSize + delimiter + streamURL + delimiter + downloadURL + delimiter + recordingType + delimiter + recordingLength + delimiter + recordingFormat + delimiter + webexCenter + delimiter + passwordReq + delimiter + password + delimiter + conferenceID + delimiter + recordingName + '"\n')
        x += 1;
print('    Printed all', str(x - 1), 'Recordings to a CSV File')
#############  End Update CSV File  #############

#############  Now read the CSV File to get recordings  #############
with open(csvFilePath + csvFileName, 'r') as csvFile:
    readCSV = csv.reader(csvFile, delimiter=',', quotechar='"')
    next(readCSV, None) #skip headers
    for row in readCSV:
        recordingIDs.append(row[0])
        hostIDs.append(row[1])
        recordingSizes.append(D(row[4]))
        recordingFormats.append(row[9].lower())
print('\nTotal Recordings to Download:  ', len(recordingIDs))
#print('First Recording: ', recordingIDs[0], ' by: ', hostIDs[0])
totalRecordings = len(recordingIDs)
#############  End CSV File read  #############

#############  Get WebEx API ticket for download API call  #############
start = time.time()
soapHeaders = {'Content-Type' : 'text/xml; charset=utf-8', 'Accept' : 'application/soap+xml, application/dime, multipart/related, text/*', 'User-Agent' : 'Axis/1.1', 'Host' : '10.224.91.216:2001', 'Cache-Control' : 'no-cache', 'Pragma' : 'no-cache', 'SOAPAction' : '""', 'Content-Length' : '578'}
soapBody = '<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><ns1:getStorageAccessTicket soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="NBRStorageService"><siteId xsi:type="xsd:long">' + siteID + '</siteId><username xsi:type="xsd:string">' + apiUser + '</username><password xsi:type="xsd:string">' + apiPassword + '</password></ns1:getStorageAccessTicket></soapenv:Body></soapenv:Envelope>'
soapResponse = requests.post(soapURL, data=soapBody, headers=soapHeaders)
if soapResponse.status_code != 200:
    # Something went wrong.
    print('SOAP Call Error!')
    print(soapResponse.status_code)
ticket = ET.fromstring(soapResponse.text)
#############  End API ticket call  #############

#############  Loop to download all recordings  #############
x = 0
while (x < totalRecordings):
    # Update ticket if old ticket is expired
    end = time.time()
    if( (end - start) > 3300 ):
        soapHeaders = {'Content-Type' : 'text/xml; charset=utf-8', 'Accept' : 'application/soap+xml, application/dime, multipart/related, text/*', 'User-Agent' : 'Axis/1.1', 'Host' : '10.224.91.216:2001', 'Cache-Control' : 'no-cache', 'Pragma' : 'no-cache', 'SOAPAction' : '""', 'Content-Length' : '578'}
        soapBody = '<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><ns1:getStorageAccessTicket soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="NBRStorageService"><siteId xsi:type="xsd:long">' + siteID + '</siteId><username xsi:type="xsd:string">' + apiUser + '</username><password xsi:type="xsd:string">' + apiPassword + '</password></ns1:getStorageAccessTicket></soapenv:Body></soapenv:Envelope>'
        soapResponse = requests.post(soapURL, data=soapBody, headers=soapHeaders)
        if soapResponse.status_code != 200:
            # Something went wrong.
            print('SOAP Call Error!')
            print(soapResponse.status_code)
        ticket = ET.fromstring(soapResponse.text)
        start = time.time()
    print('Pulling Recording #' + str(x+1), '  -  Recording ID:', recordingIDs[x] + ',', 'User ID:', hostIDs[x], '...')
    # Skip download if file has been downloaded previously
    if(os.path.isfile(csvFilePath + str(recordingIDs[x]) + '.' + str(recordingFormats[x]))):
        print('    Recording already downloaded.  Skipping...')
        x += 1
    # Skip download if recording is too large (greater than 1.5 GB).  Download manually!
    elif(recordingSizes[x] > D('1500.0')):
        print('    RECORDING IS TOO LARGE FOR THIS SCRIPT (' + str((recordingSizes[x] / D('1000')).quantize(TWOPLACES)) + 'GB), YOU MUST MANUALLY DOWNLOAD.  Skipping...')
        with open(csvFilePath + str(recordingIDs[x]) + '.txt', 'w') as arfFile:
            arfFile.write('     The recording was too large for the script.  You must manually download or it will be lost.')
        x += 1
    else:
        #  Otherwise call API to download file  
        soapHeaders = {'Content-Type' : 'text/xml; charset=utf-8', 'Accept' : 'application/soap+xml, application/dime, multipart/related, text/*', 'User-Agent' : 'Axis/1.1', 'Host' : 'localhost:7001', 'Cache-Control' : 'no-cache', 'Pragma' : 'no-cache', 'SOAPAction' : '""', 'Content-Length' : '605'}
        soapBody = '<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><ns1:downloadNBRStorageFile soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="NBRStorageService"><siteId xsi:type="xsd:long">' + siteID + '</siteId><recordId xsi:type="xsd:long">' + recordingIDs[x] + '</recordId><ticket xsi:type="xsd:string">' + str(ticket[0][0][0].text) + '</ticket></ns1:downloadNBRStorageFile></soapenv:Body></soapenv:Envelope>'
        soapResponse = requests.post(soapURL, data=soapBody, headers=soapHeaders, stream=True)
        if soapResponse.status_code != 200:
            # Something went wrong.
            print('           SOAP Download Error!  -  ', soapResponse.status_code)
            #print(soapResponse.text)
            errorResponse = ET.fromstring(soapResponse.text)
            print('          ', errorResponse[0][0][1].text)
            # If the recording no longer exists, it will throw this error.  Create a placeholder text file.
            if (errorResponse[0][0][1].text == 'The recording you are looking for does not exist or is no longer available.'):
                with open(csvFilePath + str(recordingIDs[x]) + '.txt', 'w') as arfFile:
                    arfFile.write('     The recording you are looking for does not exist or is no longer available.')
                print('    Recording does not exist.  Skipping...')
                x += 1
        else:
            # Download recording, and parse the ARF data to a file
            with open(csvFilePath + 'RecordingTempFile.zip', 'wb') as dlFile:
                for chunk in soapResponse.iter_content(chunk_size=1024*1024):
                    dlFile.write(chunk)
            splitRecording = open(csvFilePath + 'RecordingTempFile.zip', 'rb').read().split(bytearray('\r\n\r\n','utf8'))
            with  open(csvFilePath + str(recordingIDs[x]) + '.' + str(recordingFormats[x]), 'wb') as arfFile:
                arfFile.write(splitRecording[3])
            # Clean up temp file
            if os.path.isfile(csvFilePath + 'RecordingTempFile.zip'):
                os.remove(csvFilePath + 'RecordingTempFile.zip')
            # Do not progress to next download if this download is 0 bytes.  Something went wrong, repeat download!
            if (os.stat(csvFilePath + str(recordingIDs[x]) + '.' + str(recordingFormats[x])).st_size > 0):
                x += 1
            else:
                print('    Recording download error.  Retrying...')
#############  End Loop to download recordings  #############

print('Download complete.  Finished at Recording #', str(x), '\n')


