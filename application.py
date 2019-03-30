from flask import Flask, request
import json
import hashlib, hmac
import events_writer
import logging
import properties

import redis
from rq import use_connection, Queue


# this is a connection to a local redis instance
# I wasn't able to get configure the rqworkers to accept
# command line args so they could be configured to
# point to a remote instance to I just installed the
# redis instance locally and all rqworkers will process
# from the local queue even if multiple eb instances
# created
my_connection = redis.Redis(host='localhost', port=6379)
use_connection(my_connection)

logging.basicConfig(filename='/opt/python/log/webhook.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
logger = logging.getLogger()


# default queue for python rq
q = Queue()

# EB looks for an 'application' callable by default.
application = Flask(__name__)


API_KEY = properties.MG_API_KEY


def verify(token, timestamp, signature, api_key=API_KEY):
	hmac_digest = hmac.new(key=api_key,
						   msg='{}{}'.format(timestamp, token),
						   digestmod=hashlib.sha256).hexdigest()
	return hmac.compare_digest(unicode(signature), unicode(hmac_digest))


@application.route('/', methods=['GET'])
def get_stub():
	return json.dumps({'success': False, 'message': 'Method Not Allowed'}), 405, {'ContentType': 'application/json'}


@application.route('/', methods=['POST'])
def webhook_payload():

	logger.info('Got a Post Request...: {params}'.format(params=request.values))
	logger.info('LOGGING WORKS')

	params = request.values

	recipient = params['recipient'] if 'recipient' in request.values else ''
	signature = params['signature'] if 'signature' in request.values else ''
	timestamp = params['timestamp'] if 'timestamp' in request.values else ''
	token = params['token'] if 'token' in request.values else ''
	domain = params['domain'] if 'domain' in request.values else ''
	city = params['city'] if 'city' in request.values else ''
	body_plain = params['body-plain'] if 'body-plain' in request.values else ''
	client_name = params['client-name'] if 'client-name' in request.values else ''
	client_os = params['client-os'] if 'client-os' in request.values else ''
	client_type = params['client-type'] if 'client-type' in request.values else ''
	country = params['country'] if 'country' in request.values else ''
	device_type = params['device-type'] if 'device-type' in request.values else ''
	event = params['event'] if 'event' in request.values else ''
	ip = params['ip'] if 'ip' in request.values else ''
	url = params['url'] if 'url' in request.values else ''
	user_agent = params['user-agent'] if 'user-agent' in request.values else ''
	message_id = params['Message-Id'] if 'Message-Id' in request.values else ''
	message_headers = params['message-headers'] if 'message-headers' in request.values else ''
	reason = params['reason'] if 'reason' in request.values else ''
	region = params['region'] if 'region' in request.values else ''
	attachment_1 = params['attachment-1'] if 'attachment-1' in request.values else 'no attachment data'
	attachment_count = params['attachment-count'] if 'attachment-count' in request.values else ''
	code = params['code'] if 'code' in request.values else ''
	description = params['description'] if 'description' in request.values else ''
	error = params['error'] if 'error' in request.values else ''
	x_mailgun_sid = params['X-Mailgun-Sid'] if 'X-Mailgun-Sid' in request.values else ''

	logger.info("Got the following post values: sending_domain={domain}, email={recipient}, token={token}, timestamp={" \
		  "timestamp}, sig={signature}".format(domain=domain, recipient=recipient, token=token, timestamp=timestamp,
											   signature=signature))

	if verify(token, timestamp, signature, api_key=API_KEY) is True:

		logger.info("Following signature was signed correctly: {sig}".format(sig=signature))

		q.enqueue(events_writer.update_mailgun_events, body_plain, city, client_name, client_os, client_type, country, device_type, domain, event,
						  ip, recipient, region, signature, timestamp, token, url, user_agent, message_id,
						  message_headers, reason, attachment_1, attachment_count, code, description, error,
						  x_mailgun_sid)

		return json.dumps({'success': True, 'message': 'Payload Accepted'}), 200, {'ContentType': 'application/json'}
	else:
		logger.warn("Following signature DID NOT pass verification: {sig}".format(sig=signature))

		# need to return 200 else load balancer marks app as down
		return json.dumps({'success': False, 'message': 'Malformed Signature'}), 200, {'ContentType': 'application/json'}



if __name__ == "__main__":
	# Setting debug to True enables debug output. This line should be
	# removed before deploying a production app.
	application.debug = False
	application.run()
