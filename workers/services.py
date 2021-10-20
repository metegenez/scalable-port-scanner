from elasticsearch import Elasticsearch, helpers, ElasticsearchException
from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide
import redis
from datetime import datetime


class Connector():
    def __init__(self) -> None:
        pass


class RedisMBConnector(Connector):
    def __init__(self, redis: redis.Redis = Provide["redis"]):
        super().__init__()
        self.r = redis

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
    def __init__(self, elastic: Elasticsearch = Provide["es"]):
        super().__init__()
        self.es = elastic

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