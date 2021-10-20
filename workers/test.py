import unittest
import socket
from unittest import mock
from containers import Container
from PortScanner import PortScanner

class PortscanTesting(unittest.TestCase):


    def test_pinger(self):
        s = socket.socket()  # Create a socket object
        host = socket.gethostname()  # Get local machine name
        port = 12345  # Reserve a port for your service.
        s.bind((host, port))  # Bind to the port
        port_scan_mock = mock.Mock(spec=PortScanner)
        with Container.port_scanner.override(port_scan_mock):
            port_scanner = Container.port_scanner()
            result = port_scanner.check_port(("localhost", 12345))


        self.assertTrue(port_scan_mock.check_port(("localhost", 12345)))
        s.close()

    def test_pinger_multithread(self):
        s = socket.socket()  # Create a socket object
        host = socket.gethostname()  # Get local machine name
        port = 12365  # Reserve a port for your service.
        s.bind((host, port))
        port_scan_mock = mock.Mock(spec=PortScanner)
        open_ports = port_scan_mock.scan_range("localhost", [12365, 12368]).items()
        self.assertTrue(12345 in open_ports)
        self.assertTrue(12346 not in open_ports)
        s.close()

if __name__ == '__main__':
    unittest.main()
