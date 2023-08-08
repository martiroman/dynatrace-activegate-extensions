from ruxit.api.base_plugin import RemoteBasePlugin
import logging
import sys
import subprocess

logger = logging.getLogger(__name__)

class LinuxSnmpPluginRemote(RemoteBasePlugin):
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

    def snmpwalk(self, oid):
        command = ["snmpwalk", "-v", "2c", "-c", self.community, f"{self.ip}:{self.port}", oid]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            return result.stdout
        else:
            logger.error(f"Error executing SNMPwalk: {result.stderr}")
            return " "

    def getCPULoad(self):
        OID_LOAD = ".1.3.6.1.2.1.25.3.3.1.2"

        try:
            output = self.snmpwalk(OID_LOAD)
            cpu_load_values = [int(value) for value in output.strip().split("\n")]
            cpu_count = len(cpu_load_values)

            if cpu_count != 0:
                avg_cpu_load = sum(cpu_load_values) / cpu_count
                logger.info(f"{self.hostname} | CPU Load - value: {avg_cpu_load}")
                self.device.absolute(key='linux.cpu.load', value=avg_cpu_load, dimensions={"host": self.hostname})

        except Exception as e:
            logger.error(f"Error CPU LOAD: {str(e)}")

        return 1
