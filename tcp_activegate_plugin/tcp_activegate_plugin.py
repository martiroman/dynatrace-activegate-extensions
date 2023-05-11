import requests
from ruxit.api.base_plugin import RemoteBasePlugin
import logging
import paramiko

logger = logging.getLogger(__name__)

class NetworkConnectionsPluginRemote(RemoteBasePlugin):
    def initialize(self, **kwargs):
        self.servername = self.config["servername"]
        self.ipservidor = self.config["ipservidor"]
        self.usuario = self.config["usuario"]
        self.password = self.config["password"]
        self.puerto = self.config["puerto"]
        self.patron = self.config["patron"]

    def query(self, **kwargs):
        group = self.topology_builder.create_group(identifier="NetworkConnectionsGroup", group_name="Network Connections")

        device = group.create_device(identifier=self.ipservidor, display_name=self.servername)

        logger.info("Topology: group name=%s, device name=%s", group.name, device.name)
        
        ## Conexion SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(self.ipservidor, self.puerto, self.usuario, self.password)
       
        patrones = self.patron.split(",")

        for patron in patrones:
            data = patron.split("|")
            patron = data[1]
            service = data[0]

            ## Metrica Established 
            command = 'netstat -na | grep -w "'+ patron +'" | grep ESTABLISHED | wc -l'
            stdin, stdout, stderr = ssh.exec_command(command)
            result = stdout.read().decode()
        
            device.absolute(key='tcp.established', value=result, dimensions = { "service" : service })
            device.report_property(key='Servicio ' + service, value=patron)
            
            logger.info(service + " | " + patron + " - " + "established=" + result)
        
            ## Metrica Time Wait
            command = 'netstat -na | grep -w "'+ patron +'" | grep TIME_WAIT | wc -l'
            stdin, stdout, stderr = ssh.exec_command(command)
            result = stdout.read().decode()

            device.absolute(key='tcp.time_wait', value=result, dimensions = { "service" : service })
        
            device.report_property(key='Servicio ' + service, value=patron)
            
            logger.info(service + " | " +  patron + " - " + "time_wait=" + result)
        
        ## Cierre SSH
        ssh.close()

        ## Metadata:
        device.report_property(key='IP addresses', value=self.ipservidor)
