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
            #print(f"Simulando perda de pacote seq_num: {self.seq_num}")
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
                #print(f"Envia ACK pacote num {recv_seq_num}")
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
        print("Entrou na função do switch") 
        while True:
            msg, client_addr = self.rdt.receive()
            print ({msg})
            if client_addr != addr:  # Verifica se a mensagem veio do endereço do cliente certo
                continue # Se não, ignora a mensagem e continua o loop
            msg = msg.decode('utf-8').strip()  # Decodifica a mensagem recebida de bytes para string e remove espaços em branco
            print(f"Mensagem recebida de {client_addr}: {msg}")
            
            #Switch case para entrada nos comandos certos
            if msg =="login":
                print("Entrou no login do switch")
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
        print("Entrou no login do servidor") 
        _, username = msg.split() # Divide a mensagem recebida, login primeiro e nome de usuário dps
        if username in self.users.values():  # Verifica se o nome de usuário já existe
            self.rdt.send(addr, b"Nome de usuario ja esta em uso.")
        else: #Se não adiciona adiciona o endereço e nome do cliente na lista de usuários
            self.users[addr] = username
            self.rdt.send(addr, b"Voce esta online!") #mensagem de confirmação
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
        if key in self.accommodations: #verifica se a acomodação existe 
            self.rdt.send(addr, b"Acomodacao ja existe.") #se existir avisa ao cliente que tentou
        else:
            self.accommodations[key] = {  #se não existir, cria o novo
                'owner': user, #usuario
                'location': location, #localização
                'description': description, #descrição
                'availability': [f"{i:02d}/07/2024" for i in range(17, 23)] #dias disponíveis
            }
            self.rdt.send(addr, f"Acomodação {name} criada com sucesso!".encode('utf-8')) #Envia uma mensagem dizendo que criou
            self.notify_all_users(f"{user} criou a acomodação {name} em {location}.") #Notifica pra todo mundo que uma acomodação foi criada

    def list_my_accommodations(self, addr):
        user = self.users[addr] #pegar o nome do usuário desse endereço
        
        #Cria lista das acomodações que o usuário tem
        user_accommodations = [f"{name} em {loc}: {data}" for (name, loc), data in self.accommodations.items() if data['owner'] == user]
        #Converte em uma única string e envia pro cliente
        self.rdt.send(addr, '\n'.join(user_accommodations).encode('utf-8'))
        
    def list_accommodations(self, addr):
        #Cria uma lista com todas as acomodações disponíveis e suas informações
        all_accommodations = [f"{name} em {loc}: {data}" for (name, loc), data in self.accommodations.items()]
        #Converte em uma única string e envia pro cliente
        self.rdt.send(addr, '\n'.join(all_accommodations).encode('utf-8'))
        
    def list_my_reservations(self, addr):
        #Pegar o nome do usuário do endereço do cliente
        #Cria uma lista de reservas feita pelo usuário
        user = self.users[addr]
        user_reservations = [f"Reservado {name} em {loc} no dia {day}" for (name, loc,day), res  in self.reservations.items() if res['user'] == user]
        #Converte em uma única string e envia pro cliente
        self.rdt.send(addr, '\n'.join(user_reservations).encode('utf-8'))
    
    def book_accommodation(self, msg, addr):
        parts = msg.split() #Divide a mensagem em partes
        if len(parts) < 5: 
            self.rdt.send(addr, b"Argumentos insuficientes para reservar acomodacao.") #envia uma mensagem de erro se não mandou todas as partes
            return #não continua na reserva
        _, owner, name, location, day = parts #Só reserva um dia por vez
        key = (name, location) #cria chave 
        if key not in self.accommodations: #Vê se a acomodação existe
            self.rdt.send(addr, b"Acomodacao nao encontrada.") #se não existir, avisa ao cliente
            return #não continua na  reserva
        if day not in self.accommodations[key]['availability']: #Vê se o dia está disponível
            self.rdt.send(addr, b"Dia indisponivel.") #se não tover avisa ao cliente
            return
        user = self.users[addr]
        if self.accommodations[key]['owner'] == user: #vê se o proprietario ta tentando alugar dele mesmo
            self.rdt.send(addr, b"Voce nao pode reservar sua propria acomodacao.")
            return
        self.accommodations[key]['availability'].remove(day) #remove o dia dos dias disponíveis
        self.reservations[(name, location, day)] = {'user': user, 'owner': owner} #Adiciona as reservas
        self.rdt.send(addr, f"Reserva confirmada: {name} em {location} no dia {day}".encode('utf-8'))
        self.notify_user(owner, f"{user} reservou sua acomodação {name} em {location} no dia {day}")

    def cancel_reservation(self, msg, addr):
        parts = msg.split()
        if len(parts) < 4:
            self.rdt.send(addr, b"Argumentos insuficientes para cancelar reserva.")
            return
        _, owner, name, location, day = parts
        key = (name, location, day)
        if key not in self.reservations:
            self.rdt.send(addr, b"Reserva nao encontrada.")
            return
        user = self.users[addr]
        if self.reservations[key]['user'] != user:
            self.rdt.send(addr, b"Voce nao pode cancelar uma reserva que nao fez.")
            return
        self.accommodations[(name, location)]['availability'].append(day)
        self.reservations.pop(key)
        self.rdt.send(addr, f"Reserva cancelada: {name} em {location} no dia {day}".encode('utf-8'))
        self.notify_user(owner, f"{user} cancelou a reserva da sua acomodação {name} em {location} no dia {day}")
        self.notify_all_users(f"Acomodação {name} em {location} agora está disponível no dia {day}")

    def notify_user(self, user, message):
        for addr, username in self.users.items():
            if username == user:
                self.rdt.send(addr, message.encode('utf-8'))
                break

    def notify_all_users(self, message):
        for addr in self.users:
            self.rdt.send(addr, message.encode('utf-8'))

def main_servidor():
    server = Servidor(skt.AF_INET, skt.SOCK_DGRAM, ADDR_BIND, MAX_BUFFER)
    print(f"Servidor escutando em {ADDR_BIND}")

    while True:
        msg, client_addr = server.rdt.receive()
        threading.Thread(target=server.handle_client, args=(client_addr,)).start()


if __name__ == "__main__":
    main_servidor() #inicia o servidor
