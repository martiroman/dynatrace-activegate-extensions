from ruxit.api.base_plugin import RemoteBasePlugin
import logging
import subprocess

logger = logging.getLogger(__name__)

OID_LOAD =         ".1.3.6.1.2.1.25.3.3.1.2"
OID_CPU_IDLE =     ".1.3.6.1.4.1.2021.11.11.0"
OID_MEMORY_TOTAL = ".1.3.6.1.4.1.2021.4.5.0"
OID_MEMORY_FREE =  ".1.3.6.1.4.1.2021.4.6.0"
            
class LinuxSnmpMetricsPluginRemote(RemoteBasePlugin):
    def initialize(self, **kwargs):
        self.hostname = self.config.get("hostname")
        self.ip = self.config.get("ip")
        self.community = self.config.get("community") if self.config.get("community") else "default"
        self.port = self.config.get("port") if self.config.get("port") else "161"

    def query(self, **kwargs):
        self.group = self.topology_builder.create_group(identifier="LinuxSnmpHostGroup", group_name="Linux SNMP Host")
        #self.device = self.group.create_device(identifier=self.ip, display_name=self.hostname)
        self.device = self.group.create_device(identifier="test", display_name=self.hostname)

        logger.info("Topology: group name=%s, device name=%s", self.group.name, self.device.name)
        self.device.report_property(key='IP addresses', value=self.ip)

        self.getCPULoad()
        self.getMemory()

    def snmpwalk(self, oid):
        command = ["snmpwalk", "-v", "2c", "-c", self.community, f"{self.ip}:{self.port}", oid]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            return result.stdout
        else:
            logger.error(f"Error executing SNMPwalk: {result.stderr}")
            return ""

    def getVal(self, input_string):
        start_index = input_string.find("INTEGER:") + len("INTEGER:")
        last_number = input_string[start_index:].strip()

        return last_number
    
    def getCPULoad(self):
        try:
            cpu_idle = self.getVal(self.snmpwalk(OID_CPU_IDLE))
            cpu_busy = 100 - int(cpu_idle)

            logger.info(f"{self.hostname} | CPU Usage - value: {cpu_busy}")
            self.device.absolute(key='linux.cpu.usage', value=cpu_busy, dimensions={"host": self.hostname})

        except Exception as e:
            logger.error(f"Error CPU Usage: {str(e)}")

        return 1
    
    def getMemory(self):
        try:
            mem_total = self.getVal(self.snmpwalk(OID_MEMORY_TOTAL)).split()[0]
            mem_free = self.getVal(self.snmpwalk(OID_MEMORY_FREE)).split()[0]

            mem_used = 100 - 100 * (int(mem_free) / int(mem_total))

            logger.info(f"{self.hostname} | Memory - value: {mem_used}")
            self.device.absolute(key='linux.mem', value=mem_used, dimensions={"host": self.hostname})

        except Exception as e:
            logger.error(f"Error Memory: {str(e)}")

        return 1