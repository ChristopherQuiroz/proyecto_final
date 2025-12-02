from pymongo import MongoClient
import certifi

MONGO_URI = 'mongodb+srv://christopherquiroz_db_user:iyrXMN2qMefK6IBz@reposteria.jadunar.mongodb.net/'
ca = certifi.where()

def dbConnection():
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client["Reposteria"]
    except ConnectionError:
        print('Error de conexión con la bdd')
    return db