import socket
import sys
import threading
import Queue
import logging
import os
import datetime
import urllib
import traceback
import mimetypes
import time

script_dir = os.path.dirname(os.path.abspath(__file__))


class HTTPServer(object):

    def __init__(self, host=None, port=None, document_root=None, workers=None, thread_timeout = 1):
        if host:
            self.host = host
        else:
            self.host = socket.gethostname().split()[0]
        if port:
            self.port = port
        else:
            self.port = 8080
        if document_root:
            self.root_dir = document_root
        else:
            self.root_dir = script_dir
        if workers:
            self.workers = workers
        else:
            self.workers = 2
        self.mime_type = mimetypes.MimeTypes()
        logging.info('Root directory {document_root}'.format(document_root=self.root_dir))
        self.queue = Queue.Queue()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.thread_timeout = thread_timeout
        for i in range(self.workers):
            thread = threading.Thread(target=self.__proceed_sessions, args=(self.queue,))
            thread.daemon = True
            thread.name = str(i)
            thread.start()
        logging.info('Started {workers} workers'.format(workers=self.workers))
        try:
            logging.info('Startin HTTP-server on {host}:{port}'.format(host=self.host, port=self.port))
            self.socket.bind((self.host, self.port))
        except:
            logging.error('Can not bind to {port}'.format(port=self.port))
            self.shutdown()
            sys.exit(1)

    def start(self):
        self.socket.listen(5)
        print('HTTP server started')
        logging.info('HTTP server started')
        while True:
            (client, address) = self.socket.accept()
            if not client.gettimeout():
                client.settimeout(60)
            logging.info('Recieved connction from {address}'.format(address=address))
            self.queue.put((client, address))

    def shutdown(self):
        try:
            for i in range(self.workers):
                self.queue.put(('quit', 'quit'))
            logging.info('Stoping http server')
            self.socket.close()
        except:
            logging.error('Socket is already down')

    def __proceed_sessions(self, queue):
        packet_size = 1024
        while True:
            try:
                (client, address) = queue.get_nowait()
                if client == 'quit' and address == 'quit':
                    self.queue.task_done()
                    break
                else:
                    buffer = ''
                    while (len(buffer)<4096):
                        data = client.recv(packet_size)
                        logging.debug('Worker {thread} get job {data}'.format(thread=threading.current_thread().name,
                                                                                   data = data))
                        buffer += data
                        if buffer or ('\r\n' in buffer and ' ' in buffer):
                            logging.debug(buffer)
                            break
                    response = self.__make_response(buffer)
                    client.sendall(response)
                    client.close()
                    self.queue.task_done()
            except Queue.Empty:
                pass
            except Exception:
                logging.error(traceback.format_exc())
            finally:
                time.sleep(self.thread_timeout/1000000.0)
        logging.info('Worker {thread} quit'.format(thread=threading.current_thread().name))


    def __generate_headers(self, response_code, file_path = None):
        headers = ''
        if response_code == 200:
            headers += 'HTTP/1.1 200 OK\r\n'
        elif response_code == 404:
            headers += 'HTTP/1.1 404 Not Found\r\n'
        elif response_code == 405:
            headers += 'HTTP/1.1 405 Method Not Allowed\r\n'
        elif response_code == 403:
            headers += 'HTTP/1.1 403 Forbidden\r\n'
        logging.debug('Responce with code {code}'.format(code=response_code))
        date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
        headers += 'Date: {now}\n'.format(now=date)
        headers += 'Server: Otus-HTTP-server\r\n'
        if response_code == 200 and file_path:
            headers += 'Content-Length: {size}\r\n'.format(size=os.path.getsize(file_path))
            content_type = self.mime_type.guess_type(os.path.basename(file_path))[0]
            logging.debug('Responce content type {content}'.format(content=content_type))
            headers += 'Content-Type: {content}\r\n'.format(content=content_type)
        logging.debug('Headers {headers}'.format(headers=headers))
        return headers

    def __make_response(self, data):
        request_method, file_path = self._parse_data(data.decode())
        if not request_method:
            response_code = 405
        elif not file_path:
            response_code = 404
        elif file_path == 'forbidden':
            response_code = 403
        else:
            response_code = 200
        if file_path == 'forbidden':
            file_path = None
        response = self.__generate_headers(response_code, file_path).encode()
        response += '\r\n'
        if request_method != 'HEAD' and response_code == 200:
            with open(file_path, 'rb') as f:
                response += f.read()
        return response

    def _normalize_path(self, file_path):
        if file_path.find(self.root_dir) == -1:
            if file_path.startswith('/'):
                file_path = file_path[1:]
            file_path = os.path.join(self.root_dir, file_path)
            logging.debug('New file path is {file_path}'.format(file_path=file_path))
        file_path = urllib.unquote(file_path)
        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, 'index.html')
            logging.debug('Index file path is {file_path}'.format(file_path=file_path))
        elif '?' in file_path:
            file_path = file_path.split('?')[0]
        if '/../' in file_path:
            file_path = 'forbidden'
        if not os.path.isfile(file_path):
            file_path = None
        return file_path

    def _parse_data(self, data):
        logging.debug('{data}'.format(data=data.split('\r\n')))
        request_method = data.split('\r\n')[0].split(' ')[0]
        try:
            file_path = data.split('\r\n')[0].split(' ')[1]
        except Exception:
            logging.error('Wrong file path in {data}'.format(data=data.split('\r\n')[0]))
            raise Exception
        logging.debug('Request_method {request_method} file path {file_path}'.format(request_method=request_method,
                                                                                     file_path=file_path))
        file_path = self._normalize_path(file_path)
        logging.debug('Result file path is {file_path}'.format(file_path=file_path))
        if request_method not in ('GET', 'HEAD'):
            request_method = None
        return request_method, file_path
