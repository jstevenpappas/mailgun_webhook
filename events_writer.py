from ConnectionPoolFactory import threaded_connection_pool
import ConnectionPoolFactory
import sys
import properties
import logging
import inspect
import api_calls

reload(sys)
sys.setdefaultencoding('Cp1252')

logging.basicConfig(filename='/opt/python/log/webhook.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
logger = logging.getLogger()

def update_mailgun_events(body_plain, city, client_name, client_os, client_type, country, device_type, domain, event,
						  ip, recipient, region, signature, timestamp, token, url, user_agent, message_id,
						  message_headers, reason, attachment_1, attachment_count, code, description, error,
						  x_mailgun_sid):

	try:

		# we have an 'opened' event from a webhook post w/out a msg-id
		# so we have to explicitly retrieve it via the API and set the
		# field message_id to its return value so it gets properly updated
		# in the database
		if event == "opened":
			logger.info('Processing Opened event from Redis so making one-off API request for messge-id so we can populate database')
			input_ts = int(timestamp)
			message_id = api_calls.get_msg_id_for_open_event(input_ts, recipient, domain)
			logger.info('Finished processing Opened event - message-id and recipient values are the following: recipient={recipient}, message-id={msgid}'.format(recipient=recipient, msgid=message_id))



		with threaded_connection_pool.getCursor() as cursor:
			mailgun_webhook_event_sql = cursor.mogrify(
				"INSERT INTO public.mailgun_events (body_plain, city, client_name, client_os, client_type, country, "
				"device_type, domain, event, ip, recipient, region, signature, timestamp, token, url, user_agent, "
				"message_id, message_headers, reason, attachment_1, attachment_count, code, description, error, "
				"x_mailgun_sid) "
				" values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
				"%s, %s, %s)",
				(body_plain, city, client_name, client_os, client_type, country, device_type, domain, event, ip,
				 recipient, region, signature, timestamp, token, url, user_agent, message_id, message_headers, reason,
				 attachment_1, attachment_count, code, description, error, x_mailgun_sid))
			cursor.execute(mailgun_webhook_event_sql)
			cursor.close()

		logger.info('Constructed the following insert statement using the input params: {stmnt}'.format(stmnt=mailgun_webhook_event_sql))

	except Exception as detail:
		logger.error('Execption while processing the mailgun event from Redis: {e}'.format(e=detail.message))
