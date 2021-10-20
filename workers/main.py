import sys
from dependency_injector.wiring import inject, Provide
from ScanWorker import ScanWorker
from containers import Container
from ScanWorker import ScanWorker


def main():
    scan_worker = ScanWorker()
    scan_worker.start()

if __name__ == '__main__':
    main()
