import requests
import json
import getpass
import sys
import os,os.path
import datetime
import base64
import urllib
import logging
import unicodedata
import re

# VARIABLES
current_directory = os.getcwd()
folder = ''
fileNamePattern = ''
company = ''
readed = False
yesForAll = False
nowDate = datetime.datetime.now()
endDate = nowDate.strftime('%Y-%m-%d')
startDate = (nowDate - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
server_base_adress = "doc-server-int.saphety.com/Doc.WebApi.Services"
arguments = {}
token = ''
headers = {}
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='sin-pull.log')

def readContentType(contentType):
  fileType = '.txt'

  if contentType == 'application/xml' or contentType == 'text/xml':
    fileType = '.xml'
  elif contentType == 'application/pdf':
    fileType = '.pdf'
  elif contentType == 'text/plain':
    fileType = '.txt'
  elif contentType == 'application/json':
    fileType = '.json'

  return fileType

def getToken(username, password):
  service_url = "https://" + server_base_adress + "/api/Account/token"
  payload = {
      'Username': username,
      'Password': password
  }
  request_data=json.dumps(payload)
  headers = { 'content-type': 'application/json'}
  response = requests.request("POST", service_url, data=request_data, headers=headers)
  
  token = checkResultOfRequest(response)
  return token

def checkResultOfRequest(response):
  json_response = json.loads(response.text)

  if json_response["IsValid"]:
    result = json_response["Data"]
  else:
    printErrors(json_response["Errors"])
    sys.exit()
  
  return result

def printErrors(errors):
  for idx, val in enumerate(errors):
    print('#{idx} ERROR: {error}'.format(idx=idx, error=val['Code']))
    logging.error(' ERROR: ' + val['Code'])

def getShipmentContent(id, docId, idx):
  global headers
  global arguments
  global current_directory

  service_url_doc = "https://" + server_base_adress + "/api/Document/projectedDocument/" + str(docId)
  response_doc = requests.request("GET", service_url_doc, headers=headers)

  if response_doc.status_code == 200:
    response_doc = checkResultOfRequest(response_doc)

    if '--fileNamePattern' in arguments:      
      fileName = arguments['--fileNamePattern']
      fileName = fileName.replace('DocType', response_doc['DocumentType'])
      fileName = fileName.replace('DocNumber', str(response_doc['ID']))
      fileName = fileName.replace('DocID', response_doc['DocNumber'])
      fileName = fileName.replace('DocSender', response_doc['SenderEntitySubDivision'])
      fileName = fileName.replace('DocDestination', response_doc['DestinationEntitySubDivision'])
      fileName = fileName.replace('DocDate', response_doc['DocumentDate'])

      if fileName == arguments['--fileNamePattern']:
        fileName = id
    else:
      fileName = id 

    service_url = "https://" + server_base_adress + "/api/DocumentPull/OutboundShippments/" + id
    response = requests.request("GET", service_url, headers=headers)

    if response.status_code == 200:
      content = response.text
      isBinary = False

      fileType = readContentType(response.headers['Content-Type'])
      
      if '--content' in arguments:
        typeContent = arguments['--content']
        service_url_content = "https://" + server_base_adress + "/api/Streaming/Document/content/" + str(response_doc['ID']) + '/' + typeContent + '/false'
        req_response = requests.request("GET", service_url_content, headers=headers)

        if req_response.status_code == 200:
          req = urllib.request.Request(service_url_content, headers=headers)
          content_2 = urllib.request.urlopen(req)
          fileType = readContentType(content_2.headers['Content-Type'])
          isBinary = True
        else:
          saveFileWithErrors(fileName, req_response, idx, id, False)
          return

      if '--folder' in arguments:
        path = current_directory + arguments['--folder']
      else:
        path = current_directory

      fileName = getValidFileName(path, fileName, fileType)
      final_name = os.path.join(path, fileName)

      print('#' + idx + ' Saving ' + fileName + ' in ' + path + ' - DocumentID: ' + id)
      logging.info('Saving file: ' + fileName + ' in ' + path + ' - DocumentID: ' + id)
      
      if isBinary:
        file = open(final_name, "wb")
        file.write(content_2.read())
      else:
        file = open(final_name, "w")
        file.write(content)
      file.close()
    else:
      saveFileWithErrors(fileName, response, idx, id)
  else:
    saveFileWithErrors(id, response_doc, idx, id)
  
def getValidFileName(path, fileName, fileType):
  idx = 1

  fileName = slugify(fileName)
  newFileName = fileName
  fileAlreadyExists = os.path.exists(path + '\\' + newFileName + fileType)

  while fileAlreadyExists:
    newFileName = fileName + '_' + str(idx)
    idx += 1
    fileAlreadyExists = os.path.isfile(path + '\\' + newFileName + fileType)
  
  final_name = newFileName + fileType

  return final_name
    
def saveFileWithErrors(fileName, response, idx, docId, isInternal = True):
  global arguments
  global current_directory

  if '--folder' in arguments:
    path = current_directory + arguments['--folder']
  else:
    path = current_directory

  fileName = 'ERROR_' + fileName
  fileName = getValidFileName(path, fileName, '.err')
  final_name = os.path.join(path, fileName)

  if isInternal:
    json_response = json.loads(response.text)
    print('#' + idx + ' ERROR [' + response.reason + ']: ' + json_response[0]['Code'] + ' - Saving file: ' + fileName + ' in ' + path + ' - DocumentID: ' + docId)
    logging.error(' ERROR [' + response.reason + ']: ' + json_response[0]['Code'] + ' - Saving file: ' + fileName + ' in ' + path + ' - DocumentID: ' + docId)
  else:
    print('#' + idx + ' ERROR [' + str(response.status_code) + ']: ' + response.reason + ' - Saving file: ' + fileName + ' in ' + path + ' - DocumentID: ' + docId)
    logging.error(' ERROR [' + str(response.status_code) + ']: ' + response.reason + ' - Saving file: ' + fileName + ' in ' + path + ' - DocumentID: ' + docId)

  file = open(final_name, "w")
  file.write(response.text)
  file.close()

def getAllArguments():
  global arguments
  global startDate
  global endDate
  global company
  global readed
  global yesForAll

  run = False
  for idx, val in enumerate(sys.argv):
    next_indx = idx + 1
    if val == '--help':
      listHelp()
      exit()
    if val == '--username' or val == '--password' or val == '--folder' or val == '--startDate' or val == '--endDate' or val == '--company' or val == '--fileNamePattern' or val == '--content':
      arguments[val] = sys.argv[next_indx]
    if val == '--readed':
      readed = True
    if val == '--y':
      yesForAll = True

  if '--folder' in arguments:
    folderExists = os.path.isdir(current_directory + arguments['--folder'])
    if not folderExists:
      print('ERROR: The folder "' + current_directory + arguments['--folder'] + '" does not exist!')
      logging.error('ERROR: The folder "' + current_directory + arguments['--folder'] + '" does not exist!')
      exit()

  if '--fileNamePattern' in arguments:
    if 'DocType' not in arguments['--fileNamePattern'] and 'DocNumber' not in arguments['--fileNamePattern'] and 'DocID' not in arguments['--fileNamePattern'] and 'DocSender' not in arguments['--fileNamePattern'] and 'DocDestination' not in arguments['--fileNamePattern'] and 'DocDate' not in arguments['--fileNamePattern']:
      print('ERROR: The fileNamePattern "' + arguments['--fileNamePattern'] + '" does not contain a defined tag!')
      logging.error('ERROR: The fileNamePattern "' + arguments['--fileNamePattern'] + '" does not contain a defined tag!')
      exit()

  if '--startDate' in arguments:
    startDate = arguments['--startDate']

  if '--endDate' in arguments:
    startDate = arguments['--endDate']

  if '--company' in arguments:
    company = arguments['--company']

  getDataToGetToken()
      
def getDataToGetToken():
  global token
  global arguments

  if not '--username' in arguments:
    username = input("Username: ")
    arguments['--username'] = username

  if not '--password' in arguments:
    password = getpass.getpass("Password: ")
  else:
    password = arguments['--password']

  logging.info('Beginning download process!')
  logging.info('Argument List: ' + str(arguments))

  token = getToken(arguments['--username'], password)

  runApplication()

  logging.info('Ending process!')
    
def listHelp():
  print('HELP')
  print('* [--help] to see a list of help.')
  print('* [--y] to say yes to all. Silent mode')
  print('* [--readed] to see only de readed documents.')
  print('* [--folder] to defined a folder to save the files, based on the current file folder. Ex: \SaphetyPull')
  print('* [--username] to defined your username. Ex: --username saphety')
  print('* [--password] to defined your password. Ex: --password invoice_network')
  print('* [--startDate] to defined your start date. Ex: --startDate 2021-01-01')
  print('* [--endDate] to defined your end date. Ex: --endDate 2022-01-01')
  print('* [--company] to defined your associated company. Ex: --company PT507957547')
  print('* [--content] to defined your return file type. You can choose between PDF and UBL21. Ex: --content PDF')
  print('* [--fileNamePattern] to defined the final file name. Use the next tags to change the file name.')
  print('**  [DocType] - Document type')
  print('**  [DocNumber] - Document number (unique)')
  print('**  [DocID] - Document ID  (unique)')
  print('**  [DocSender] - Document sender VAT')
  print('**  [DocDestination] - Document destination VAT')
  print('**  [DocDate] - Document date')
  print('**  EXAMPLE:')
  print('***   Command > ... --fileNamePattern DocType-DocNumber ')
  print('***   Result  > INVOICE-12345.xml ')
  print('')
  print('FULL EXAMPLE')
  print('> pull_integration.py --username saphety --password invoice_network --startDate 2021-01-01 --readed --fileNamePattern DocType-DocNumber --content PDF')
  print('')
  print('LOGS')
  print('* You can see the log file in the current file folder. File name: sin-pull.log')

def runApplication():
  global headers
  global startDate
  global endDate
  global company
  global readed
  global yesForAll

  # Count the number of unread files
  service_url = """{ServerBaseUrl}/api/DocumentPull/OutboundShippments/count""".format(
      ServerBaseUrl=server_base_adress
  )
  service_url = "https://" + service_url
  print ('** CALLING ' + service_url + ' **')
  #headers
  headers = {
      'Content-Type': 'application/json',
      'Authorization': 'bearer ' + token
      }
  # payload as json
  if company == '':
    payload_count = {
      'DeliveredStatus': readed,
      'CreationDateStart': startDate,
      'CreationDateEnd': endDate
    }
  else:
    payload_count = {
      'DeliveredStatus': readed,
      'CreationDateStart': startDate,
      'CreationDateEnd': endDate,
      'DestinationEntityCode': company
    }
  request_data=json.dumps(payload_count)
  # Send the request (POST). The service return a request id
  response = requests.request("POST", service_url, data=request_data, headers=headers)

  # formating the response to json for visualization purposes only
  json_response = json.loads(response.text)
  nFilesToreceive = json_response["Data"]
  print("Files to receive: " + str(nFilesToreceive))
  logging.info('Files to receive: ' + str(nFilesToreceive))

  if int(nFilesToreceive) > 0:
    if not yesForAll:
      download = input('Do you want to download all the files? (Yes/No): ')
    else:
      print('You will download all files now! Silent mode (--y)')
      logging.info('Downloaded all files automatic! Silent mode (--y)')
      download = 'Yes'

    if download == 'Yes':
      # Start Getting Files to Receive
      service_url = """{ServerBaseUrl}/api/DocumentPull/OutboundShippments/search""".format(
          ServerBaseUrl=server_base_adress
      )
      service_url = "https://" + service_url
      print ('** CALLING ' + service_url + ' **')
      #headers
      headers = {
          'Content-Type': 'application/json',
          'Authorization': 'bearer ' + token
          }
      # payload as json
      payload = {
        'RestrictionCriteria': payload_count,
        "PageNumber": 0,
        "RowsPerPage": 9999
      }
      request_data=json.dumps(payload)
      # Send the request (POST). The service return a request id
      response = requests.request("POST", service_url, data=request_data, headers=headers)

      # formating the response to json for visualization purposes only
      json_response = json.loads(response.text)
      #print(json.dumps(json_response, indent=4))

      print("If you want to stop, press CTRL + C!")
      for idx, shipment in enumerate(json_response["Data"]):
        getShipmentContent(shipment["Id"], shipment["DocumentId"], str(idx))
    else:
      logging.info('The user dont want to download the files')
  else:
    print('There are no documents to pull!')
    logging.info('There are no documents to pull!')

def slugify(value, allow_unicode=False):
  value = str(value)

  if allow_unicode:
      value = unicodedata.normalize('NFKC', value)
  else:
      value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')

  value = re.sub(r'[^\w\s-]', '', value.lower())
  return re.sub(r'[-\s]+', '-', value).strip('-_')

#STARTING
getAllArguments()
