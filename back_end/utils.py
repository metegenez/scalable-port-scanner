import ipaddress

def find_ips_in_range(start, end):
    start = ipaddress.ip_address(start)
    end = ipaddress.ip_address(end)
    result = []
    while start <= end:
        result.append(str(start))
        start += 1
    return result


def calculate_ip_addresses(ip_range):
    if not ip_range.__contains__("/") and not ip_range.__contains__("-"):
        all_ip_list = [ip_range]
    elif ip_range.__contains__("/"):
        ip_net = ipaddress.ip_network(u"{}".format(ip_range))
        all_ip_list = [str(i) for i in list(ip_net.hosts())]
    elif ip_range.__contains__("-"):
        all_ip_list = find_ips_in_range(ip_range.split("-")[0], ip_range.split("-")[1])
    else:
        raise
    return all_ip_list