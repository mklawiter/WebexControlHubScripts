#!/usr/bin/env python
""" Python Script to Delete Users from an Org in Control Hub
    
This script is designed to delete users from a Control Hub organization based on an INPUT CSV file with user emails.
The script is designed to be executed by users with "full admin" role in the org.
Output file called Errors.csv is generated at the end in the same directory as the input CSV file 
(Errors.csv will be empty if the script runs successfully without errors)
Tested with Python version 3.6
The script is limited to only allow 100 users per input file.
If you need to delete more than 100 users then you need to split users into multiple CSV input files or modify the script.

The CSV file should be created using the format from the CSV export from Control Hub.
- Keep the rows of users that should be deleted and REMOVE USERS who should NOT be deleted
- Do not delete the header line, or the first user to delete will be skipped
- Very little validation is done of the input file.  Deleting fields can break this script.
- (The fourth field of each row is the email of the user that will be deleted)
- IMPORTANT:  THE FILE SHOULD ONLY HAVE ENTRIES OF USERS THAT SHOULD BE DELETED

"""
__author__ = "Matt Klawiter"
__date__ = "2020/4/29"

#############  Imports  #############
import requests
import json
import os
import csv
import urllib
import time

#############  Definitions  #############
csvFilePath = ''                                                        # Update this value to skip entering command line input
accessToken = ''                                                        # Update this value to skip entering command line input
loopCount = 0
deletedCount = 0
errorCount = 0
userEmails = []
errorMessage = ''
listPeopleURL = 'https://webexapis.com/v1/people'                  # Webex CH List People API URL
deletePersonURL = 'https://webexapis.com/v1/people/'               # Webex CH Delete Person API URL
getMyDetailsURL = 'https://webexapis.com/v1/people/me'             # Webex CH Get My Details API URL

#############   User Input and Validation  #############
print('This script requires two inputs:')
print('    1. The full file path on your device for an input CSV file\n       (ex: C:\Scripts\exported_file.csv on Windows or ~/Scripts/exported_file.csv on Mac)\n')
print('    2. An access token used to authorize the API calls\n       (You can get yours from https://developer.webex.com/docs/api/getting-started)')
print('    If you changed these variables in the script itself, it will attempt to validate and use those values instead\n')
validationSuccess = 0
# Loop to allow the user to input a file path and file name until successful.
while (validationSuccess == 0):
    if not csvFilePath :
        csvFilePath = input('Please enter the full file path of the CSV file you wish to use:  ')
    # Validate the Input CSV file exists.
    csvFilePath = os.path.expanduser(csvFilePath)
    if( not os.path.isfile(csvFilePath) ):
        print('No Input CSV file found on your device at: ' + csvFilePath)
        print('Please check the file path you entered above and try again.\n')
        csvFilePath = ''
    else:
        validationSuccess = 1
print('Input CSV file found at: ', csvFilePath, '\n')
errorFilePath = os.path.join(os.path.dirname(csvFilePath),'Errors.csv')
validationSuccess = 0
# Loop to allow the user to input an access token until successful.
while (validationSuccess == 0):
    if not accessToken :
        accessToken = input('Please enter your access token:  ')
    # Get People API Call to validate access token.
    validationResponse = requests.get(getMyDetailsURL,
                headers={'Authorization': 'Bearer ' + accessToken})
    if validationResponse.status_code == 401:
        # This means the access token was invalid.
        print('Access Token was invalid.  Please check your access token was entered correctly and hasn\'t expired and try again below.\n')
        accessToken = ''
    else:
        validationSuccess = 1
print('Input file and Access Token have validated succesfully.\n')
#############   End User Input  #############

#############   Read in CSV File of Users to Delete  #############
# The CSV file should be created from the CSV export from control hub.
# Keep the rows of users that should be deleted and REMOVE USERS who should NOT be deleted
# Do not delete the header line, or the first user to delete will be skipped
# Very little validation is done of the input file.  Deleting fields will break this script.
# IMPORTANT:  THE FILE SHOULD ONLY HAVE ENTRIES OF USERS THAT SHOULD BE DELETED
#
with open(csvFilePath, 'r') as csvFile:
    readCSV = csv.reader(csvFile, delimiter=',', quotechar='"')
    next(readCSV, None) #skip header line
    for row in readCSV:
        if len(row) >= 3 and row[3] != '':
            userEmails.append(row[3])
totalUsers = len(userEmails)
# Check to prevent the script from deleting more than 100 users at a time.
# Modify or delete this IF statement if you want to delete more than 100 users at once.
if totalUsers > 100:
    print('You have attempted to delete more than 100 users.  Please divide your input CSV file into multiple files of 100 users or less and run again.\n')
    exit()
#############  End CSV File read  #############

#############  User Confirmation  #############
# Check to make sure they want to delete the number of users found in the input CSV file
print('Total Users to Delete:', str(totalUsers))
proceed = input('Do you want to proceed?  (Y/N)  ')
if proceed.upper() != 'Y' and proceed.upper() != 'YES':
    print('You have chosen to quit without deleting users.  Ending script.\n')
    exit()
print('Delete in progress.  Please wait, the script takes 2 - 3 seconds per user on average...\n')
#############  End User Confirmation  #############

# Create CSV file for error tracking
with open(errorFilePath,'w') as csvfile:
    csvfile.write('User Email,API Call Response Code,Response Message\n')

#############   Loop to Delete Users from the CSV file  #############
while (loopCount < totalUsers):

    #############   API Call to get UserID using Email  #############
    # Get People API Call
    response = requests.get(listPeopleURL + '?email=' + urllib.parse.quote_plus(userEmails[loopCount]),
                headers={'Authorization': 'Bearer ' + accessToken})
    # Pausing script for a 429 Error
    while response.status_code == 429:
        print('Webex returned a 429 response (too many API calls at once).  Pausing script for 30 seconds...')
        time.sleep(30)
        response = requests.get(listPeopleURL + '?email=' + urllib.parse.quote_plus(userEmails[loopCount]),
            headers={'Authorization': 'Bearer ' + accessToken})
    if response.status_code != 200 or len(response.json()['items']) == 0:
        # This means something went wrong.
        if response.status_code != 200:
            print('    Error: Get User ID API call error', str(response.status_code),'on user', str(userEmails[loopCount]))
            errorMessage = response.json()['message']
        else:
            print('    Error: User not found for email', str(userEmails[loopCount]))
            errorMessage = 'No user found with that email.'
        with open(errorFilePath,'a') as csvfile:
            csvfile.write(str(userEmails[loopCount]) + ',' + str(response.status_code) + ',' + errorMessage + '\n')
        errorCount += 1
    else:
    #############  End API Call to get UserID  #############

        #############  Delete Users based on userID (this only occurs if previous call succeeded) #############
        for users in response.json()['items']:
            # Delete API Call
            deleteResponse = requests.delete(deletePersonURL + users['id'],
                                headers={'Authorization': 'Bearer ' + accessToken})
            # Pausing script for a 429 Error
            while deleteResponse.status_code == 429:
                print('Webex returned a 429 response (too many API calls at once).  Pausing script for 30 seconds...')
                time.sleep(30)
                deleteResponse = requests.delete(deletePersonURL + users['id'],
                    headers={'Authorization': 'Bearer ' + accessToken})
            if deleteResponse.status_code != 204:
                # This means something went wrong.
                print('    Error: Delete User API call error', str(deleteResponse.status_code), 'on user', str(userEmails[loopCount]))
                errorMessage = deleteResponse.json()['message']
                with open(errorFilePath,'a') as csvfile:
                    csvfile.write(str(userEmails[loopCount]) + ',' + str(deleteResponse.status_code) + ',' + errorMessage + '\n')
                errorCount += 1
            else:
                deletedCount += 1
                print('Deleted user #' + str(deletedCount) + ':  ' + str(userEmails[loopCount]))
        #############  End Delete Users based on userID #############
    
    loopCount += 1
#############  End Loop to Delete Users  #############
        
print('\nDelete complete.  Deleted', str(deletedCount), 'users, with', str(errorCount), 'errors.')
if errorCount > 0:
    print('Please check the Errors.csv file for users that were unable to be deleted.')
print()

"""
Copyright 2020 <Cisco Systems inc>
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
