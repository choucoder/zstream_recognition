import mongoengine as mge

def custom_connect(host='127.0.0.1', port=27017):
    mge.connect('uno', host=host, port=port)
    #mge.connect('_zeye-cloud', host=host, port=port)

def test_default_connect(host='127.0.0.1', port=27017):
	database = 'dos'
	mge.connect(database, host=host, port=port)

