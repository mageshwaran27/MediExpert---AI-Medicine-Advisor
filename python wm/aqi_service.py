import requests

def get_aqi(lat, lng):
    try:
        url = f"https://api.openaq.org/v2/latest?coordinates={lat},{lng}"
        resp = requests.get(url)
        data = resp.json()
        aqi_value = data['results'][0]['measurements'][0]['value']
        return aqi_value
    except:
        return None

def check_aqi_alert(lat, lng, threshold=150):
    aqi = get_aqi(lat,lng)
    if aqi is not None and aqi > threshold:
        print(f"ALERT! AQI high at {lat},{lng} -> {aqi}")
