import subprocess, platform
import concurrent.futures
import re
import configparser
class IPPinger:
    def __init__(self):

        pass

    @staticmethod
    def ping(host_or_ip, packets=1, timeout=1000):
        ''' Calls system "ping" command, returns True if ping succeeds.
        Required parameter: host_or_ip (str, address of host to ping)
        Optional parameters: packets (int, number of retries), timeout (int, ms to wait for response)
        Does not show any output, either as popup window or in command line.
        Python 3.5+, Windows and Linux compatible
        '''
        # The ping command is the same for Windows and Linux, except for the "number of packets" flag.
        if platform.system().lower() == 'windows':
            command = ['ping', '-n', str(packets), '-w', str(timeout), host_or_ip]
            # run parameters: capture output, discard error messages, do not show window
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, creationflags=0x08000000)
            # 0x0800000 is a windows-only Popen flag to specify that a new process will not create a window.
            # On Python 3.7+, we can use a subprocess constant:
            #   result = subprocess.run(command, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if IPPinger.guess_online_win(result):
                # This method may not be accurate all the time.
                # However, it will give an idea of the underlying operating system in a remote system.
               return IPPinger.guess_os_win(result)
            else:
                return False
        else:
            command = ['ping', '-c', str(packets), '-w', str(timeout), host_or_ip]
            # run parameters: discard output and error messages
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "Unknown" if IPPinger.guess_online_linux(result) else False #OS detection is not implemented for Linux

    @staticmethod
    def guess_online_win(result):
        """
        On windows 7+, ping returns 0 (ok) when host is not reachable; to be sure host is responding,
        we search the text "TTL=" on the command output. If it's there, the ping really had a response.
        :param result:
        :return:
        """
        return result.returncode == 0 and b'TTL=' in result.stdout
    @staticmethod
    def guess_online_linux(result):
        return result.returncode == 0

    @staticmethod
    def guess_os_win(result):
        ttl = re.search(b'TTL=(.*)\r', result.stdout).group(1).decode()
        if ttl == "64":
            return "Linux"
        elif ttl == "128":
            return "Windows"
        else:
            return "Unknown"

    def ping_hosts(self, all_hosts):
        """

        :param all_hosts: List of string
        :return: Results of ALL ips, not only online ones.
        """
        ping_result = IPPinger.get_ping_results(all_hosts)
        return ping_result

    @staticmethod
    def generate_message_mask(ping_result):
        return [temp != False for temp in ping_result]

    @staticmethod
    def get_ping_results(all_hosts):
        """
        Multithreaded pinging for given list of ip adresses.
        :param all_hosts: List of string
        :return:
        """
        config = configparser.ConfigParser()
        config.read('config.ini')
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(config["threading"]["max_thread"])) as executor:
            return list(executor.map(lambda host: IPPinger.ping(host), all_hosts))