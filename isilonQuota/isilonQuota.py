from ruxit.api.base_plugin import RemoteBasePlugin
import logging
import requests
import base64
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

class IsilonQuotaPluginRemote(RemoteBasePlugin):
    def initialize(self, **kwargs):
        self.ip = self.config["ip"]
        self.user = self.config["user"]
        self.password = self.config["password"]
        self.url = f'https://{self.ip}:8080/platform/6/quota/quotas'

    def query(self, **kwargs):
        self.group = self.topology_builder.create_group(identifier="StorageGroup", group_name="Storage")
        self.device = self.group.create_device(identifier=self.ip, display_name="isilon-" + self.ip)

        logger.info("Topology: group name=%s, device name=%s", self.group.name, self.device.name)
        self.device.report_property(key='IP addresses', value=self.ip)

        encoded_credentials = base64.b64encode(f"{self.user}:{self.password}".encode()).decode('utf-8')
        headers = {"Authorization": f"Basic {encoded_credentials}"}

        response = requests.get(self.url, headers=headers, verify=False)
        logger.info(f"Response: {response.status_code} - {response.headers}")

        if response.status_code < 400:
            isi_object = response.json()
            quotas = isi_object['quotas']
            
            for quota in quotas:
                path = quota["path"]

                thresholds = quota["thresholds"]
                hard = thresholds.get("hard")
                usage = quota["usage"]
                logical = usage.get("logical")

                if hard is None or logical is None:
                    continue

                hard = hard
                logical = logical
                usage = round((logical / hard) * 100,2)
                
                #logger.info("quota." + path + "- " + "usage=" + str(usage))

                if usage > 100:
                    usage = 100
                if usage < 0:
                    usage = 0

                self.device.absolute(key="isilon.quota", value=usage, dimensions = { "ip" : self.ip, "path" : path })

        else:
            logger.error(f"Error: {response.status_code}") 
                            