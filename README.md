# httpserver
HTTP-сервер, реализованный в рамках домашнего задания. Принимаемые соединения ставятся в очередь, разбираемую пуллом "рабочих"
Сервер принимает на вход следующие параметры:
--host - хост, по умолчанию localhost
--port - порт, на котором стартует http-server, 8080 по умолчанию
--document_root - корневой каталог из которого сервер возвращает файлы, по умолчанию - директория где расположен файл server.py
--workers - колличество "работников", разбирающих очередь
--log_level - уровень логгирования, по умолчанию Error

Пример
python httpd.py --workers=2
Результат нагрузочного тестирования для двух тредов:

Server Software:        Otus-HTTP-server
Server Hostname:        127.0.1.1
Server Port:            8080

Document Path:          /
Document Length:        0 bytes

Concurrency Level:      100
Time taken for tests:   7.562 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      4200000 bytes
HTML transferred:       0 bytes
Requests per second:    6612.30 [#/sec] (mean)
Time per request:       15.123 [ms] (mean)
Time per request:       0.151 [ms] (mean, across all concurrent requests)
Transfer rate:          542.42 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    2  40.7      0    1033
Processing:     3   13   6.9     13     422
Waiting:        3   13   6.9     13     422
Total:          8   15  45.0     13    1452

Percentage of the requests served within a certain time (ms)
  50%     13
  66%     14
  75%     15
  80%     15
  90%     15
  95%     16
  98%     17
  99%     18
 100%   1452 (longest request)
