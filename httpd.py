import server
import signal
import sys
import argparse
import logging
import os

script_dir = os.path.dirname(os.path.abspath(__file__))


def quitServer(sig, unused):
    server.shutdown()
    sys.exit(1)

def init_logger():
    log_path = os.path.join(script_dir, 'server.log')
    logging.basicConfig(filename=log_path, level=logging.ERROR,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    logging.info('Loggin is started')

if __name__ == "__main__":
    signal.signal(signal.SIGINT, quitServer)
    init_logger()
    server = server.HTTPServer()
    server.start()
    #parser = argparse.ArgumentParser()
    #parser.add_argument('--port', type=int)
    #parser.add_argument('--document_root')
    #parser.add_argument('--workers', type=int)
    #args = parser.parse_args()
    #server = server.HTTPServer(port=args.port, document_root=args.document_root, workers=args.workers)

