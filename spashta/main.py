from cloudant.client import Cloudant
from cloudant.error import CloudantException
import flask
from flask import Flask, render_template, request, jsonify
from flask_restful import Resource, Api, reqparse
import atexit,os,json,random,sys,requests

try:
    import urllib.parse
    from urllib.parse import urlparse, urlencode # Python 3
except ImportError:
    import urllib
    from urllib import urlencode  # Python 2

app = Flask(__name__, static_url_path='')
api = Api(app)

# Get Text tone analyzed
class HelloWorld(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('feedback', type=str, help='Feedback is empty')
        args = parser.parse_args()
        userInput = args['feedback']
        print('...userinput:',userInput)
        userId = 'd8bda777-003f-4d8e-9fdf-0919d8be3cf6'
        password = 'oOuR25RAK5G5'

        i = {'version' : '2017-09-21','text' : userInput}
        encodedUserInput = urlencode(i)
        url = 'https://gateway.watsonplatform.net/tone-analyzer/api/v3/tone?' + encodedUserInput
        try:
                resp = requests.get(url,auth=(userId,password))
                if resp.status_code == 200:
                        responseGot = resp.json()
                        print('...Response from Tone Analyzer :',responseGot)
                        toneArray = responseGot['document_tone']['tones']
                        if (len(toneArray)==0):
                                tone = 'Unable to decipher'
                        else:
                                firstRec = toneArray[0]
                                tone = firstRec['tone_name']
        except Exception as e:
                print(e)
                tone='Error occured'

        d = {
               'toneFound': tone
        }
        responseTo = flask.make_response(jsonify(d))
        print("...",responseTo.get_data())
        responseTo.headers["Content-Type"] = "application/json"
        return responseTo

api.add_resource(HelloWorld, '/analyze')

databaseName = 'wiamdatabase'
client = None
db = None
dbUser = None
dbPassword = None
dbUrl = None

toneUser = None
tonePassword = None
toneUrl=None

def getWorkItemId():
        return random.randint(1000,9999)

def doInitialSetup():
        # This is a simple collection of data,to store within the database.
        sampleData = [
                ["WIAM-"+ str(getWorkItemId()), "abisrk", "tech lead", "CWS"],
                ["WIAM-"+ str(getWorkItemId()), "sivaraa", "project manager", "Bankline"],
                ["WIAM-"+ str(getWorkItemId()), "chunr", "tech lead", "Bankline"],
                ["WIAM-"+ str(getWorkItemId()), "raj", "tech lead", "CWS"],
                ["WIAM-"+ str(getWorkItemId()), "abisrk", "tech lead", "Image & Workflow"]
        ]
        for document in sampleData:
                # Retrieve the fields in each row.
                accRequest = document[0]
                userId = document[1]
                role = document[2]
                application = document[3]

                # Create a JSON document that represents
                # all the data in the row.
                jsonDocument = {
                        "accessRequestId": accRequest,
                        "userId": userId,
                        "role": role,
                        "application": application
                }

                # Create a document using the Database API.
                newDocument = db.create_document(jsonDocument)

                # Check that the document exists in the database.
                if newDocument.exists():
                        print("Document '{0}' successfully created.".format(accRequest))
                # Space out the results.
                print("----\n")


if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        dbUser = creds['username']
        dbPassword = creds['password']
        dbUrl = 'https://' + creds['host']
        client = Cloudant(dbUser, dbPassword, url=dbUrl, connect=True)
        #client.delete_database(databaseName)
        db = client.create_database(databaseName, throw_on_exists=False)
        doInitialSetup()
elif "CLOUDANT_URL" in os.environ:
    client = Cloudant(os.environ['CLOUDANT_USERNAME'], os.environ['CLOUDANT_PASSWORD'], url=os.environ['CLOUDANT_URL'], connect=True)
    #client.delete_database(databaseName)
    db = client.create_database(databaseName, throw_on_exists=False)
    doInitialSetup()
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('******** Loading local VCAP_SERVICES ***********')
        creds = vcap['services']['wiamCredentials'][0]['credentials']
        dbUser = creds['username']
        dbPassword = creds['password']
        dbUrl = creds['host']
        client = Cloudant(dbUser, dbPassword, url=dbUrl, connect=True)
        #client.delete_database(databaseName)
        db = client.create_database(databaseName, throw_on_exists=False)
        print("************ Connected *******************")
        doInitialSetup()

# On IBM Cloud Cloud Foundry, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))

@app.route('/')
def root():
    return 'Sriramajayam'

# Get Endpoint to retrieve all records from db
@app.route('/all', methods=['GET'])
def getAllRecords():
    if client:
        allRecs = [document for document in db]
        return jsonify(allRecs)
    else:
        print('No database')
        return jsonify(['No database'])

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
