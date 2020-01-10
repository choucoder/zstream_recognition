from lib.utils import *
from requests import post

url = '0.0.0.0:8443'

filename = '1578634264880298-f6e1.jpg'
raw = encodeImg('queue/{}'.format(filename))

response = post(
    url = 'http://{}/person-query'.format(url),
    json = {
        'picture': raw,
        'filename': filename,
        'mode': "queue",
        "wait": True,
        'key': "hash"
    },
)
print(response.json())