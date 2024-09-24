import json, urllib.request, urllib.parse

def get(url):
    try:
        request = urllib.request.Request(url, method='GET')
        response = urllib.request.urlopen(request)
    except Exception as e:
        print(e.code)
        print(e.reason)
        return None
    else:
        result = response.read().decode('utf-8')
        #print(result)
        return json.loads(result)

def post(url, data):
    return http(url, data, 'POST')

def put(url, data):
    return http(url, data, 'PUT')

def http(url, data, method):
    try:
        headers = {
            'Content-Type': 'application/json',
        }
        request = urllib.request.Request(
            url, json.dumps(data).encode(), headers, method=method
        )
        response = urllib.request.urlopen(request)
    except Exception as e:
        print(e.code)
        print(e.reason)
        return None
    else:
        result = response.read().decode('utf-8')
        return json.loads(result)
