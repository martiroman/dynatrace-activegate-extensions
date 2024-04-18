from ruxit.api.base_plugin import RemoteBasePlugin
import logging
import requests
import base64

logger = logging.getLogger(__name__)

class IsilonQuotaPluginRemote(RemoteBasePlugin):
    def initialize(self, **kwargs):
        self.ip = self.config["ip"]
        self.user = self.config["user"]
        self.password = self.config["password"]
        self.url = 'https://{self.ip}:8080/platform/6/quota/quotas'

    def query(self, **kwargs):
        self.group = self.topology_builder.create_group(identifier="StorageGroup", group_name="Storage")
        self.device = self.group.create_device(identifier=self.ip, display_name="isilon-" + self.ip)

        logger.info("Topology: group name=%s, device name=%s", self.group.name, self.device.name)
        self.device.report_property(key='IP addresses', value=self.ip)

        self.queryAPI()


    def queryAPI(self):
        try:
            encoded_credentials = base64.b64encode(f"{self.user}:{self.password}".encode()).decode('utf-8')
            headers = {"Authorization": f"Basic {encoded_credentials}"}

            response = requests.get(self.url, headers=headers)

            if response.status_code == 200:
                isi_object = response.json()
                quotas = isi_object['quotas']
                
                for quota in quotas:
                    path = quota["path"]
                    print("Path:", path)

                    thresholds = quota["thresholds"]
                    hard = thresholds.get("hard")
                    usage = quota["usage"]
                    logical = usage.get("logical")

                    if hard is None or logical is None:
                      print(" No hay datos ", path)
                      continue

                    hard = hard #/ (1024 * 1024 * 1024 * 1024)
                    logical = logical #/ (1024 * 1024 * 1024 * 1024)

                    dif = hard - logical
                    div = round((logical / hard) * 100,2)
                    
                
                    self.send_metric(path, div)

                logger.info(quotas)
            else:
                print(f"Error: {response.status_code}") 
            
        except Exception as e:
            print("Error:", e)



    def send_metric(self, path, usage):
        logger.info(path + "- " + "usage=" + usage)

        self.device.absolute(key=path, value=usage)
#        self.device.report_property(key='quota path', value=usage)
