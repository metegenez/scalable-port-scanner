from PortScanner import PortScanner
import time
from IPPinger import IPPinger
import ipaddress
from services import*

# Poll queue
# Scan ports for each IP
# Index findings into elasticsearch

class ScanWorker():

    def __init__(self):
        self.redis = RedisMBConnector()
        self.elastic = ElasticService()
        self.port_scanner = PortScanner()
        self.pinger = IPPinger()

    def pool_queue(self):
        # Pooling is periodically done by a simple infinite while loop. When service is alive, it tries to get
        # IP address and port range from message broker which is a Redis DB in this case.
        # We are pooling first task from REDIS and scan the ip address.
        while self.redis.if_batch_contains_messages():
            message = self.redis.get_last_message()
            # if message is None: #Workers can compete on each message.
            #     continue
            self.execute_message(message)



    def execute_message(self, message):
        target_ips, port_list, job_id = ScanWorker.convert_message_to_variables(message)
        print("{} is executing.".format(job_id))
        self.elastic.index_scan_start(job_id)
        all_ips = ScanWorker.calculate_ip_addresses(target_ips)
        # Get ip address OS information during ping with TTL defaults.
        information = self.pinger.ping_hosts(all_ips)
        ip_address_with_information = {p:f for (p, f) in zip(all_ips, information) if f != False}
        # Index OS findings
        self.elastic.index_os_findings(job_id, [{target_ip: {"status": "Available", "OS": ip_info} for target_ip, ip_info in ip_address_with_information.items()}])
        # Scan ports
        port_result = self.port_scanner.portscan(list(ip_address_with_information.keys()), port_list)
        # Index findings on Elasticsearch DB.
        self.elastic.index_port_findings(job_id, port_result)
        # Index Status as finished
        self.elastic.index_scan_result(job_id)




    @staticmethod
    def convert_message_to_variables(message):
        target_ip = message.decode().split("#")[0]
        if not message.decode().split("#")[1].__contains__("-"):
            # '192.162.32.1#80,8080,50,10'
            return target_ip, [int(port) for port in message.decode().split("#")[1].split(",")], \
                   message.decode().split("#")[2]
        else:
            # '192.162.32.1#0-1000'
            min_range = message.decode().split("#")[1].split("-")[0]
            max_range = message.decode().split("#")[1].split("-")[1]
            return target_ip, list(range(int(min_range), int(max_range) + 1)), message.decode().split("#")[2]

    def start(self):
        while True:
            print("Pooling working")
            self.pool_queue()
            time.sleep(2)

    @staticmethod
    def find_ips_in_range(start, end):
        start = ipaddress.ip_address(start)
        end = ipaddress.ip_address(end)
        result = []
        while start <= end:
            result.append(str(start))
            start += 1
        return result

    @staticmethod
    def calculate_ip_addresses(ip_range):
        if not ip_range.__contains__("/") and not ip_range.__contains__("-"):
            all_ip_list = [ip_range]
        elif ip_range.__contains__("/"):
            ip_net = ipaddress.ip_network(u"{}".format(ip_range))
            all_ip_list = [str(i) for i in list(ip_net.hosts())]
        elif ip_range.__contains__("-"):
            all_ip_list = ScanWorker.find_ips_in_range(ip_range.split("-")[0], ip_range.split("-")[1])
        else:
            raise
        return all_ip_list




