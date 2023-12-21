from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask.views import MethodView
import telebot
from telebot import types
from telebot.types import InputMediaPhoto
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
from sqlite3 import Error
from PIL import Image
import os

                                                            #Функции камфайндера

def MeshokFind(response, i, path):
    camimages = []
    caminformation = {'Name': None, 'Price': None, 'Description': None, 'Images': None, 'Imagefilename': None}
    soup = BeautifulSoup(response.text, 'html5lib')
    caminformation['Name'] = soup.find('title').text
    caminformation['Price'] = float(soup.find('b', itemprop="price").text)
    caminformation['Description'] = soup.find('td', id="desc", itemprop="description").text
    for element in soup.findAll('img', id=re.compile("thumb\d+")):
        camimages.append(element['src'])
    camimages_str = ",".join(camimages)
    caminformation['Images'] = camimages_str
    #data-zoom-image
    try:
        img_url = camimages[0]
        img = Image.open(requests.get(img_url, stream = True).raw)
        img.save(path+'/'+str(i)+'.png')
        caminformation['Imagefilename'] = (path+'/'+str(i)+'.png')
    except:
        caminformation['Imagefilename'] = 'noimage'
    return(caminformation)

def ASK(request):
   payload = {'search': request}  
   print(payload)
   response = requests.get('https://meshok.net/listing', params=payload)
   soup = BeautifulSoup(response.text, 'html5lib')
   listoflots = []
   for element in soup.findAll('div', class_="add_fav_item Sadd_fav"):
      listoflots.append(element['rel'])
   #сделать поиск по другим страницам
   return(response.status_code, listoflots)

def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

                                                                #функции

def request_internet_func(request):
    func = ASK(request)
    print(func)
    if func[0] == 200 and len(func[1]) != []:
        listoflots = func[1]
        path = '/Users/georgy/Desktop/penis/nigger_killer/images/'+str(request)
        try:
            os.makedirs(path)
        except:
                pass    
        connection = create_connection('penislist.db')
        cursor = connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Listofcamlots(
        id INTEGER PRIMARY KEY,
        searchrequest TEXT NOT NULL,
        Code TEXT NOT NULL UNIQUE,
        Name TEXT NOT NULL,
        Description TEXT NOT NULL,
        Price REAL,
        Images TEXT NOT NULL,
        Imagefilename TEXT NOT NULL,
        favorite TEXT,
        actuality TEXT NOT NULL,
        UNIQUE(Code)
        )'''
        )
        cursor.execute('''UPDATE Listofcamlots SET actuality = 'N' where searchrequest = ? ''', (request,))
        cursor.execute("SELECT Name, actuality FROM Listofcamlots")
        cameras = cursor.fetchall()
        for i in range(0, len(listoflots)):
            url = 'https://meshok.net/item/' + listoflots[i]
            response = requests.get(url)
            caminformation = MeshokFind(response, i, path)
            try:
                cursor.execute('INSERT INTO Listofcamlots (searchrequest, Code, Name, Price, Description, Images, Imagefilename, actuality) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (
                (request), (listoflots[i]), caminformation['Name'], caminformation['Price'], caminformation['Description'], caminformation['Images'], caminformation['Imagefilename'], 'Y'))
            except:
                search = 0
                cursor.execute("SELECT searchrequest FROM Listofcamlots WHERE Code=?", (listoflots[i],))
                search = cursor.fetchall()
                search = str(search[0][0]) + ', ' + request
                cursor.execute('''UPDATE Listofcamlots SET actuality = 'Y', searchrequest = ? WHERE Code = ? ''', (search, listoflots[i],))
        connection.commit()
        connection.close()
        return(len(listoflots))
    if func[0] != 200:
        return('e')

                                                                #flask каллл

app = Flask(__name__)
api = Api(app)

#lot_arguments = reqparse.RequestParser()
#lot_arguments.add_argument(fav = , types=str, help =)


class request_core(Resource):
    def post(self, request):
        func = request_internet_func(request)
        if func == 'e':
            return {'message':'проблемы с доступом к сайту'}
        else:
            return {'message':'Я нашел ' + str(func) + ' лота для тебя'}
        
class show(Resource):
    def get(self, request):
        connection = create_connection('penislist.db')
        cursor = connection.cursor()
        cursor.execute('SELECT DISTINCT searchrequest FROM Listofcamlots')
        searchrequest = cursor.fetchall()
        print(searchrequest)
        connection.commit()
        connection.close()
        return {'listofcams':searchrequest}
    def post(self, request):
        connection = create_connection('penislist.db')
        cursor = connection.cursor()
        if request != 'F':
            cursor.execute("SELECT Name, Price, Images, Imagefilename, favorite, actuality FROM Listofcamlots WHERE searchrequest LIKE '%'||?||'%'", (request,))
        else:
            cursor.execute("SELECT Name, Price, Images, Imagefilename, favorite, actuality FROM Listofcamlots WHERE favorite = 'F'") 
        cameras = cursor.fetchall()
        return {'listofcams':cameras}
    
class avgprices(Resource):
    def get(self, request):
        connection = create_connection('penislist.db')
        cursor = connection.cursor()
        cursor.execute("SELECT AVG(price) FROM Listofcamlots WHERE actuality= 'Y' and searchrequest=?", (request,))
        actualcameras = cursor.fetchall()[0][0]
        cursor.execute("SELECT AVG(price) FROM Listofcamlots WHERE actuality= 'N' and searchrequest=?", (request,))
        nonactualcameras = cursor.fetchall()[0][0]
        connection.commit()
        connection.close()
        return {'actualprice':str(actualcameras), 'sellprice':str(nonactualcameras)}
    
class addfav(Resource):
    def put(self, request):
        connection = create_connection('penislist.db')
        cursor = connection.cursor()
        cursor.execute('''UPDATE Listofcamlots SET favorite = 'F' WHERE Name = ? ''', (request,))
        connection.commit()
        connection.close()
        return {'message':'Лот добавлен в избранное.'}

class showlot(Resource):
    def get(self, request):
        connection = create_connection('penislist.db')
        cursor = connection.cursor()
        cursor.execute("SELECT Name, Description, Price, Images, Code, Imagefilename, favorite, actuality FROM Listofcamlots WHERE Name=?", (request,))
        cameras = cursor.fetchall()
        return {'camerainformation':cameras}
 
api.add_resource(request_core, '/startsearch/<string:request>')
api.add_resource(show, '/show/<string:request>')
api.add_resource(avgprices, '/showstatistics/<string:request>')
api.add_resource(addfav, '/addlottofav/<string:request>')
api.add_resource(showlot, '/showextralot/<string:request>')

if __name__ == '__main__':
    app.run(debug=True)