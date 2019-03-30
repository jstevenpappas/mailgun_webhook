import requests
import json
from time import gmtime, strftime
import properties
import logging

API_KEY = properties.MG_API_KEY


logging.basicConfig(filename='/opt/python/log/webhook.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
logger = logging.getLogger()


'''
Base function for the wrapper function 
get_begin_end_times_tuple() below
'''
def get_utc_from_epoch(epoch_ts):
	return strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime(epoch_ts))


'''
Returns a tuple based on the input Epoch timestamp...
this will be epoch-delta for being
and epoch+delta for the end time params
'''
def get_begin_end_times_tuple(epoch_time):
	seconds_delta = 30
	begin = get_utc_from_epoch(epoch_time - seconds_delta)
	end = get_utc_from_epoch(epoch_time + seconds_delta)
	return begin, end


'''
Makes and  API request to access the 'open' event assoc. with a 
specific email and time frame.
if I get an open event via webhook, it came w/out the msgid so
i make a separate API call for the 'open' event where the begin
and end time are 30 seconds before and after the actual open TS
reported in the webhook event 
'''
def get_msg_id(open_ts, recipient, domain, event="opened"):
	try:
		base_url = "https://api.mailgun.net/v3/{sending_domain}/events".format(sending_domain=domain)

		begin_time, end_time = get_begin_end_times_tuple(open_ts)
		return requests.get(
			base_url,
			auth=("api", API_KEY),
			params={"begin": begin_time,
					"end": end_time,
					"limit": 1,
					"pretty": "yes",
					"recipient": recipient,
					"event": event})

	except Exception as detail:
		logger.error('Exeception occurred for Mailgun API request accessing message-id -in Opened event for recipient={email} and timestamp={ts}: {e}'.format(email=recipient, ts=open_ts, e=detail.message))



'''
Wrapper function that formats and accesses the valuable pieces 
of the JSON response...  the actual API call is made in the 
get_msg_id() function
'''
def get_msg_id_for_open_event(open_ts, recipient, domain):
	try:

		resp = get_msg_id(open_ts, recipient, domain)
		jsonStr = resp.text
		json_loaded = json.loads(jsonStr)
		msg_id = json_loaded["items"][0]["message"]["headers"]["message-id"]
		logger.info('Successfully returned the message-id value from API and extracted from JSON: {msgid}'.format(msgid=msg_id))
		return msg_id

	except Exception as detail:
		logger.error('Exception occurred during the invocation of get_msg_id_for_open_event() function call: {e}'.format(e=detail.message))


# TODO: remove this after creating unit test
def main():
	open_timestamp = 1510157649
	recipient = "bts319@gmail.com"
	domain = "mg.turkette.com"
	msg_id = get_msg_id_for_open_event(open_timestamp, recipient, domain)
	print msg_id


if __name__ == "__main__":
	main()
