import http.client
import os

def get_weather_data(latitude, longitude):
    conn = http.client.HTTPSConnection("weatherapi-com.p.rapidapi.com")

    headers = {
        'X-RapidAPI-Key': "044502cb26msh017138364e50774p1f4c2fjsna420df4f77d9",
        'X-RapidAPI-Host': "weatherapi-com.p.rapidapi.com"
    }

    query = f"/current.json?q={latitude},{longitude}"
    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()

    return data.decode("utf-8")

    