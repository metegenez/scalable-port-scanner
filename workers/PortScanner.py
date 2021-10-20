import socket
import concurrent.futures
from typing import List, Dict
from PortServiceGuesser import PortServiceGuesser
import itertools
import configparser
DEFAULT_TIMEOUT = 0.5
SUCCESS = 0
class PortScanner():
    def __init__(self):
        self.PortServiceGuesser = PortServiceGuesser()

    @staticmethod
    def check_port(host_port, timeout=DEFAULT_TIMEOUT):
        ''' Try to connect to a specified host on a specified port.
        If the connection takes longer then the TIMEOUT we set we assume
        the host is down. If the connection is a success we can safely assume
        the host is up and listing on port x. If the connection fails for any
        other reason we assume the host is down and the port is closed.'''

        # Create and configure the socket.
        sock = socket.socket()
        sock.settimeout(timeout)

        # the SO_REUSEADDR flag tells the kernel to reuse a local
        # socket in TIME_WAIT state, without waiting for its natural
        # timeout to expire.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Like connect(address), but return an error indicator instead
        # of raising an exception for errors returned by the C-level connect()
        # call (other problems, such as “host not found,” can still raise exceptions).
        # The error indicator is 0 if the operation succeeded, otherwise the value of
        # the erroneous.
        connected = sock.connect_ex(host_port) is SUCCESS
        # If you know the port number of a network service, you can find the service name using the getservbyport()
        # socket class function from the socket library.
        # You can optionally give the protocol name when calling this function.
        if connected:
            try:
                return socket.getservbyport(host_port[1])
            except:
                return "Unknown by socket."

        # Mark the socket closed.
        # The underlying system resource (e.g. a file descriptor)
        # is also closed when all file objects from makefile() are closed.
        # Once that happens, all future operations on the socket object will fail.
        # The remote end will receive no more data (after queued data is flushed).
        sock.close()

        # False if port is closed.
        return connected


    def portscan(self, target_ips: List[str], port_list=None) -> List[Dict]:

        if port_list is None:
            port_list = [80, 8080]
        all_tuples = list(itertools.product(target_ips, port_list))
        port_mask = PortScanner.scan_range(all_tuples) #There can be
        port_information = {}
        for i in range(len(all_tuples)):
            if not port_mask[i] is False:
                # Get port information from defaults if socket is not provide it.
                if port_mask[i] == "Unknown by socket.":
                    temp_port_info = self.guess_port_information(all_tuples[i][1])
                else:
                    temp_port_info = {"port": all_tuples[i][1], "service": port_mask[i],
                                      "desc": port_mask[i]}
                # Fill port information
                if all_tuples[i][0] in port_information:
                    port_information[all_tuples[i][0]].append(temp_port_info)
                else:
                    port_information[all_tuples[i][0]] = [temp_port_info]
        return [{item: port_information[item]} for item in port_information.keys()]

    def guess_port_information(self, port: int) -> Dict:
        """

        :param open_ports: List of open ports
        :return:
        """
        return {"port": port, "service": self.PortServiceGuesser.guess_service_short_name(port),
                                    "desc": self.PortServiceGuesser.guess_service_desc(port)}

    @staticmethod
    def scan_range(all_tuples) -> List[int]:
        config = configparser.ConfigParser()
        config.read('config.ini')
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(config["threading"]["max_thread"])) as executor:
            # Multithread trial.
            return list(executor.map(lambda target_tuple: PortScanner.check_port(target_tuple), all_tuples))



