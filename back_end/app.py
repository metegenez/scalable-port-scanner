import ipaddress
from datetime import datetime
from uuid import uuid4

import redis
from elasticsearch import Elasticsearch, helpers
from flask import Flask, jsonify, request
from flask_cors import CORS

from utils import calculate_ip_addresses

r = redis.Redis(host='redis', port=6379, db=0, client_name="backend")
app = Flask(__name__)
CORS(app)
cors = CORS(app, resource={
    r"/*": {
        "origins": "*"
    }
})
es = Elasticsearch(host="es01")
INDEX_NAME = "scans"

@app.route("/healthcheck", methods=["GET"])
def heathcheck():
    return str(r.ping() and es.ping())

@app.route("/jobs", methods=["POST"])
def enqueue_job():
    ip_range = request.json["ip_range"]
    port_range = request.json["port_range"]
    job_id = str(uuid4())
    time = str(datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'))
    # Create elasticsearch index
    body = {
        "job_id": job_id,
        "start_timestamp": time,
        "finished_timestamp": time,
        "scanned_ip": ip_range,
        "scanned_ports": port_range,
        "status": "Waiting",  # or Finished
        "ip_info": [],
        "ip_port_info": []
    }
    es.index(index=INDEX_NAME, id=job_id, body=body)
    # For workers, put ips into message broker.
    msg_id = str(uuid4())
    r.execute_command("HSET", "messages", msg_id, ip_range +
                      "#" + port_range + "#" + job_id)
    r.execute_command("ZADD", "due", datetime.now().timestamp(), msg_id)
    return job_id


@app.route("/jobs/<string:name>", methods=["GET"])
def job_details(name):
    detail = es.get(index=INDEX_NAME, id=name)
    return {"detail": detail, "ip_addresses": calculate_ip_addresses(detail['_source']["scanned_ip"])}


@app.route("/jobs", methods=["GET"])
def retrieveAllJobs():
    query = {
        "query": {
            "match_all": {}
        }
    }
    scan = helpers.scan(es, index=INDEX_NAME, query=query, scroll='1m')
    return {"all_scans": [temp["_source"] for temp in scan]}


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
