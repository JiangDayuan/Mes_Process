import urllib.request
import urllib.parse
import json
import requests

def piwebget(url):
    req = urllib.request.Request(url=url,method='GET')
    with urllib.request.urlopen(req) as f:
        p_data = f.read().decode('utf-8')
    return json.loads(p_data)

def piwebpost(url):
    body = [{
            'uuid': '05666c4c-f0bf-4778-818e-30c0c80a379e',
            'path': 'P:/jfy/',
            'attributes': {"1001": "123", "1003": "good_part"}
            }]
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    r = requests.post(url, headers=headers, data = json.dumps(body))
    print(r.text)

#url = "http://10.202.162.122:8090/dataServiceRest/measurements?partUuids={68617beb-cffc-4f85-ba67-05dc2456898b}&searchCondition=4>[2015-01-01T00:00:00Z]"
#print(piwebget(url))
uuu = "http://10.202.162.122:8090/dataServiceRest/parts"
piwebpost(uuu)
#request = urllib.request.urlopen(url)
#info = request.read().decode('utf-8')
#jf = json.loads(info)
#print(jf[0]['attributes']['20047'])
#print(info.status)

#url2 = "http://10.202.162.122:8090/dataServiceRest/parts"
#dist = [
#        {
#            'uuid': '05666c4c-f0bf-4778-818e-30c0c80a379e',
#            'path': 'P:/jfy/',
#            'attributes': {"1001": "123456789", "1003": "good_part"}
#        }
#        ]
#d_json = json.dumps(dist)
#data = urllib.parse.urlencode(dist[0])
#data = data.encode('utf-8')
#request = urllib.request.Request(url2)
#request.add_header("Content-Type","application/json;charset=utf-8")
#f = urllib.request.urlopen(request, data)
#print(f.read().decode('utf-8'))