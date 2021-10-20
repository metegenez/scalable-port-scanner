from dependency_injector import containers, providers
from ScanWorker import ScanWorker
import redis
from elasticsearch import Elasticsearch
from PortScanner import PortScanner
from IPPinger import IPPinger
from services import ElasticService, RedisMBConnector
from PortServiceGuesser import PortServiceGuesser
from uuid import uuid4
class Container(containers.DeclarativeContainer):
    """
    Containers are collections of the providers.
    There are several use cases how you can use containers:
        *Keeping all the providers in a single container (most common).

        *Grouping of the providers from the same architectural layer (for example, Services, Models and Forms containers).

        *Grouping of providers from the same functional groups (for example, container Users, that contains all functional parts of the users package).
    """
    config = providers.Configuration()

    # Gateways

    es = providers.Singleton(
        Elasticsearch,
        host=config.host.ip,
    )

    redis = providers.Singleton(
        redis.Redis,
        host=config.host.ip,
        port=6379,
        db=0,
        client_name="worker"+str(uuid4())
    )

    pinger = providers.Factory(
        IPPinger,
    )

    guesser = providers.Factory(
        PortServiceGuesser
    )

    port_scanner = providers.Factory(
        PortScanner
    )

    es_service = providers.Factory(
        ElasticService,
        elastic= es
    )
    redis_service = providers.Factory(
        RedisMBConnector,
        redis= redis
    )

    scan_worker = providers.Factory(
        ScanWorker,
        redis= redis_service,
        elastic= es_service,
        # port_scanner= PortScanner,
        # pinger= IPPinger
    )