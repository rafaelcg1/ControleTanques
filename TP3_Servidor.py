import sys
import os
import socket
import threading
import time
from math import sqrt, pi, sin
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt



vazao1max = 100 #Valor máximo de vazão no tanque 1
vazao2max = 40 #Valor máximo de vazão no tanque 2
vazaomin = 0 #Valor mínimo de vazão para ambos os tanques

global H1MAX, H2MAX, H1REF, H2REF
H1REF = 8.0
H2REF = 6.0

EXECUTION_TIME = 120 #Exemplo de tempo de execução do programa (neste caso foi definido por 120s)

def interface (lock):  
    global H1REF, H2REF
    t = tini
    while (t < tini + EXECUTION_TIME):
        t = time.time()
        print ("Deseja escolher uma ou as duas referências?")
        num_ref = int(input("Digite 1 para escolher H1, 2 para escolher H2 e 3 para escolher ambas: \n")) #Recebe qual tipo de alteração o usuario deseja fazer
        if (num_ref == 1):
            H1REF = float (input("Entre com novo valor para referencia de H1: \n")) #Altera o valor da referencia de h1
        elif (num_ref == 2):
            H2REF = float (input("Entre com novo valor para referencia de H2:\n")) #Altera o valor da referencia de h2
        elif (num_ref == 3):
            H1REF = float (input("Entre com novo valor para referencia de H1: \n")) #Altera o valor da referencia de h1
            H2REF = float (input("Entre com novo valor para referencia de H2: \n")) #Altera o valor da referencia de h2
        time.sleep(0.1)

def h_tanque1 (t, h1):
    global entrada_tq1, entrada_tq2
    gama1 = 20 #Coeficiente de descarga
    r1 = 2 #Valor do raio 1 menor
    R1 = 10 #Valor do raio 1 maior
    H1 = 20 #Altura do tanque 1
    h1 = 0 if h1 < 0 else h1
    dh1 = (entrada_tq1 - gama1*sqrt(h1) - entrada_tq2) / (pi*(r1 + ((R1 - r1)/ H1) * h1)**2) #Realizando o cálculo da eq diferencial
    return (dh1)

def h_tanque2 (t, h2):
    global entrada_tq2
    gama2 = 10 #Coeficiente de descarga
    r2 = 1 #Valor do raio 1 menor
    R2 = 5 #Valor do raio 2 maior
    H2 = 10 #Altura do tanque 1
    h2 = 0 if h2 < 0 else h2
    dh2 = (entrada_tq2 - gama2*sqrt(h2)) / (pi*(r2 + ((R2 - r2)/ H2) * h2)**2) #Realizando o cálculo da eq diferencial
    return (dh2)

tini = time.time() #Definindo um tempo inicial
h1 = 0
h1_hist = [] #Criação de um histórico para salvar os valores de h1
h1_hist.append(h1) 
t1 = tini #Atribui o tempo inicial a t1


h2 = 0
h2_hist = [] #Criação de um histórico para salvar os valores de h2
h2_hist.append(h2) 
t2 = tini #Atribui o tempo inicial a t2

entrada_tq1 = vazao1max #Entrada do tanque 1 inicia com vazão 1 máxima
entrada_tq2 = vazaomin #Entrada do tanque 2 inicia com vazão mínima

def tanque(num_tanque, lock): 
    global h1, h2, t1, t2
    t = tini
    while (t < tini + EXECUTION_TIME):
        t = time.time()
        if (num_tanque == 1): #Caso seja enviado o parâmetro 1 é realizado o processo para o tanque 1
            lock.acquire()
            sol1 = solve_ivp(h_tanque1, [t1, t], [h1]) #Aplicação do método runge kutta
            t1 = t
            h1 = sol1.y[0][-1]
            h1_hist.append(h1)
            lock.release()

        if (num_tanque == 2): #Caso seja enviado o parâmetro 2 é realizado o processo para o tanque 2
            lock.acquire()
            sol2 = solve_ivp(h_tanque2, [t2, t], [h2]) #Aplicação do método runge kutta
            t2 = t
            h2 = sol2.y[0][-1]
            h2_hist.append(h2)
            lock.release()

        time.sleep(0.1)

def controlador(lock):
    global h1, h2, entrada_tq1, entrada_tq2, vazao1max, vazao2max, vazaomin
    t = tini
    #Controle ON/OFF:
    while (t < tini + EXECUTION_TIME):
        t = time.time()
        lock.acquire()
        H1MAX = 0.5*sin(0.5*t)+ H1REF #Aplicando a senoide em torno da altura referência do tanque 1
        if (h1>H1MAX):
            entrada_tq1 = vazaomin
        else:
            entrada_tq1 = vazao1max

        H2MAX = 0.5*sin(0.5*t)+ H2REF #Aplicando a senoide em torno da altura referência do tanque 2
        if (h2>H2MAX):
            entrada_tq2 = vazaomin
        else:
            entrada_tq2 = vazao2max
        lock.release()
       
        time.sleep(0.2)

def imprime_dados(lock):
    global h1, h2, entrada_tq1, entrada_tq2
    file = open("log.txt","w") #Cria e abre um arquivo de escrita
    file.write(f"h1\t|h2\t|q1i\t|q2i\t|timestamp\n") #Escreve no arquivo os títulos da tabela
    t = tini
    while (t < tini + EXECUTION_TIME):
        t = time.time()
        lock.acquire()
        file.write(f"{h1:.2f}\t|{h2:.2f}\t|{entrada_tq1}\t|{entrada_tq2}\t|{t}\n") #Escreve o valor atual de h1, h2, q1i e q2i
        lock.release()
        time.sleep(1)
    file.close() #Fecha o arquivo

def sinotico(lock):
    global h1, h2, entrada_tq1, entrada_tq2
    t = tini
    
    # inicializando servidor e configurando para esperar conexoes
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.bind(('127.0.0.1', 8280))
    serversocket.listen(5)
    connection, address = serversocket.accept()

    while (t < tini + EXECUTION_TIME):
        # envia informacoes do processo para o arquivo cliente
        connection.send(bytes(f"{h1:.2f}     |{h2:.2f}     |{entrada_tq1}     |{entrada_tq2}     |{t}", 'UTF-8'))
        time.sleep(1)

#Função principal
lock = threading.Lock()

process_thread1 = threading.Thread(target = tanque, args = (1, lock,))
process_thread2 = threading.Thread(target = tanque, args = (2, lock,))
interface_thread = threading.Thread(target= interface, args = (lock,), daemon=True)
softPLC_thread = threading.Thread(target= controlador, args = (lock,))
logger_thread = threading.Thread(target= imprime_dados, args = (lock,))
synoptic_process = threading.Thread (target = sinotico, args = (lock,), daemon = True)

process_thread1.start()
process_thread2.start()
interface_thread.start()
softPLC_thread.start()
logger_thread.start()
synoptic_process.start()

threads = []
threads.append(process_thread1)
threads.append(process_thread2)
threads.append(softPLC_thread)
threads.append(logger_thread)

#Join em todas as threads
for y in threads:
    y.join()

print("Fim do processo")

#Simulação gráfica do processo
plt.style.use('seaborn-whitegrid')
plt.plot(h1_hist, label="Tanque 1")
plt.plot(h2_hist, label="Tanque 2")
plt.legend()
plt.show()
