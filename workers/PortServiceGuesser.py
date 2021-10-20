import json

class PortServiceGuesser:
    def __init__(self):
        self.read_files()
        pass

    def read_files(self):
        with open("docs/port_service_set.json") as json_file:
            self.services = json.load(json_file)
        with open("docs/port_desc.json") as json_file:
            self.descriptions = json.load(json_file)


    def guess_service_short_name(self, port):
        if isinstance(port, int):
            port = str(port)
        return self.services[port]

    def guess_service_desc(self, port):
        if isinstance(port, int):
            port = str(port)
        return self.descriptions[port]
