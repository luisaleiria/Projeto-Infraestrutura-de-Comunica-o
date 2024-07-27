import socket as skt
import os
import time
import random
import threading

MAX_BUFFER = 1024  # tamanho máximo dos dados
ADDR_BIND = ('localhost', 7070)  # endereço e porta do servidor
LOSS_PROBABILITY = 0.3  # probabilidade de perda de pacote


class RDT:
    def __init__(self, socket, max_buffer):
        self.socket = socket
        self.max_buffer = max_buffer
        self.seq_num = 0 # número de sequencia inicial

    def send(self, addr, msg):
        #simula a perda de pacotes com a probabilidade definida na parte de cima do codigo
        if random.random() < LOSS_PROBABILITY:
            print(f"Simulando perda de pacote seq_num: {self.seq_num}")
            return  # Simula a perda do pacote, enviando nada
        
        # Cria um pacote com o numero de sequencia e mensagem
        packet = f"{self.seq_num}|".encode('utf-8') + msg
        self.socket.sendto(packet, addr) #envia o pacote
        print(f"Enviado pacote seq_num: {self.seq_num}")
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
                print(f"Envia ACK pacote num {recv_seq_num}")
                self.seq_num = 1 - self.seq_num #alterna o num de seq
                return msg, addr # retorna a mensagem e o endereço pro servidor



class Servidor:
    def __init__(self, sckt_family, sckt_type, sckt_binding, max_buffer):
        self.sckt = skt.socket(sckt_family, sckt_type) #cria o socket
        self.sckt.bind(sckt_binding) # vincula o socket ao endereço dado
        self.rdt = RDT(self.sckt, max_buffer) #cria uma instancia do rdt
        self.users = {} # cria uma instancia do usuario
        self.accommodations = {} # cria uma instancia da acomodação
        self.reservations = {} # cria uma instancia da reserva

    def handle_client(self, addr):
         # Loop para lidar com as mensagens do cliente
        while True:
            msg, client_addr = self.rdt.receive()
            if client_addr != addr:  # Verifica se a mensagem veio do endereço do cliente certo
                continue # Se não, ignora a mensagem e continua o loop
            msg = msg.decode('utf-8').strip()  # Decodifica a mensagem recebida de bytes para string e remove espaços em branco
            print(f"Mensagem recebida de {client_addr}: {msg}")
            
            #Switch case para entrada nos comandos certos
            if msg.startswith("login"):
                self.login(msg, client_addr)
            elif msg == "logout":
                self.logout(client_addr)
            elif msg.startswith("create"):
                self.create_accommodation(msg, client_addr)
            elif msg == "list:myacmd":
                self.list_my_accommodations(client_addr)
            elif msg == "list:acmd":
                self.list_accommodations(client_addr)
            elif msg == "list:myrsv":
                self.list_my_reservations(client_addr)
            elif msg.startswith("book"):
                self.book_accommodation(msg, client_addr)
            elif msg.startswith("cancel"):
                self.cancel_reservation(msg, client_addr)

    def login(self, msg, addr):
        _, username = msg.split() # Divide a mensagem recebida, login primeiro e nome de usuário dps
        if username in self.users.values():  # Verifica se o nome de usuário já existe
            self.rdt.send(addr, b"Nome de usuario ja esta em uso.")
        else: #Se não adiciona adiciona o endereço e nome do cliente na lista de usuários
            self.users[addr] = username
            self.rdt.send(addr, b"Voce esta online!") #menagem de confirmação
            print(f"{username} logou com sucesso em {addr}")
            
    def logout(self, addr):
        if addr in self.users: #Verifica se está nos usuários ativos
            username = self.users.pop(addr) #remove da lista de usuários ativos
            self.rdt.send(addr, b"Logout bem-sucedido.") #mensagem de confirmação
            print(f"{username} deslogou de {addr}")
            
    def create_accommodation(self, msg, addr):
        parts = msg.split() #Divide a msg recebida, cada parte é separada por espaços
        if len(parts) < 4: #Verifica se tem tudo que precisa pra criar
            self.rdt.send(addr, b"Argumentos insuficientes para criar acomodacao.")
            return
        
        #Atribui as partes da mensagem as variáveis da acomodação
        _, name, location, description = parts[0], parts[1], parts[2], ' '.join(parts[3:])
        user = self.users[addr] #pega o número de usuario de quem ta criado a acomodação
        key = (name, location) #cria uma chave de identificação usando a tupla de nome e localização
        if key in self.accommodations: #verifica se a acom
            self.rdt.send(addr, b"Acomodacao ja existe.")
        else:
            self.accommodations[key] = {
                'owner': user,
                'location': location,
                'description': description,
                'availability': [f"{i:02d}/07/2024" for i in range(17, 23)]
            }
            self.rdt.send(addr, f"Acomodação {name} criada com sucesso!".encode('utf-8'))
            self.notify_all_users(f"{user} criou a acomodação {name} em {location}.")


def main_servidor():
    server = Servidor(skt.AF_INET, skt.SOCK_DGRAM, ADDR_BIND, MAX_BUFFER) #cria uma instancia do servidor
    print(f"Server está escutando no {ADDR_BIND}")

    while True:
        filename, client_address = server.receive_file() #recebe um arquivo
        server.rdt.send(client_address, filename.encode('utf-8')) #envia o nome do arquivo
        server.send_file(client_address, filename) #envia o arquivo renomeado de volta pro cliente
        time.sleep(0.1)
        os.remove(filename) #remove o arquivo depois de enviar


if __name__ == "__main__":
    main_servidor() #inicia o servidor
