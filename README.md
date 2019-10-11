# PyStarChat

A python client for [StarChat](https://github.com/GetJenny/starchat),
the conversational engine provided by [GetJenny](https://www.getjenny.com).

## Usage

### Package installation
To install the package, run the following commands:
```
pip install -e git+https://github.com/GetJenny/python-starchat-client#egg=py_starchat
```

### StarChat installation
The client needs a running StarChat instance, see the
[StarChat documentation](https://getjenny.github.io/starchat-doc/)
and follow the installation steps.
Following the standard installation process, you should be able to reach StarChat
at `http://localhost:8888`. Check it by typing in you terminal
`curl -X GET localhost:8888`. If you get `OK`, StarChat is up.

### Elasticsearch setup
Configure Elasticsearch performing the operations described in the StarChat documentation
(see under _Elasticsearch Configuration_).

### Setup the client and check connection to StarChat

To import the package and setup the client, open a python console and type
```
>>> from py_starchat.StarChatClient import StarChatClient
>>> sc_client = StarChatClient(url = 'http://localhost',
...                            port = '8888',
...                            version='5.1')
>>> sc_client.check_service()
True
```

### Troubleshooting
If something went wrong, you can inspect the StarChat address by typing
```
>>> sc_client.address
```
in your python console and copy the address in your browser to check if you are
able to connect to the StarChat server. If not, refer to the StarChat
documentation and make sure that StarChat is running before testing the client.
