from elasticsearch import Elasticsearch, ElasticsearchException
import redis
from datetime import datetime
from uuid import uuid4
import configparser
class Connector():
    def __init__(self) -> None:
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        pass


class RedisMBConnector(Connector):
    def __init__(self):
        super().__init__()
        self.r = redis.Redis(host=self.config["host"]["ip"],
        port=6379,
        db=0,
        client_name="worker"+str(uuid4()))

    def if_batch_contains_messages(self):
        try:
            return len(
                self.r.execute_command("ZRANGEBYSCORE", "due", "-inf", "+inf", "LIMIT", 0, 1)) > 0
        except redis.exceptions.RedisError as e:
            raise Exception(e)


    def get_last_message(self):
        try:
            msgs = self.r.execute_command("ZRANGEBYSCORE", "due", "-inf", datetime.now().timestamp(), "LIMIT", 0, 1)
            if len(msgs) > 0:
                msg_id = msgs[0] #Workers can be compete on each messages
            else:
                return None
            message = self.r.execute_command("HGET", "messages", msg_id)
            self.r.execute_command("ZREM", "due", msg_id)
            self.r.execute_command("HDEL", "messages", msg_id)
            return message
        except redis.exceptions.RedisError as e:
            raise Exception(e)



class ElasticService(Connector):
    def __init__(self):
        super().__init__()
        self.es = Elasticsearch(host=self.config["host"]["ip"])

    def index_scan_start(self, job_id):
        try:
            self.es.update(index="scans", id=job_id,
                           body={
                               "script": {
                                   "inline": "ctx._source.status='Scanning'",
                                   "lang": "painless"
                               }
                           })
            time = str(datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'))
            self.es.update(index="scans", id=job_id,
                           body={
                               "script": {
                                   "inline": f"ctx._source.start_timestamp='{time}'",
                                   "lang": "painless"
                               }
                           })
        except ElasticsearchException as e:
            raise Exception(e)
    def index_scan_result(self, job_id):
        # Update scan status.
        try:
            self.es.update(index="scans", id=job_id,
                           body={
                               "script": {
                                   "inline": "ctx._source.status='Finished'",
                                   "lang": "painless"
                               }
                           })
            time = str(datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'))
            self.es.update(index="scans", id=job_id,
                           body={
                               "script": {
                                   "inline": f"ctx._source.finished_timestamp='{time}'",
                                   "lang": "painless"
                               }
                           })
        except ElasticsearchException as e:
            raise Exception(e)

    def index_port_findings(self, job_id, ip_result):
        # Update findings accordingly.
        try:
            self.es.update(index="scans", id=job_id,
                           body={
                               "script": {
                                   "source": "ctx._source.ip_port_info.addAll(params.ip_port_info)",
                                   "lang": "painless",
                                   "params": {
                                       "ip_port_info": ip_result
                                   }
                               }
                           })
        except ElasticsearchException as e:
            raise Exception(e)

    def index_os_findings(self, job_id, ip_result):
        try:
            self.es.update(index="scans", id=job_id,
                           body={
                               "script": {
                                   "source": "ctx._source.ip_info.addAll(params.ip_info)",
                                   "lang": "painless",
                                   "params": {
                                       "ip_info": ip_result
                                   }
                               }
                           })
        except ElasticsearchException as e:
            raise Exception(e)