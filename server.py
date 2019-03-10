import socket
import sys
import threading
import Queue
import logging
import os
import datetime
import urllib

script_dir = os.path.dirname(os.path.abspath(__file__))


class HTTPServer(object):

    def __init__(self, port=8080, document_root=script_dir, workers=5):
        self.host = socket.gethostname().split()[0]
        self.port = port
        logging.info('Root directory {document_root}'.format(document_root=document_root))
        self.root_dir = document_root
        self.queue = Queue.Queue()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        for i in range(workers):
            thread = threading.Thread(target=self.__proceed_sessions, args=(self.queue,))
            thread.daemon = True
            thread.name=str(i)
            thread.start()
        logging.info('Started {workers} workers'.format(workers=workers))

    def start(self):
        try:
            logging.info('Startin HTTP-server on {host}:{port}'.format(host=self.host, port=self.port))
            self.socket.bind((self.host, self.port))
        except:
            logging.error('Can not bind to {port}'.format(port=self.port))
            self.shutdown()
            sys.exit(1)
        self._receive_connections()

    def shutdown(self):
        try:
            logging.info('Stoping http server')
            self.socket.close()
        except:
            logging.error('Socket is already down')




    def _receive_connections(self):
        self.socket.listen(5)
        while True:
            (client, address) = self.socket.accept()
            if not client.gettimeout():
                client.settimeout(60)
            logging.info('Recieved connction from {address}'.format(address=address))
            self.queue.put((client, address))

    def __proceed_sessions(self, queue):
        packet_size = 1024
        while True:
            try:
                (client, address) = queue.get()

                data = client.recv(packet_size)
                logging.debug('Worker {thread} get job {data}'.format(thread=threading.current_thread().name,
                                                                                   data = data))
                if not data: continue
                response = self.__make_response(data)
                logging.debug('Worker {thread} response {response}'.format(thread=threading.current_thread().name,
                                                                           response=response))
                client.send(response)
                client.close()
            except Queue.Empty:
                pass

    @staticmethod
    def __generate_headers(response_code, file_size, file_type):
        headers = ''
        if response_code == 200:
            headers += 'HTTP/1.1 200 OK\n'
        elif response_code == 404:
            headers += 'HTTP/1.1 404 Not Found\r\n'
        elif response_code == 405:
            headers += 'HTTP/1.1 405 Method Not Allowed\r\n'
        date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
        headers += 'Date: {now}\n'.format(now=date)
        headers += 'Server: Otus-HTTP-server\r\n'
        if file_size:
            headers += 'Content-Length: {size}\r\n'.format(size=file_size)
            if file_type in ['.html', '.css']:
                content_type = 'text/{type}'.format(type=file_type[1:])
            elif file_type in ['.js', '.swf']:
                content_type = 'application/{type}'.format(type=file_type[1:])
            elif file_type in ['.jpg', '.jpeg', '.png', '.gif', '.swf']:
                if file_type == '.jpg':
                    file_type = '.jpeg'
                content_type = 'image/{type}'.format(type=file_type[1:])
            else:
                content_type = None
            if content_type:
                headers += 'Content-Type: {content}\r\n'.format(content=content_type)
        return headers

    def __make_response(self, data):
        (response_code, file_bytes, file_size, file_type) = self._parse_data(data.decode())
        response = self.__generate_headers(response_code, file_size, file_type).encode()
        if file_bytes:
            response += '\r\n'
            response += file_bytes
        return response

    def _parse_data(self, data):
        logging.debug('{data}'.format(data=data.split('\n')))
        request_method = data.split('\n')[0].split(' ')[0]
        file_path = data.split('\n')[0].split(' ')[1]
        logging.debug('Request_method {request_method} file path {file_path}'.format(request_method=request_method,
                                                                                    file_path=file_path))
        if request_method in ('GET', 'HEAD'):
            if file_path.find(self.root_dir) == -1:
                file_path =self.root_dir + file_path
                logging.debug('New file path is {file_path}'.format(file_path=file_path))
            file_path = urllib.unquote(file_path)
            logging.debug('New file path is {file_path}'.format(file_path=file_path))
            if (not os.path.isfile(file_path)) or (os.path.isdir(file_path) and os.path.isfile(os.path.join(file_path, 'index.html'))):
                logging.info('Client is trying to get file that not exitst {file_path}'.format(file_path=file_path))
                return 403, None, 0, None
            with open(file_path, 'rb') as file:
                file_bytes = file.read()
            file_size = os.path.getsize(file_path)
            if request_method == 'HEAD':
                logging.info('Request method is HEAD')
                return 200, None, file_size, os.path.splitext(file_path)[1]
            else:
                logging.info('Request method is GET')
                return 200, file_bytes, file_size, os.path.splitext(file_path)[1]
        else:
            return 405, '', 0, ''

