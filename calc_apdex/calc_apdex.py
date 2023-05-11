import requests
from ruxit.api.base_plugin import RemoteBasePlugin
import logging
from math import floor
from datetime import datetime

import pandas as pd
import numpy as np
import urllib.parse

logger = logging.getLogger(__name__)

class ApdexPluginRemote(RemoteBasePlugin):
    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)
        self.start_time=floor(datetime.now().timestamp()*1000) - self.pollingInterval
        self.end_time=None

    def initialize(self, **kwargs):
        self.name = self.config["name"]
        self.metric = self.config["metric"]
        self.pollingInterval = self.config["pollingInterval"]

    def getMetric(self):

        TIMEFRAME = "&from=now-7d"
        RESOLUTION = "&resolution=1m"
        METRIC = self.metric

        QUERY = "/v2/metrics/query?metricSelector=" + urllib.parse.quote(METRIC, safe='()') + RESOLUTION  + TIMEFRAME


        parametros = {
            'accept': 'application/json; charset=utf-8',
            'Authorization': 'Api-Token ' + API_TOKEN
        }

        respuesta = requests.get(API_URL + QUERY, headers=parametros, verify=False)
        if respuesta.status_code == 200:
            json_data = respuesta.json()
        else:
            print('Error al hacer la solicitud a la API. Código de estado: ', respuesta.status_code)

        metricId = json_data["result"][0]["metricId"]

        dimensionMap = json_data["result"][0]["data"][0]["dimensionMap"]
        timestamps = json_data["result"][0]["data"][0]["timestamps"]
        values = json_data["result"][0]["data"][0]["values"]

        DF_Data = pd.DataFrame( np.c_[timestamps, values], columns=['Timestamp', 'Value'])

        # Elimino las columnas sin valor (None)
        DF_Data.dropna(axis=0, inplace=True)

        # Considera solo LaV de 8.00 a 20.00hs

        DF_Data['Timestamp'] = pd.to_datetime(DF_Data['Timestamp'], unit='ms')
        filtro = ((DF_Data['Timestamp'].dt.dayofweek >= 0) & (DF_Data['Timestamp'].dt.dayofweek <= 4)) & ((DF_Data['Timestamp'].dt.hour >= 8) & (DF_Data['Timestamp'].dt.hour <= 19))

        DF_Data = DF_Data[filtro]
        #DF_Data.to_csv('datos.csv', index=False)

        X = np.array(DF_Data["Value"], dtype=float)

        # Redondeo de decimales
        X = np.around(X, decimals=3)

        #moda = stat.mode(X)
        #moda_cont = np.count_nonzero(X == moda)

        # Calcular los valores estadísticos
        p10 = np.percentile(X, 10)
        p50 = np.percentile(X, 50)
        p90 = np.percentile(X, 90)

        mediana = np.median(X)
        promedio = np.mean(X)
        desviacion = np.std(X)

        return p50

    def query(self, **kwargs):
        '''
        Routine call from the ActiveGate
        '''

        group = self.topology_builder.create_group(identifier="ApdexGroup", group_name="APDEX")
        device = group.create_device(identifier=self.name, display_name="APDEX")
        logger.info("Topology: group name=%s, device name=%s", group.name, device.name)
        
        self.end_time = floor(datetime.now().timestamp()*1000)
        if self.end_time - self.start_time >= self.pollingInterval:
            val = self.getMetric()  
            self.start_time = self.end_time + 1
            device.absolute(key='apdex', value=val, dimensions = { "name" : self.name })
            logger.info("APDEX" + " | " + self.name + " = " + str(val))

        
        ## Metadata:
        #device.report_property(key='IP addresses', value=self.ipservidor)
