from pymongo import MongoClient
from django.conf import settings
import os
import environ

base = environ.Path(__file__) - 2 # two folders back (/a/b/ - 2 = /)
environ.Env.read_env(env_file=base('django.env')) # reading .env file

print( 'Currently running operations on: {}'.format(os.environ.get("DB")) )

client = MongoClient("mongodb+srv://root_user:{}@{}.awytu.mongodb.net".format(os.environ.get("DB_PASSWORD"), os.environ.get("DB")))

webapp = MongoClient("mongodb+srv://root_user:{}@{}.awytu.mongodb.net".format(os.environ.get("DB_PASSWORD"), os.environ.get("DB")))