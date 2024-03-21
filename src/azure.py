import http.client, urllib.request, urllib.parse, urllib.error, base64

headers = {
    # Request headers
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': 'ENV KEY',
}
params = urllib.parse.urlencode({
    # Request parameters
    'model-version': 'latest',
})
try:
    with open('src/static/kitchen.jpg', 'rb') as image_file:
        conn = http.client.HTTPSConnection('voicerobots.cognitiveservices.azure.com')
        conn.request("POST", "/vision/v3.2/detect?%s" % params, image_file.read(), headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))