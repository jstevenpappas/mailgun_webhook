import os

"""
Any env var ref'd here is set
in the AWS EB web browser/gui
"""
RDS_LUIGI_DB_NAME = os.environ['RDS_LUIGI_DB_NAME']
RDS_LUIGI_USERNAME = os.environ['RDS_LUIGI_USERNAME']
RDS_LUIGI_PASSWORD = os.environ['RDS_LUIGI_PASSWORD']
RDS_LUIGI_HOSTNAME = os.environ['RDS_LUIGI_HOSTNAME']
RDS_LUIGI_PORT = os.environ['RDS_LUIGI_PORT']
MG_API_KEY = os.environ['MAILGUN_API_KEY']