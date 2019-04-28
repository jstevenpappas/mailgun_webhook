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


* install [virtualenv](https://virtualenv.pypa.io/en/latest/) 
```
virtualenv ~/mghook
```

* activate the virtualenv
```
~$ source ~/mghook/bin/activate
```

* ensure you have the correct [environment variables](https://en.wikipedia.org/wiki/Environment_variable#Unix) set in your local env
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

* if necessary, copy or create the requisite [SSH Keys](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html) in your [/Users/username/.ssh/ directory](https://superuser.com/questions/635269/cant-find-ssh-directory-in-my-terminal)

* initialize the aws eb repo by running [eb init](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb3-init.html) in the root of the dir you git clone'd in and select the mhook keypair when prompted
```
eb init -p python2.7 mghook-app
```

* to test [ssh'ing into your environment specific EC2 instance](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb3-ssh.html)
```
eb ssh mghook-prod
```

* to deploy
```
eb deploy mghook-prod
```

* the application should be accessible behind your [chosen domain](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/customdomains.html) (example one below)
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

* the application hosts a receiver for [Mailgun webhook](https://documentation.mailgun.com/en/latest/api-webhooks.html) that accepts POST requests from [MailGun for mailing events](https://documentation.mailgun.com/en/latest/api-events.html#events) (e.g., unsubs, bounces, etc)
* it logs the event - 1 per post - to the reporting database
* it responds to GETs only with json text so the [AWS ELB loadbalancer](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features.managing.elb.html) doesn't mark it down
* it verifies POST requests by comparing the [signature](https://en.wikipedia.org/wiki/HMAC) param value with the output of the [sha256](https://en.wikipedia.org/wiki/SHA-2) hash of the concatenated timestamp and token param values
* if the values match - we accept the event as coming from Mailgun... if it doesn't then it is an imposter!
* also, if [signature](https://en.wikipedia.org/wiki/HMAC) is good... a response is sent right away back to Mailgun confirming such - the events are written to a [Redis](https://redis.io/) cache local to the eb server
immediatly and is processed later asynchronously by 4 separate rq workers running as background daemons on the eb server.
* the [rqworkers](https://python-rq.org/docs/workers/) are managed - in turn - by a [supervisord](http://supervisord.org/) daemon (see file .[ebextensions](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/ebextensions.html)/01-[rqworker.config](http://python-rq.org/patterns/supervisor/) for how it is setup and configured via [supervisord](http://supervisord.org/))





## Testing

Yes - this needs test cases!!!!

But if you are running locally, you can still test it:
* choose  timestamp and token param values:  we'll use 
```
timestamp=1506614545
token=BLAHBLAHBLAH
```
 

* get the [sha256](https://en.wikipedia.org/wiki/SHA-2) hash value of those two values concatented using the  to create the hmac (I used the prod value of the [API](https://help.mailgun.com/hc/en-us/articles/203380100-Where-Can-I-Find-My-API-Key-and-SMTP-Credentials-) key below for the output)
```
echo -n '1506614545BLAHBLAHBLAH' | openssl sha256 -hmac $MAILGUN_API_KEY
(stdin)= 5fd197818bb9832565dd6f78e74a940ca47a8635fbb6259645e5f4b3cbf0c50c
```
* the value from stdin is going to be the value for the [signature](https://en.wikipedia.org/wiki/HMAC) param 
```
5fd197818bb9832565dd6f78e74a940ca47a8635fbb6259645e5f4b3cbf0c50c
```

* use the above param values along with some others that Mailgun uses to construct a curl POST request to your locally running application
 ```
curl --data  "event=opened&recipient=john@tzn.com&domain=email.mx.americasbesthouse.com&ip=127.0.0.1&country=US&city=PRAGUE&\
timestamp=1506614545&token=BLAHBLAHBLAH&signature=5fd197818bb9832565dd6f78e74a940ca47a8635fbb6259645e5f4b3cbf0c50c"
```

* assuming you used the same [$MAILGUN_API_KEY](https://help.mailgun.com/hc/en-us/articles/203380100-Where-Can-I-Find-My-API-Key-and-SMTP-Credentials-) env var value as the one your app uses then the [signature](https://en.wikipedia.org/wiki/HMAC) should match and you should see JSON indicating such
```
{'success': True, 'message': 'Payload Accepted'}
```
* if the [signature](https://en.wikipedia.org/wiki/HMAC) doesn't match, you'll see the following:
```
{'success': False, 'message': 'Malformed Signature'}
```

* NOTE: the HTTP response codes are 200 on both so the [load balancer doesn't accidentally mark them as being down](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/ts-elb-healthcheck.html)



