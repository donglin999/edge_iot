#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from opcua import Client, ua
import time
import threading
from datetime import datetime
from apps.utils.baseLogger import Log



class OpcClient:
    def connect(self, url, device_name):
        try:
            client = Client(url, timeout=10)
            client.connect()
            #client.set_auto_reconnect(True)
            Log().printInfo(device_name + ': opc client is connected')
            return client
        except Exception as e:
            Log().printError(device_name + ':=================>')
            Log().printError(e)
            raise
