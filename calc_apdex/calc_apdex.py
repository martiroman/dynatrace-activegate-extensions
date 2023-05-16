from ruxit.api.base_plugin import RemoteBasePlugin
import logging
import requests
from datetime import datetime,timedelta
from croniter import croniter
import pandas as pd
import numpy as np
import urllib.parse

logger = logging.getLogger(__name__)

class ApdexPluginRemote(RemoteBasePlugin):

    def initialize(self, **kwargs):
        self.name = self.config["name"]
        self.metric = self.config["metric"]
        self.token = self.config["token"]
        self.endpoint = self.config["endpoint"]
        self.schedule = self.config["schedule"] or "*/1 * * * *"
        self.timeframe = self.config["timeframe"] or "now-24h"
        #self.rango = self.config["rango"] or "8-20"

    def sendMetric(self, val):
        parametros = {
            'accept': 'application/json; charset=utf-8',
            'Authorization': 'Api-Token ' + self.token,
            'Content-Type': 'text/plain; charset=utf-8'
        }

        data = 'apdex.horalab,app=' + self.name +' ' + str(val)
        query = "/v2/metrics/ingest?"

        respuesta = requests.post(self.endpoint + query, headers=parametros, data=data, verify=False)

        if respuesta.status_code < 300:
            logger.info("Metrica enviada")
        else:
            logger.info("Error al enviar la metrica. Codigo de estado: ", respuesta.status_code)

    def getMetric(self):

        TIMEFRAME = "&from=" + self.timeframe
        RESOLUTION = "&resolution=1m"
        metric = self.metric
        query = "/v2/metrics/query?metricSelector=" + urllib.parse.quote(metric, safe='()') + RESOLUTION  + TIMEFRAME

        parametros = {
            'accept': 'application/json; charset=utf-8',
            'Authorization': 'Api-Token ' + self.token
        }

        respuesta = requests.get(self.endpoint + query, headers=parametros, verify=False)

        if respuesta.status_code == 200:
            json_data = respuesta.json()
        else:
            logger.info("Error al hacer la solicitud API. Codigo de estado: ", respuesta.status_code)

        metricId = json_data["result"][0]["metricId"]
        dimensionMap = json_data["result"][0]["data"][0]["dimensionMap"]
        timestamps = json_data["result"][0]["data"][0]["timestamps"]
        values = json_data["result"][0]["data"][0]["values"]

        DF_Data = pd.DataFrame( np.c_[timestamps, values], columns=['Timestamp', 'Value'])

        # Elimino las columnas sin valor (None)
        DF_Data.dropna(axis=0, inplace=True)


        DF_Data['Timestamp'] = pd.to_datetime(DF_Data['Timestamp'], unit='ms')
        #filtro = ((DF_Data['Timestamp'].dt.dayofweek >= 0) & (DF_Data['Timestamp'].dt.dayofweek <= 4)) & ((DF_Data['Timestamp'].dt.hour >= 8) & (DF_Data['Timestamp'].dt.hour <= 19))

        #DF_Data = DF_Data[filtro]

        X = np.array(DF_Data["Value"], dtype=float)

        # Redondeo de decimales
        #X = np.around(X, decimals=3)

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
        now = datetime.now().astimezone()
        cron = croniter(self.schedule, now, ret_type=datetime)
        previous_execution = cron.get_prev().astimezone()
        next_execution = cron.get_next().astimezone()

        time_since = now - previous_execution
        if time_since <= timedelta(minutes=1):
            val = self.getMetric()

            self.sendMetric(val)

            logger.info(now.strftime("%Y-%M-%d %H:%M:%S") + " : APDEX  | " + self.name + " = " + str(val))

