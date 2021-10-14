import redis
from datetime import datetime
r = redis.Redis(host='localhost', port=6379, db=0)
import time
# Poll queue
# Scan ports for each IP
# Index findings into elasticsearch

def pool_queue():
    while len(r.execute_command("ZRANGEBYSCORE", "due", "-inf",  datetime.now().timestamp(), "LIMIT", 0, 1)) > 0:
        msg_id = r.execute_command("ZRANGEBYSCORE", "due", "-inf",  datetime.now().timestamp(), "LIMIT", 0, 1)[0]
        ip_address = r.execute_command("HGET", "messages", msg_id)
        r.execute_command("ZREM", "due", msg_id)
        r.execute_command("HDEL", "messages", msg_id)
        print(ip_address)
        time.sleep(0.6)



def frequent_job():
    while True:
        print("Pooling working")
        pool_queue()
        time.sleep(5)

def scan_single_ip(port_range):
    #This will multihreaded
    pass


def index_findings():
    pass


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    frequent_job()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/