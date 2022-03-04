import socket 

# inicializando cliente e conectando ao servidor desejado
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientsocket.connect(('127.0.0.1', 8280))

while True:
    buf = clientsocket.recv(512)
    if len(buf) > 0:
        print(str(buf))
        