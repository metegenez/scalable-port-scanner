# Scalable Port Scanner

In this application, a port scanner was developed that can scan computers in a network in a multithreaded and distributed manner. Basically, elements that could create bottlenecks on the application were made multithreaded and mapped efficiently.

# System Design

The requirements of the designed system are that Workers can process different JOB requests on different machines at the same time and index the outputs of these requests in a DB. This means scalable services. Although this scaling is manual, it requires a message queue and services that periodically pool that queue.

![portscanner.png](https://s3.us-west-2.amazonaws.com/secure.notion-static.com/b708ae39-bdf5-4046-83d6-7a13b7da4ae8/portscanner.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45O3KS52Y5%2F20211020%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20211020T000321Z&X-Amz-Expires=86400&X-Amz-Signature=2852fe54a6a8a7674798f1feb04d16a0659edc6ef123c746ccc7f34362dae339&X-Amz-SignedHeaders=host&response-content-disposition=filename%20%3D"portscanner.png")

For this reason, Redis was preferred as a message queue and added to the system. In this way, it is ensured that transactions are queued and consumed by different service replicas.

## Client Side

Here, React framework is preferred. Basically, the frontend functions are to view all the job requests at hand, to create new requests and to see the details of the completed requests.

Internal technologies used for bindings:

- Redux: For async event management
- Redux Saga: Side effect manager

## Backend

We position the backend as a REST API. Python Flask is used for this service. It manages the job queue publishing and job getters. Jinja template engine is not used for web application.

## Message Queue

There are lots of options when it comes to choosing a message queue for our application. We don’t need something as heavyweight as RabbitMQ or Amazon SQS. A popular alternative is to build a queue using Redis. 

### Implementation

A simple implementation will use LPUSH to push messages onto the queue, and **BRPOP** pull them off, respectively. Whilst this is useful for a basic FIFO queue, it does not support delayed messages - pushing a message to be pulled from the queue at a later date. Even if our application does not require a delayed job request feature, it can be asked in future and implementation is selected accordingly. 

We exploited the sorted set feature of Redis. If we associate the message and the timestamp of the message, we can easily fetch the earliest message added in the queue up to a certain timestamp. In detail, a publisher is adding certain message as

```bash
redis> HSET messages <id> <message>
redis> ZADD due <due_timestamp> <id>
```

and a subscriber can fetch it as

```bash
redis> ZRANGEBYSCORE due -inf <current_timestamp> LIMIT 0 1
redis> HGET messages <message_id>
#Delete fetched message
redis> ZREM due <message_id>
redis> HDEL messages <message_id>  
```

Unfortunately, workers cannot get the message if they collapse but it is enough for our needs. Also, each message is a String, so we used a workaround as

```bash
"<ip_range>#<port_range>#<job_id>"
"192.168.32.1/24#0-1000#ff0ece2e-b215-4e5e-8dd8-e3d322ceebcc"
```

## Data Layer

We selected the Elasticsearch  which is a distributed open-source search engine and analytics database which was developed by java on Apache Lucene. It allows to store data, search and analyze a large volume of data within seconds. In this part, I face a couple of issues regarding data strorage. 

### Implementation

In a typical RDBMS, we store data in a form of a table. one row represents one useful piece of information. But in Elasticsearch we save data in the form of JSON string. A JSON string in Elasticsearch is called a document. The JSON field in RDBMS terms is the column and the value itself is the value. 

Our first problem started with mapping the indexed data in Elasticsearch. It has a feature of dynamic mapping, it caused field creation problems due to array of object in our JSON objects. Elasticsearch tries to map the ip_open_ports in a nested manner and couldnot scale due to **"Limit of total fields [1000] in index [test_index] has been exceeded" error.**

```json
{ 
...rest,
"ip_port_info": [
    {
        "192.168.1.1": [
            {
                "desc": "SSH",
                "port": 22,
                "service": "ssh"
            },
            {
                "desc": "Telnet",
                "port": 23,
                "service": "telnet"
            },
            {
                "desc": "Domain Name Server",
                "port": 53,
                "service": "domain"
            },
            {
                "desc": "HTTP",
                "port": 80,
                "service": "http"
            }
        ]
    }, ...rest
]}
```

This is a common warning seen due to what is commonly known as a mapping explosion. Defining too many fields in an index can lead to a mapping explosion, which can cause out of memory errors and difficult situations to recover from. But at the first place, we didnot define anything, still dynamic mapping cannot handle the complexity of our JSON. So, we came up a solution as.

- Setting "dynamic": "false"
- Use a flattened structure to reduce complexity.

and PUT the mapping below immediately after DB creation.

```bash
{
  "scans": {
    "mappings": {
      "dynamic": "false",
      "properties": {
        "finished_timestamp": {
          "type": "date"
        },
        "ip_info": {
          "type": "flattened"
        },
        "ip_port_info": {
          "type": "flattened"
        },
        "job_id": {
          "type": "keyword"
        },
        "scanned_ip": {
          "type": "keyword"
        },
        "scanned_ports": {
          "type": "keyword"
        },
        "start_timestamp": {
          "type": "date"
        },
        "status": {
          "type": "keyword"
        }
      }
    }
  }
}
```

This was our first attempt to use Elasticsearch, still I gives the expected results but search capabilities are decreased dramatically.

# Workers

Workers are designed to be work in a distributed manner. There 3 main steps to scan given IP range and port range. We enabled that each job is executed in different machine, or next to a job finishes. This means, we do not divide the jobs between nodes. This can cause an suboptimal load balancing if jobs are different in size and job count is low. 

![portscanner (1).png](Scalable%20Port%20Scanner%207ce67e5833e9476384a953f2120e8b74/portscanner_(1).png)

### Pooling

This part of work is explained in Message Queue section. 

### Ping IP Range

It calls system "ping" command, returns OS information if ping succeeds or False otherwise. The main functionality is Python 3.5+, Windows and Linux compatible - OS detection is implemented only in Windows currently-. Making this "ping" function threaded is handled in same class. Most of the methods are static, still we used a non-static function to cover all. 

**OS Detection**

You can quickly detect whether a system is running with Linux, or Windows or any other OS by looking at the TTL value from the output of the ping command. You don't need any extra applications to detect a remote system's OS. This is implemented only in Windows.

### Connect Port Range

This part consumes the online IP knowdledge of previous block. This part takes online IP addresses and port ranges, takes product of two list as tuples as

```json
[
('192.168.1.1', 80), 
('192.168.1.1', 8080), 
('192.168.1.2', 80), 
('192.168.1.2', 8080), 
...]
```

and so on. Then, it tries to connect them multihreaded. 

**Service Detection**

Service detection is based on 

```python
socket.getservbyport()
```

 If it cannot detect,  we put most known default port services into account and read it from a file.

# Setup

## Test

To test application locally, we need virtual machines and Docker Desktop (Windows only). 

- Create a Linux/Windows machine with bridge adapter to make VM get IP address from host network.

![Untitled](https://s3.us-west-2.amazonaws.com/secure.notion-static.com/b81a699e-ec9e-41d8-a38b-78bf85de348c/portscanner_%281%29.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45O3KS52Y5%2F20211020%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20211020T000900Z&X-Amz-Expires=86400&X-Amz-Signature=ecb587424dfc351d5c816172e86ac51041c9a30dbcb61a7f14aad2fa4b46715b&X-Amz-SignedHeaders=host&response-content-disposition=filename%20%3D"portscanner%2520%281%29.png")

- If Host (where the Web Application is running) is Windows, disable the Security Firewall. Probably there is a least-priviledged approach here, but for simplicity disable it to ping Host from VM.

## Setup

- Clone the repository. / Download the code.
- Prepare web application.
    - Start the web application.
    
    ```bash
    docker-compose up
    ```
    
    - PUT the mapping in Elasticsearch DB. (There can be done with config files anyway.) Index name is default **"scans".**
    
    ```python
    curl --location --request PUT 'localhost:9200/scans' \
    --header 'Content-Type: application/json' \
    --data-raw '{
      "mappings": {
        "dynamic": false,
        "properties": {
          "start_timestamp": {
            "type": "date"
          },
          "finished_timestamp": {
            "type": "date"
          },
          "job_id": {
            "type": "keyword"
          },
          "scanned_ip": {
            "type": "keyword"
          },
          "status": {
            "type": "keyword"
          },
          "scanned_ports": {
            "type": "keyword"
          },
           "ip_info": {
            "type": "flattened"
          },
          "ip_port_info": {
            "type": "flattened"
          }
        }
      }
    }'
    ```
    
    - Then you can visit localhost:3000.
- Prepare Workers
    - Change the config.ini file in "./workers" subdirectory. Put your host IP address accordingly.
    - Install requirements. (You can use venv also.)
    
    ```python
    pip install -r ./workers/requirements.txt
    ```
    
    - Run it.
    
    ```python
    python ./workers/main.py
    ```
    

All done.

### Troubleshot:

- If any Redis intance is running in your host computer, worker and dockerized backend may end up connection to different Redis intances.
