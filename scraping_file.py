import requests
from bs4 import BeautifulSoup
import sqlite3
import json

connection = sqlite3.connect("albums.sqlite")
cursor = connection.cursor()

cursor.execute('''
    create table if not exists albums
        ('id' integer primary key,
        'Title' varchar(200),
        'Artist' varchar(200),
        'Date' varchar(50),
        'Tags' varchar(500),
        'Summary' longtext,
        'Image' varchar(200))
    ''')

genre = "heavy+metal"
for i in range(1, 11):
    url = f"https://www.last.fm/tag/{genre}/albums"
    parameters = {"page": i}
    content = requests.get(url, params=parameters).text
    soup = BeautifulSoup(content, 'html.parser')
    items = soup.findAll("div", class_="resource-list--release-list-item")
    for item in items:
        title = item.find("h3").text.strip()
        artist = item.find("p", class_="resource-list--release-list-item-artist").text.strip()
        json_dict = requests.get(
            "http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=66257839044cef7e32d32b97b3be2384"
            f"&artist={artist.replace(' ', '+')}&album={title.replace(' ', '+')}&format=json").json()
        try:
            date = json_dict["album"]["wiki"]["published"][:-7]
            summary = json_dict["album"]["wiki"]["summary"]
            image_link = json_dict["album"]["image"][-1]["#text"]
            image_name = image_link.split("/")[-1]
            tags = []
            for tag in json_dict["album"]["tags"]["tag"]:
                tags.append(tag["name"])
            tags = ", ".join(tags)
            with open(f"images/{image_name}", "wb") as image:
                image.write(requests.get(image_link).content)
            sql_tuple = title, artist, date, tags, summary, image_name
            cursor.execute('''
                insert into albums ('Title', 'Artist', 'Date', 'Tags', 'Summary', 'Image')
                values (?, ?, ?, ?, ?, ?)
                ''', sql_tuple)
            connection.commit()
        except Exception:
            print(json_dict)

connection.close()
