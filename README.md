# mghook

#### Table of Contents

1. [Description](#description)
2. [Setup](#setup)
3. [Logs](#logs-location) 
4. [Usage](#usage)
5. [Workflow](#workflow)
6. [Testing](#testing)

## Description

## Setup
Minimal setup is required.


* install virtualenv 
```
virtualenv ~/mghook
```

* activate the virtualenv
```
~$ source ~/mghook/bin/activate
```

* ensure you have the correct env variables set in your local env
```
export MAILGUN_API_KEY='some-test-value'
export RDS_LUIGI_DB_NAME=reporting
export RDS_LUIGI_USERNAME=event_writer
export RDS_LUIGI_PASSWORD=somepass
export RDS_LUIGI_HOSTNAME=your-local-postgres-instance.local.com
export RDS_LUIGI_PORT=5439
```


* choose a directory and then clone repo
```
git clone https://git.cogolo.net/jpappas/mghook.git
```

* install the requirements
```
pip install -r requirements.txt
```

* initialize the aws eb repo
```
eb init -p python2.7 mghook-app
```

* copy the mghook files form the SSH Keys folder in box to your /Users/<username>/.ssh/ directory

* run eb init in the root of the dir you git clone'd in and select the mghook keypair when prompted

* to ssh to the prod server
```
eb ssh mghook-prod
```

* to deploy
```
eb deploy mghook-prod
```

* the prod app is accessible behind the following domain
```
https://mgeventsink.com/
```

## Logs Location
The logs are written to the following file on the server (and locally):
/opt/python/log/webhook.log

## Usage

It is run locally by doing the following:
> python application.py



## Workflow

* the application hosts a webhook that accepts POST requests from MailGun for mailing events (e.g., unsubs, bounces, etc)
* it logs the event - 1 per post - to the Luigi database
* it responds to GETs only with json text so the aws loadbalancer doesn't mark it down
* it verifies POST requests by comparing the signature param value with the output of the sha256 hash of the concatenated timestamp and token param values
* if the values match - we accept the event as coming from Mailgun... if it doesn't then it is an imposter!
* also, if signature is good... a response is sent right away back to Mailgun confirming such - the events are written to a Redis cache local to the eb server
immediatly and is processed later asynchronously by 4 separate rq workers running as background daemons on the eb server.
* the rqworkers are managed - in turn - by a supervisord daemon (see file .ebextensions/01-rqworker.config for how it is setup and configured)





## Testing

Yes - this needs test cases!!!!

But if you are running locally, you can still test it:
* choose  timestamp and token param values:  we'll use 
```
timestamp=1506614545
token=BLAHBLAHBLAH
```
 

* get the sha256 hash value of those two values concatented using the  to create the hmac (I used the prod value of the API key below for the output)
```
echo -n '1506614545BLAHBLAHBLAH' | openssl sha256 -hmac $MAILGUN_API_KEY
(stdin)= 5fd197818bb9832565dd6f78e74a940ca47a8635fbb6259645e5f4b3cbf0c50c
```
* the value from stdin is going to be the value for the signature param 
```
5fd197818bb9832565dd6f78e74a940ca47a8635fbb6259645e5f4b3cbf0c50c
```

* use the above param values along with some others that Mailgun uses to construct a curl POST request to your locally running application
 ```
curl --data  "event=opened&recipient=john@tzn.com&domain=email.mx.americasbesthouse.com&ip=127.0.0.1&country=US&city=PRAGUE&\
timestamp=1506614545&token=BLAHBLAHBLAH&signature=5fd197818bb9832565dd6f78e74a940ca47a8635fbb6259645e5f4b3cbf0c50c"
```

* assuming you used the same $MAILGUN_API_KEY env var value as the one your app uses then the signatures should match and you should see JSON indicating such
```
{'success': True, 'message': 'Payload Accepted'}
```
* if the signatures don't match, you'll see the following:
```
{'success': False, 'message': 'Malformed Signature'}
```

* NOTE: the HTTP response codes are 200 on both so the load balancer doesn't accidentally mark them as being down



