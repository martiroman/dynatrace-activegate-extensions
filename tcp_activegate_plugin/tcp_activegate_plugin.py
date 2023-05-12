from ruxit.api.base_plugin import RemoteBasePlugin
import logging
import paramiko

logger = logging.getLogger(__name__)

class NetworkConnectionsPluginRemote(RemoteBasePlugin):
    def initialize(self, **kwargs):
        self.servername = self.config.get("servername")
        self.ipservidor = self.config.get("ipservidor")
        self.usuario = self.config.get("usuario")
        self.password = self.config.get("password") if self.config.get("password") else None
        self.puerto = self.config.get("puerto")
        self.patron = self.config.get("patron")
        self.key = self.config.get("ssh_key_file") if self.config.get("ssh_key_file") else None
        self.passphrase = self.config.get("ssh_key_passphrase") if self.config.get("ssh_key_passphrase") else None

    def query(self, **kwargs):
        self.group = self.topology_builder.create_group(identifier="NetworkConnectionsGroup", group_name="Network Connections")
        self.device = self.group.create_device(identifier=self.ipservidor, display_name=self.servername)

        logger.info("Topology: group name=%s, device name=%s", self.group.name, self.device.name)
        self.device.report_property(key='IP addresses', value=self.ipservidor)
        
        patrones = self.patron.split(",")
        ssh = self.connectSSH()
        for patron in patrones:
            self.getMetric(patron, "established", ssh)
            self.getMetric(patron, "time_wait", ssh)
        
        ssh.close()     
        
    def connectSSH(self):
        ## Conexion SSH
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)

        if self.key is not None:
                logger.info("Conexion usando Key")
                ssh.connect(self.ipservidor, port=self.puerto, username=self.usuario, key_filename=self.key, passphrase=self.passphrase)
        else:
                logger.info("Conexion usando")
                ssh.connect(self.ipservidor, port=self.puerto, username=self.usuario, password=self.password, timeout=20)
        return ssh

    def getMetric(self, patron, estado, ssh):
        data = patron.split("|")
        patron = data[1]
        service = data[0]

        command = 'netstat -na | grep -w "'+ patron +'" | grep -i '+ estado + ' | wc -l'
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode()
                  
        logger.info(service + " | " + patron + " - " + "estado=" + result)

        self.device.absolute(key='tcp.'+ estado, value=result, dimensions = { "service" : service })
        self.device.report_property(key='Servicio ' + service, value=patron)

        return 1