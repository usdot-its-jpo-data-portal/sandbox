import os
import json
from sodapy import Socrata
import boto3
import time
import datetime
import urllib.request
import requests
from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings()
import logging

'''
This is a timed lambda function that runs every hour to check for new Wyoming CV Pilot Traveler Information Messages on 
the s3 bucket usdot-its-cvpilot-public-data and add them to the sample dataset on data.transportation.gov. If a new data
file is found, the file is opened and read line-by-line. The Traveler Information Messages are then transcribed from their current
json format, to a flat json to work with the Socrata backend on data.transportation.gov. The transcribed data is uploaded
to data.transportation.gov through the Socrata API. The code then checks the total number of rows in the sample dataset,
if the number exceeds 3 million, the difference is deleted from the dataset. This maintains the sample dataset as easily
accessible on data.transportation.gov.

Requires:
- Uploading to AWS requires packaging the source code with the Python extensions into a single zip file. This code requires
the Python requests library to be packaged with the source code to work on AWS.
- The user must edit the USERNAME, PASSWORD and API_KEY fields below to include their own Socrata credentials.
'''

logger = logging.getLogger()
logger.setLevel(logging.INFO)
USERNAME = ""
PASSWORD = ""
API_KEY = ""

def setMetadata(formatted_tim, tim_dict):
	'''
	Reads the metadata section of the Wyoming CV Pilot Traveler Information Messages and flattens them into
	the data.transportation.gov column headers.

	Parameters:
		formatted_tim: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		tim_dict: Dict containing individual TIM from the Wyoming CV Pilot data file truncated to 
		include just metadata.

	Returns:
		formatted_tim with additional keys 
	'''
	formatted_tim['metadata_generatedAt'] = tim_dict['recordGeneratedAt'].replace('Z[UTC]','')
	formatted_tim['metadata_recordGeneratedBy'] = tim_dict['recordGeneratedBy']
	formatted_tim['metadata_logFileName'] = tim_dict['logFileName']
	formatted_tim['metadata_securityResultCode'] = tim_dict['securityResultCode']
	formatted_tim['metadata_sanitized'] = str(tim_dict['sanitized'])
	formatted_tim['metadata_payloadType'] = tim_dict['payloadType']
	formatted_tim['metadata_recordType'] = tim_dict['recordType']
	formatted_tim['metadata_serialId_streamId'] = tim_dict['serialId']['streamId']
	formatted_tim['metadata_serialId_bundleSize'] = tim_dict['serialId']['bundleSize']
	formatted_tim['metadata_serialId_bundleId'] = tim_dict['serialId']['bundleId']
	formatted_tim['metadata_serialId_recordId'] = tim_dict['serialId']['recordId']
	formatted_tim['metadata_serialId_serialNumber'] = tim_dict['serialId']['serialNumber']
	formatted_tim['metadata_receivedAt'] = tim_dict['odeReceivedAt'].replace('Z[UTC]','')
	formatted_tim['metadata_rmd_elevation'] = tim_dict['receivedMessageDetails']['locationData']['elevation']
	formatted_tim['metadata_rmd_heading'] = tim_dict['receivedMessageDetails']['locationData']['heading']
	formatted_tim['metadata_rmd_latitude'] = tim_dict['receivedMessageDetails']['locationData']['latitude']
	formatted_tim['metadata_rmd_longitude'] = tim_dict['receivedMessageDetails']['locationData']['longitude']
	formatted_tim['metadata_rmd_speed'] = tim_dict['receivedMessageDetails']['locationData']['speed']
	formatted_tim['metadata_rmd_rxSource'] = tim_dict['receivedMessageDetails']['rxSource']
	formatted_tim['metadata_schemaVersion'] = tim_dict['schemaVersion']
	return formatted_tim

def setMiscellaneous(formatted_tim, tim_dict):
	'''
	Reads data not in a specific section of the Wyoming CV Pilot Traveler Information Messages and flattens them into
	the data.transportation.gov column headers.

	Parameters:
		formatted_tim: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		tim_dict: Dict containing individual TIM from the Wyoming CV Pilot data file

	Returns:
		formatted_tim with additional keys 
	'''
	formatted_tim['dataType'] = tim_dict.get('dataType','')
	formatted_tim['messageId'] = tim_dict.get('data',{}).get('MessageFrame',{}).get('messageId','')
	return formatted_tim

def setTravelerInformation(formatted_tim,tim_dict):
	'''
	Reads the traveler information section of the Wyoming CV Pilot Traveler Information Messages and flattens them into
	the data.transportation.gov column headers.

	Parameters:
		formatted_tim: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		tim_dict: Dict containing individual TIM from the Wyoming CV Pilot data file truncated to 
		include just payload/data/MessageFrame/value/TravelerInformation.

	Returns:
		formatted_tim with additional keys 
	'''
	formatted_tim['travelerinformation_timeStamp'] = tim_dict.get('timeStamp', '')
	formatted_tim['travelerinformation_packetID'] = tim_dict.get('packetID', '')
	formatted_tim['travelerinformation_urlB'] = tim_dict.get('urlB', '')
	formatted_tim['travelerinformation_msgCnt'] = tim_dict.get('msgCnt', '')
	return formatted_tim

def setTravelerDataFrame(formatted_tim, tim_dict):
	'''
	Reads the traveler dataframe section of the Wyoming CV Pilot Traveler Information Messages and flattens them into
	the data.transportation.gov column headers. If regions/GeographicalPath is in the traveler dataframe setRegions is
	called.

	Parameters:
		formatted_tim: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		tim_dict: Dict containing individual TIM from the Wyoming CV Pilot data file truncated to 
		include just payload/data/MessageFrame/value/TravelerInformation/dataFrames/TravelerDataFrame.

	Returns:
		formatted_tim with additional keys 
	'''
	if 'regions' in tim_dict:
		if 'GeographicalPath' in tim_dict['regions']:
			formatted_tim = setRegions(formatted_tim, tim_dict['regions']['GeographicalPath'])
	formatted_tim['travelerdataframe_durationTime'] = tim_dict.get('duratonTime')
	formatted_tim['travelerdataframe_sspMsgRights1'] = tim_dict.get('sspMsgRights1')
	formatted_tim['travelerdataframe_sspMsgRights2'] = tim_dict.get('sspMsgRights2')
	formatted_tim['travelerdataframe_startYear'] = tim_dict.get('startYear')
	formatted_tim['travelerdataframe_msgId_crc'] = str(tim_dict.get('msgId',{}).get('roadSignID',{}).get('crc'))
	formatted_tim['travelerdataframe_msgId_viewAngle'] = str(tim_dict.get('msgId',{}).get('roadSignID',{}).get('viewAngle'))
	formatted_tim['travelerdataframe_msgId_mutcdCode'] = str(tim_dict.get('msgId',{}).get('roadSignID',{}).get('mutcdCode'))
	formatted_tim['travelerdataframe_msgId_elevation'] = tim_dict.get('msgId',{}).get('roadSignID',{}).get('position',{}).get('elevation')
	formatted_tim['travelerdataframe_msgId_lat'] = tim_dict.get('msgId',{}).get('roadSignID',{}).get('position',{}).get('lat')
	formatted_tim['travelerdataframe_msgId_long'] = tim_dict.get('msgId',{}).get('roadSignID',{}).get('position',{}).get('long')
	formatted_tim['travelerdataframe_priority'] = tim_dict.get('priority')
	formatted_tim['travelerdataframe_content_itis'] = tim_dict.get('content',{}).get('advisory',{}).get('SEQUENCE',{}).get('item', {}).get('itis')
	formatted_tim['travelerdataframe_url'] = tim_dict.get('url')
	formatted_tim['travelerdataframe_sspTimRights'] = tim_dict.get('sspTimRights')
	formatted_tim['travelerdataframe_sspLocationRights'] = tim_dict.get('sspLocationRights')
	formatted_tim['travelerdataframe_frameType'] = str(tim_dict.get('frameType'))
	formatted_tim['travelerdataframe_startTime'] = tim_dict.get('startTime')
	return formatted_tim

def setRegions(formatted_tim, tim_dict):
	'''
	Reads the regions part of the traveler dataframe section of the Wyoming CV Pilot Traveler Information Messages
	and flattens them into the data.transportation.gov column headers.

	Parameters:
		formatted_tim: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		tim_dict: Dict containing individual TIM from the Wyoming CV Pilot data file truncated to 
		include just payload/data/MessageFrame/value/TravelerInformation/dataFrames/TravelerDataFrame/regions/GeographicalPath

	Returns:
		formatted_tim with additional keys 
	'''	
	formatted_tim['travelerdataframe_closedPath'] = str(tim_dict.get('closedPath'))
	formatted_tim['travelerdataframe_anchor_elevation'] = tim_dict.get('anchor',{}).get('elevation')
	formatted_tim['travelerdataframe_anchor_lat'] = tim_dict.get('anchor',{}).get('lat')
	formatted_tim['travelerdataframe_anchor_long'] = tim_dict.get('anchor',{}).get('long')
	formatted_tim['travelerdataframe_name'] = tim_dict.get('name')
	formatted_tim['travelerdataframe_laneWidth'] = tim_dict.get('laneWidth')
	formatted_tim['travelerdataframe_directionality'] = str(tim_dict.get('directionality'))
	formatted_tim['travelerdataframe_desc_nodes'] = str(tim_dict.get('description',{}).get('path',{}).get('offset',{}).get('xy',{}).get('nodes',{}).get('NodeXY'))
	formatted_tim['travelerdataframe_desc_scale'] = tim_dict.get('description',{}).get('path',{}).get('scale')
	formatted_tim['travelerdataframe_id'] = str(tim_dict.get('id'))
	formatted_tim['travelerdataframe_direction'] = str(tim_dict.get('direction'))
	return formatted_tim

def process_tim(tim_in):
	'''
	The main method that processes each Traveler Information Message from the input file. Reads JSON, calls 
	setMetadata, setMiscellaneous, setTravelerInformation and setTravelerDataFrame for each file. 

	Parameters:
		tim_in: A list of strings containing Traveler Information Messages from the Wyoming CV Pilot

	Returns:
		tim_list: A list of processed Travler Information Messages to be uploaded to data.transportation.gov
	'''
	tim_list = []
	for tim in tim_in:
		try:
			tim_dict = json.loads(tim)
			formatted_tim = {}
			formatted_tim = setMetadata(formatted_tim, tim_dict['metadata'])
			formatted_tim = setMiscellaneous(formatted_tim, tim_dict['payload'])
			formatted_tim = setTravelerInformation(formatted_tim, tim_dict['payload']['data']['MessageFrame']['value']['TravelerInformation'])
			formatted_tim = setTravelerDataFrame(formatted_tim, tim_dict['payload']['data']['MessageFrame']['value']['TravelerInformation']['dataFrames']['TravelerDataFrame'])
			tim_list.append(formatted_tim)
		except:
			pass 
	return tim_list

def lambda_handler(event, context):
	'''
	Method called by Amazon Web Services when the lambda trigger fires. This lambda is configured to be triggered
	every hour. This method connects to the s3 bucket usdot-its-cvpilot-public-data, determines the current
	datetime and builds the folder structure to search based on the datetime one hour ago. Checks if any files have
	been added in the past hour. If so, opens them and reads line-by-line to bsm_in. Uploads processed results to
	data.transportation.gov. Checks if total number of rows is greater than 3 million and deletes excess rows.

	Parameters:
		event, context: Amazon Web Services required parameters. Describes triggering event, not needed for this function.
	'''	
	start = time.time()
	s3 = boto3.resource('s3')
	logger.info("Connecting to bucket")
	mybucket = s3.Bucket('usdot-its-cvpilot-public-data')

	logger.info("Loading JSON")
	timenow = datetime.datetime.now(tz = datetime.timezone(datetime.timedelta(hours=0)))
	timestamp = timenow - datetime.timedelta(hours = 1, seconds = timenow.second, microseconds = timenow.microsecond)
	now = timestamp + datetime.timedelta(hours = 1)
	prefix = "wydot/TIM/{}/{:02}/{:02}/{:02}/".format(timestamp.year,timestamp.month,timestamp.day,timestamp.hour)
	tim_list = []
	for record in mybucket.objects.filter(Prefix=prefix):
		if record.last_modified > timestamp and record.last_modified <= now:
			tim_in = record.get()['Body'].read().decode('utf-8')
			tim_in = tim_in.splitlines()
			tim_list += process_tim(tim_in)

	if timenow.hour != timestamp.hour:
		prefix = "wydot/TIM/{}/{:02}/{:02}/{:02}/".format(timestamp.year,timestamp.month,timestamp.day,timenow.hour)
		for record in mybucket.objects.filter(Prefix=prefix):
			if record.last_modified > timestamp and record.last_modified <= now:
				tim_in = record.get()['Body'].read().decode('utf-8')
				tim_in = tim_in.splitlines()
				tim_list += process_tim(tim_in)

	logger.info("Connecting to Socrata")
	client = Socrata("data.transportation.gov", API_KEY, USERNAME, PASSWORD,timeout=400)

	logger.info("Uploading...")
	uploadResponse = client.upsert("2rdx-wgpx", tim_list)
	logger.info(uploadResponse)

	r = requests.get("https://data.transportation.gov/resource/2rdx-wgpx.json?$select=count(*)", auth=HTTPBasicAuth(USERNAME,PASSWORD))
	r = r.json()
	count = int(r[0]['count'])
	if count > 3000000:
		toDelete = count - 3000000
		logger.info(toDelete)
		retrievedRows = client.get("2rdx-wgpx", limit=toDelete, exclude_system_fields=False)
		deleteList = []
		for x in range(0,toDelete):
			tempDictionary = {}
			tempDictionary[':id'] = retrievedRows[x][':id']
			tempDictionary[':deleted'] = True
			deleteList.append(tempDictionary)
		logger.info("deleting now:")
		logger.info(client.upsert("2rdx-wgpx", deleteList))