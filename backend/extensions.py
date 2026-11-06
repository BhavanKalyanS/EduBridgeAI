from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_pymongo import PyMongo

jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
mongo = PyMongo()