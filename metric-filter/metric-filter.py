from ruxit.api.base_plugin import RemoteBasePlugin
import logging
import requests
from datetime import datetime,timedelta
from croniter import croniter
import pandas as pd
import numpy as np
import urllib.parse
import time

logger = logging.getLogger(__name__)

class MetricFilterPluginRemote(RemoteBasePlugin):

    def initialize(self, **kwargs):
        self.name = self.config["name"]
        self.metric = self.config["metric"]
        self.token = self.config["token"]
        self.endpoint = self.config["endpoint"]
        self.schedule = self.config["schedule"] or "*/1 * * * *"
        self.tag = self.config["tag"] or "schedule1"
        self.schedule2 = self.config["schedule2"] or "0 * * * *"
        self.tag2 = self.config["tag2"] or "schedule2"
        self.timeframe = self.config["timeframe"] or "now-1h"
        self.type = self.config["type"]

    def sendMetric(self, data):
        '''
        Routine send Metric via API to Dynatrace
        '''
        parametros = {
            'accept': 'application/json; charset=utf-8',
            'Authorization': 'Api-Token ' + self.token,
            'Content-Type': 'text/plain; charset=utf-8'
        }

        query = "/v2/metrics/ingest?"

        respuesta = requests.post(self.endpoint + query, headers=parametros, data=data, verify=False)

        if respuesta.status_code < 300:
            logger.info("Metrica enviada")
        else:
            logger.info("Error al enviar la metrica. Codigo de estado: ", respuesta.status_code)

    def getData(self):
        '''
        Routine extract Metric from Dynatrace via API
        '''
        now = datetime.now().astimezone()

        timeframe = "&from=" + self.timeframe
        resolution = "&resolution=1m"
        metric = self.metric
        
        if self.type == "Metric":
            query = "/v2/metrics/query?metricSelector=" + urllib.parse.quote(metric, safe='()') + resolution  + timeframe
        else:
            hora_atras = now - datetime.timedelta(hours=1)
            timestamp = int(time.mktime(hora_atras.timetuple()))
            params = "&startTimestamp=" + timestamp +"&addDeepLinkFields=false&explain=false"
            query = "/v1/userSessionQueryLanguage/table?query=" + urllib.parse.quote(metric, safe='()') + params

        parametros = {
            'accept': 'application/json; charset=utf-8',
            'Authorization': 'Api-Token ' + self.token
        }

        respuesta = requests.get(self.endpoint + query, headers=parametros, verify=False)

        if respuesta.status_code == 200:
            json_data = respuesta.json()
        else:
            logger.info("Error al hacer la solicitud API. Codigo de estado: ", respuesta.status_code)

        return json_data

    def processUSQL(self, json_data):
        return 0
    
    def processMetric(self, tag, json_data):
        metricId = json_data["result"][0]["metricId"]
        dimensionMap = json_data["result"][0]["data"][0]["dimensionMap"]
        timestamps = json_data["result"][0]["data"][0]["timestamps"]
        values = json_data["result"][0]["data"][0]["values"]

        DF_Data = pd.DataFrame( np.c_[timestamps, values], columns=['Timestamp', 'Value'])

        # Elimino las columnas sin valor (None)
        DF_Data.dropna(axis=0, inplace=True)


        DF_Data['Timestamp'] = pd.to_datetime(DF_Data['Timestamp'], unit='ms')

        X = np.array(DF_Data["Value"], dtype=float)

        # Calcular los valores estadísticos
        p10 = np.percentile(X, 10)
        p50 = np.percentile(X, 50)
        p90 = np.percentile(X, 90)

        mediana = np.median(X)
        promedio = np.mean(X)
        desviacion = np.std(X)

        metric = 'apdex.filter.' + self.name +',tag=' + tag +' ' + str(p50)
        self.sendMetric(metric)

        return p50

    def cronCheck(self, now, scheduler):
        cron_expr_list = scheduler.split(';')
        ejecuta = 0
        for ncron in cron_expr_list:
            cron = croniter(ncron, now, ret_type=datetime)
            previous_execution = cron.get_prev().astimezone()
            next_execution = cron.get_next().astimezone()

            time_since = now - previous_execution
            if time_since <= timedelta(minutes=1):
                ejecuta = 1
        return ejecuta

    def query(self, **kwargs):
        '''
        Routine call from the ActiveGate
        '''
        now = datetime.now().astimezone()

        tag = ""
        if self.cronCheck(now, self.schedule):
            tag = self.tag
        
        if self.cronCheck(now, self.schedule2):
            tag = self.tag2

        if tag != "":
            jsonData = self.getData()
            if self.type == "Metric":
                val = self.processMetric(tag, jsonData)
            else:
                val = self.processMetric(tag, jsonData)

            logger.info(now.strftime("%Y-%M-%d %H:%M:%S") + " : APDEX " + tag + ' | ' + self.name + " = " + str(val))
