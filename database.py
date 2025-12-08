from pymongo import MongoClient
import certifi

MONGO_URI = 'mongodb+srv://yessi_user:JJ1PDpipjF1uBIUf@cluster0.ngwl6q9.mongodb.net/?appName=Cluster0'
ca = certifi.where()
def dbConnection():
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client["Reposteria"]
    except ConnectionError:
        print('Error de conexión con la bdd')
    return db