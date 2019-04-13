import server
import signal
import sys
import argparse
import logging
import os

script_dir = os.path.dirname(os.path.abspath(__file__))


def quit_server(sig, unused):
    server.shutdown()
    sys.exit(1)


def init_logger(log_level):
    log_path = os.path.join(script_dir, 'server.log')
    if log_level == 'error':
        log_level = logging.ERROR
    elif log_level == 'debug':
        log_level = logging.DEBUG
    elif log_level == 'info':
        log_level = logging.INFO
    logging.basicConfig(filename=log_path, level=log_level,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    logging.info('Loggin is started')


if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit_server)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int)
    parser.add_argument('--document_root')
    parser.add_argument('--workers', type=int)
    parser.add_argument('--host')
    parser.add_argument('--log_level')
    args = parser.parse_args()
    if not args.log_level:
        init_logger('error')
    else:
        init_logger(args.log_level)
    server = server.HTTPServer(host=args.host, port=args.port, document_root=args.document_root, workers=args.workers)
    server.start()
