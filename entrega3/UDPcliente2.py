import socket as skt
import os
import time
import random

MAX_BUFFER = 1024  # tamanho máximo dos dados
ADDR_BIND = ('localhost', 8080)  # endereço e porta do cliente
ADDR_TARGET = ('127.0.0.1', 7070)  # endereço e porta do servidor

LOSS_PROBABILITY = 0.3  # probabilidade de perda de pacote


class RDT:
    def __init__(self, socket, max_buffer):
        self.socket = socket
        self.max_buffer = max_buffer
        self.seq_num = 0 # numero de sequencia inicial

    def send(self, addr, msg):
         #simula a perda de pacotes com a probabilidade definida na parte de cima do codigo
        print("entrou RDT")
        #if random.random() < LOSS_PROBABILITY:
        #    print(f"Simulando perda de pacote seq_num: {self.seq_num}")
        #    return  # Simula a perda do pacote

        # Cria um pacote com o numero de sequencia e mensagem
        packet = f"{self.seq_num}|".encode('utf-8') + msg
        self.socket.sendto(packet, addr)
        #print(f"Enviado pacote seq_num: {self.seq_num}")
        self.seq_num = 1 - self.seq_num  # alterna entre 0 e 1

    def receive(self):
        while True:
            data, addr = self.socket.recvfrom(self.max_buffer) #recebe os dados
            if b'|' not in data:
                continue #ignora os pacotes que foram mal formados
            header, msg = data.split(b'|', 1) #separa o cabeçalho da mensagem em si
            recv_seq_num = int(header.decode('utf-8')) #decodifica a sequencia
            if recv_seq_num == self.seq_num:
                #envia o ACK confirmando o recebimento
                self.socket.sendto(f"ACK{recv_seq_num}".encode('utf-8'), addr)
                print(f"Recebido e confirmado pacote seq_num: {recv_seq_num}")
                self.seq_num = 1 - self.seq_num #alterna o num de seq
                return msg, addr # retorna a mensagem e o endereço pro servidor




class Cliente:
    def __init__(self, sckt_family, sckt_type, sckt_binding, max_buffer):
        self.sckt = skt.socket(sckt_family, sckt_type) #cria o socket
        self.sckt.bind(sckt_binding) #vincula o socket ao endereço dado
        self.rdt = RDT(self.sckt, max_buffer) #cria uma instancia de RDT
        self.server_addr = ADDR_TARGET

    def login(self, username):
        print("ta em login")
        self.rdt.send(self.server_addr, f"login {username}".encode('utf-8'))
        msg, _ = self.rdt.receive()
        print(msg.decode('utf-8'))

    def logout(self):
        self.rdt.send(self.server_addr, b"logout")
        msg, _ = self.rdt.receive()
        print(msg.decode('utf-8'))

    def create_accommodation(self, name, location, description):
        self.rdt.send(self.server_addr, f"create {name} {location} {description}".encode('utf-8'))
        msg, _ = self.rdt.receive()
        print(msg.decode('utf-8'))

    def list_my_accommodations(self):
        self.rdt.send(self.server_addr, b"list:myacmd")
        msg, _ = self.rdt.receive()
        print(msg.decode('utf-8'))

    def list_accommodations(self):
        self.rdt.send(self.server_addr, b"list:acmd")
        msg, _ = self.rdt.receive()
        print(msg.decode('utf-8'))

    def list_my_reservations(self):
        self.rdt.send(self.server_addr, b"list:myrsv")
        msg, _ = self.rdt.receive()
        print(msg.decode('utf-8'))

    def book_accommodation(self, owner, name, location, day):
        self.rdt.send(self.server_addr, f"book {owner} {name} {location} {day}".encode('utf-8'))
        msg, _ = self.rdt.receive()
        print(msg.decode('utf-8'))

    def cancel_reservation(self, owner, name, location, day):
        self.rdt.send(self.server_addr, f"cancel {owner} {name} {location} {day}".encode('utf-8'))
        msg, _ = self.rdt.receive()
        print(msg.decode('utf-8'))

def main_cliente():
    client = Cliente(skt.AF_INET, skt.SOCK_DGRAM, ADDR_BIND, MAX_BUFFER)

    while True:
        command = input("> ")
        if command.startswith("login"):
            print("ta no case login")
            _, username = command.split()
            client.login(username)
        elif command == "logout":
            client.logout()
        elif command.startswith("create"):
            _, name, location, *description = command.split()
            client.create_accommodation(name, location, ' '.join(description))
        elif command == "list:myacmd":
            client.list_my_accommodations()
        elif command == "list:acmd":
            client.list_accommodations()
        elif command == "list:myrsv":
            client.list_my_reservations()
        elif command.startswith("book"):
            _, owner, name, location, day = command.split()
            client.book_accommodation(owner, name, location, day)
        elif command.startswith("cancel"):
            _, owner, name, location, day = command.split()
            client.cancel_reservation(owner, name, location, day)

if __name__ == "__main__":
    main_cliente() 