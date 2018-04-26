import os
import json
from sodapy import Socrata
import boto3
import time
import datetime
import requests
from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings()
import logging

'''
This is a timed lambda function that runs every five minutes to check for new Wyoming CV Pilot Basic Safety Messages on 
the s3 bucket usdot-its-cvpilot-public-data and add them to the sample dataset on data.transportation.gov. If a new data
file is found, the file is opened and read line-by-line. The Basic Safety Messages are then transcribed from their current
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

def setMetadata(formatted_bsm, bsm_dict):
	'''
	Reads the metadata section of the Wyoming CV Pilot Basic Safety Messages and flattens them into
	the data.transportation.gov column headers.

	Parameters:
		formatted_bsm: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		bsm_dict: Dict containing individual BSM from the Wyoming CV Pilot data file truncated to 
		include just metadata.

	Returns:
		formatted_bsm with additional keys 
	'''
	formatted_bsm['metadata_generatedAt'] = bsm_dict['recordGeneratedAt'].replace('Z[UTC]','')
	formatted_bsm['metadata_generatedBy'] = bsm_dict['recordGeneratedBy']
	formatted_bsm['metadata_logFileName'] = bsm_dict['logFileName']
	formatted_bsm['metadata_securityResultCode'] = bsm_dict['securityResultCode']
	formatted_bsm['metadata_sanitized'] = str(bsm_dict['sanitized'])
	formatted_bsm['metadata_payloadType'] = bsm_dict['payloadType']
	formatted_bsm['metadata_recordType'] = bsm_dict['recordType']
	formatted_bsm['metadata_serialId_streamId'] = bsm_dict['serialId']['streamId']
	formatted_bsm['metadata_serialId_bundleSize'] = bsm_dict['serialId']['bundleSize']
	formatted_bsm['metadata_serialId_bundleId'] = bsm_dict['serialId']['bundleId']
	formatted_bsm['metadata_serialId_recordId'] = bsm_dict['serialId']['recordId']
	formatted_bsm['metadata_serialId_serialNumber'] = bsm_dict['serialId']['serialNumber']
	formatted_bsm['metadata_receivedAt'] = bsm_dict['odeReceivedAt'].replace('Z[UTC]','')
	formatted_bsm['metadata_schemaVersion'] = bsm_dict['schemaVersion']
	formatted_bsm['metadata_bsmSource'] = bsm_dict['bsmSource']
	return formatted_bsm

def setCoreData(formatted_bsm, bsm_dict):
	'''
	Reads the coreData (SAE J2735-based) section of the Wyoming CV Pilot Basic Safety Messages and
	flattens them into the data.transportation.gov column headers.

	Parameters:
		formatted_bsm: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		bsm_dict: Dict containing individual BSM from the Wyoming CV Pilot data file truncated to
		contain just payload/data/coreData

	Returns:
		formatted_bsm with additional keys 
	'''
	formatted_bsm['coreData_msgCnt'] = bsm_dict['msgCnt']
	formatted_bsm['coreData_id'] = bsm_dict['id']
	formatted_bsm['coreData_secMark'] = str(bsm_dict['secMark'])
	formatted_bsm['coreData_position_lat'] = bsm_dict['position']['latitude']
	formatted_bsm['coreData_position_long'] = bsm_dict['position']['longitude']
	formatted_bsm['coreData_elevation'] = bsm_dict['position']['elevation']
	formatted_bsm['coreData_accelset_accelYaw'] = bsm_dict['accelSet']['accelYaw']
	formatted_bsm['coreData_accuracy_semiMajor'] = bsm_dict['accuracy']['semiMajor']
	formatted_bsm['coreData_accuracy_semiMinor'] = bsm_dict['accuracy']['semiMinor']
	formatted_bsm['coreData_transmission'] = bsm_dict['transmission']
	formatted_bsm['coreData_speed'] = bsm_dict['speed']
	formatted_bsm['coreData_heading'] = bsm_dict['heading']
	formatted_bsm['coreData_brakes_wheelBrakes_leftFront'] = str(bsm_dict['brakes']['wheelBrakes']['leftFront'])
	formatted_bsm['coreData_brakes_wheelBrakes_rightFront'] = str(bsm_dict['brakes']['wheelBrakes']['rightFront'])
	formatted_bsm['coreData_brakes_wheelBrakes_unavailable'] = str(bsm_dict['brakes']['wheelBrakes']['unavailable'])
	formatted_bsm['coreData_brakes_wheelBrakes_leftRear'] = str(bsm_dict['brakes']['wheelBrakes']['leftRear'])
	formatted_bsm['coreData_brakes_wheelBrakes_rightRear'] = str(bsm_dict['brakes']['wheelBrakes']['rightRear'])
	formatted_bsm['coreData_brakes_traction'] = bsm_dict['brakes']['traction']
	formatted_bsm['coreData_brakes_abs'] = bsm_dict['brakes']['abs']
	formatted_bsm['coreData_brakes_scs'] = bsm_dict['brakes']['scs']
	formatted_bsm['coreData_brakes_brakeBoost'] = bsm_dict['brakes']['brakeBoost']
	formatted_bsm['coreData_brakes_auxBrakes'] = bsm_dict['brakes']['auxBrakes']
	formatted_bsm['coreData_size'] = str(bsm_dict['size'])
	return formatted_bsm

def setVSE(formatted_bsm, bsm_dict):
	'''
	Optional method if SAE J2735 Part II Vehicle Safety Extensions are included in Basic Safety Message.
	Attempts to read the required and optional members of the Vehicle Safety Extensions of the 
	Wyoming CV Pilot Basic Safety Messages and flattens them into the data.transportation.gov column headers.

	Parameters:
		formatted_bsm: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		bsm_dict: Dict containing individual BSM from the Wyoming CV Pilot data file truncated to include
		just VehicleSafetyExtensions

	Returns:
		formatted_bsm with additional keys 
	'''
	formatted_bsm['part2_vse_events'] = str(bsm_dict.get('events'))
	formatted_bsm['part2_vse_ph_crumbdata'] = str(bsm_dict.get('pathHistory',{}).get('crumbData'))
	formatted_bsm['part2_vse_pp_confidence'] = bsm_dict.get('pathPrediction',{}).get('confidence')
	formatted_bsm['part2_vse_pp_radiusofcurve'] = bsm_dict.get('pathPrediction',{}).get('radiusOfCurve')
	formatted_bsm['part2_vse_lights'] = bsm_dict.get('lights')
	return formatted_bsm

def setSUVE(formatted_bsm, bsm_dict):
	'''
	Optional method if SAE J2735 Part II Supplemental Vehicle Extensions are included in Basic Safety Message.
	Attempts to read the required and optional members of the Supplemental Vehicle Extensions of the 
	Wyoming CV Pilot Basic Safety Messages and flattens them into the data.transportation.gov column headers.

	Parameters:
		formatted_bsm: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		bsm_dict: Dict containing individual BSM from the Wyoming CV Pilot data file truncated to
		include just SupplementalVehicleExtensions classDetails

	Returns:
		formatted_bsm with additional keys 
	'''
	formatted_bsm['part2_suve_cd_hpmstype'] = bsm_dict.get('hpmstype')
	formatted_bsm['part2_suve_cd_role'] = bsm_dict.get('role')
	formatted_bsm['part2_suve_vd_height'] = bsm_dict.get('height')
	formatted_bsm['part2_suve_vd_mass'] = bsm_dict.get('mass')
	formatted_bsm['part2_suve_vd_trailerweight'] = bsm_dict.get('trailerWeight')
	return formatted_bsm

def setSPVE(formatted_bsm, bsm_dict):
	'''
	Optional method if SAE J2735 Part II Special Vehicle Extensions are included in Basic Safety Message.
	Attempts to read the required and optional members of the Special Vehicle Extensions of the 
	Wyoming CV Pilot Basic Safety Messages and flattens them into the data.transportation.gov column headers.

	Parameters:
		formatted_bsm: Dict containing the flattened JSON to be uploaded to data.transportation.gov
		bsm_dict: Dict containing individual BSM from the Wyoming CV Pilot data file truncated to
		just SpecialVehicleExtensions trailers

	Returns:
		formatted_bsm with additional keys 
	'''
	formatted_bsm['part2_spve_tr_conn_pivotoffset'] = bsm_dict.get('connection',{}).get('pivotOffset')
	formatted_bsm['part2_spve_tr_conn_pivotangle'] = bsm_dict.get('connection',{}).get('pivotAngle')
	formatted_bsm['part2_spve_tr_conn_pivots'] = str(bsm_dict.get('connection',{}).get('pivots'))
	formatted_bsm['part2_spve_tr_ssprights'] = bsm_dict.get('sspRights')
	formatted_bsm['part2_spve_tr_units_isDolly'] = str(bsm_dict.get('units').get('isDolly'))
	formatted_bsm['part2_spve_tr_units_width'] = bsm_dict.get('units').get('width')
	formatted_bsm['part2_spve_tr_units_length'] = bsm_dict.get('units').get('length')
	formatted_bsm['part2_spve_tr_units_height'] = bsm_dict.get('units').get('height')
	return formatted_bsm

def process_bsm(bsm_in):
	'''
	The main method that processes each Basic Safety Message from the input file. Reads JSON, calls 
	setMetadata and setCoreData for each file. Checks if the message has partII elements 
	and calls the appropriate processing method based on the partII id.

	Parameters:
		bsm_in: A list of strings containing Basic Safety Messages from the Wyoming CV Pilot

	Returns:
		bsm_list: A list of processed Basic Safety Messages to be uploaded to data.transportation.gov
	'''
	bsm_list = []
	for bsm in bsm_in:
		try:
			bsm_dict = json.loads(bsm)
			formatted_bsm = {}
			formatted_bsm = setMetadata(formatted_bsm, bsm_dict['metadata'])
			formatted_bsm['dataType'] = bsm_dict['payload']['dataType']
			formatted_bsm = setCoreData(formatted_bsm, bsm_dict['payload']['data']['coreData'])
			for elem in bsm_dict["payload"]["data"]["partII"]:
				if elem["id"] == "VehicleSafetyExtensions":
					formatted_bsm = setVSE(formatted_bsm, elem['value'])
				elif elem["id"] == "SupplementalVehicleExtensions":
					formatted_bsm = setSUVE(formatted_bsm, elem['value'].get('classDetails',{}))
				else:
					formatted_bsm = setSPVE(formatted_bsm, elem['value'].get('trailers',{}))
			formatted_bsm['coreData_position'] = "POINT (" + str(formatted_bsm["coreData_position_long"]) + " " + str(formatted_bsm["coreData_position_lat"]) + ")"
			bsm_list.append(formatted_bsm)
		except:
			pass
	return bsm_list

def lambda_handler(event, context):
	'''
	Method called by Amazon Web Services when the lambda trigger fires. This lambda is configured to be triggered
	every five minutes. This method connects to the s3 bucket usdot-its-cvpilot-public-data, determines the current
	datetime and  builds the folder structure based on the datetime five minutes ago. Checks if any files have
	been added in the past five minutes. If so, opens them and reads line-by-line to bsm_in. Uploads processed results to
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
	timestamp = timenow - datetime.timedelta(minutes = 5, seconds = timenow.second, microseconds = timenow.microsecond)
	now = timestamp + datetime.timedelta(minutes = 5)
	prefix = "wydot/BSM/{}/{:02}/{:02}/{:02}/".format(timestamp.year,timestamp.month,timestamp.day,timestamp.hour)
	bsm_list = []
	for record in mybucket.objects.filter(Prefix=prefix):
		if record.last_modified > timestamp and record.last_modified <= now:
			bsm_in = record.get()['Body'].read().decode('utf-8')
			bsm_in = bsm_in.splitlines()
			bsm_list += process_bsm(bsm_in)

	if timestamp.hour != timenow.hour:
		prefix = "wydot/BSM/{}/{:02}/{:02}/{:02}/".format(timestamp.year,timestamp.month,timestamp.day,timenow.hour)
		for record in mybucket.objects.filter(Prefix=prefix):
			if record.last_modified > timestamp and record.last_modified <= now:
				bsm_in = record.get()['Body'].read().decode('utf-8')
				bsm_in = bsm_in.splitlines()
				bsm_list += process_bsm(bsm_in)

	logger.info("Connecting to Socrata")
	client = Socrata("data.transportation.gov", API_KEY, USERNAME, PASSWORD, timeout=400)

	logger.info("Uploading...")
	uploadResponse = client.upsert("9k4m-a3jc", bsm_list)
	logger.info(uploadResponse)
	newRows = uploadResponse['Rows Created']
	logger.info(newRows)

	r = requests.get("https://data.transportation.gov/resource/9k4m-a3jc.json?$select=count(*)", auth=HTTPBasicAuth(USERNAME,PASSWORD))
	r = r.json()
	count = int(r[0]['count'])
	if count > 3000000:
		toDelete = count - 3000000
		logger.info(toDelete)
		retrievedRows = client.get("9k4m-a3jc", limit=toDelete, exclude_system_fields=False)
		deleteList = []
		for x in range(0,toDelete):
			tempDictionary = {}
			tempDictionary[':id'] = retrievedRows[x][':id']
			tempDictionary[':deleted'] = True
			deleteList.append(tempDictionary)
		logger.info("deleting now:")
		logger.info(client.upsert("9k4m-a3jc", deleteList))
	logger.info(time.time()-start)