# Scalable Port Scanner


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
    cd workers/
    pip install -r requirements.txt
    ```
    
    - Run it.
    
    ```python
    python main.py
    ```
    

All done.

### Troubleshot:

- If any Redis intance is running in your host computer, worker and dockerized backend may end up connection to different Redis intances.

In this application, a port scanner was developed that can scan computers in a network in a multithreaded and distributed manner. Basically, elements that could create bottlenecks on the application were made multithreaded and mapped efficiently.

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


