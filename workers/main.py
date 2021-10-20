import sys
from dependency_injector.wiring import inject, Provide
from ScanWorker import ScanWorker
from containers import Container


@inject
def main(scan_worker: ScanWorker = Provide[Container.scan_worker],) -> None:
    scan_worker.start()


if __name__ == '__main__':
    container = Container()
    container.init_resources()
    container.config.from_ini('config.ini')
    container.wire(modules=[sys.modules[__name__]])
    main()
