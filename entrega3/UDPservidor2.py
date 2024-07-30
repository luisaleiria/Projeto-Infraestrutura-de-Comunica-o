import socket as skt
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor

MAX_BUFFER = 1024  # tamanho máximo dos dados
ADDR_BIND = ('localhost', 7070)  # endereço e porta do servidor
LOSS_PROBABILITY = 0.0  # probabilidade de perda de pacote


class RDT:
    def __init__(self, socket, max_buffer):
        self.socket = socket
        self.max_buffer = max_buffer
        self.seq_num = 0  # número de sequência inicial

    def send(self, addr, msg):
        # Simula a perda de pacotes com a probabilidade definida na parte de cima do código
        if random.random() < LOSS_PROBABILITY:
            # print(f"Simulando perda de pacote seq_num: {self.seq_num}")
            return  # Simula a perda do pacote, enviando nada

        # Cria um pacote com o número de sequência e mensagem
        time.sleep(0.1)
        packet = f"{self.seq_num}|".encode('utf-8') + msg
        self.socket.sendto(packet, addr)  # envia o pacote
        print(f"Enviado pacote seq_num: {self.seq_num}")
        self.seq_num = 1 - self.seq_num  # alterna entre 0 e 1

    def receive(self):
        while True:
            data, addr = self.socket.recvfrom(self.max_buffer)  # recebe os dados
            if b'|' not in data:
                continue  # ignora os pacotes que foram mal formados
            header, msg = data.split(b'|', 1)  # separa o cabeçalho da mensagem em si
            recv_seq_num = int(header.decode('utf-8'))  # decodifica a sequência
            if recv_seq_num == self.seq_num:
                # envia o ACK confirmando o recebimento
                time.sleep(0.1)
                self.socket.sendto(f"ACK{recv_seq_num}".encode('utf-8'), addr)
                # print(f"Envia ACK pacote num {recv_seq_num}")
                self.seq_num = 1 - self.seq_num  # alterna o número de sequência
                return msg, addr  # retorna a mensagem e o endereço pro servidor


class Servidor:
    def __init__(self, sckt_family, sckt_type, sckt_binding, max_buffer):
        self.sckt = skt.socket(sckt_family, sckt_type)  # cria o socket
        self.sckt.bind(sckt_binding)  # vincula o socket ao endereço dado
        self.rdt = RDT(self.sckt, max_buffer)  # cria uma instância do RDT
        self.users = {}  # cria uma instância dos usuários
        self.accommodations = {}  # cria uma instância das acomodações
        self.reservations = {}  # cria uma instância das reservas
        self.send_count = 0

    def handle_client(self, msg, client_addr):
        # Lida com as mensagens do cliente
        print("Entrou na função do switch")
        msg = msg.decode('utf-8')
        parts = msg.split()
        print(f"Mensagem recebida de {client_addr}: {msg}")
        print(f"parts é {parts[0]}")

        # Switch case para entrada nos comandos certos
        if parts[0] == "login":
            print("Entrou no login do switch")
            self.login(msg, client_addr)
        elif parts[0] == "logout":
            self.logout(client_addr)
        elif parts[0] == "create":
            self.create_accommodation(msg, client_addr)
        elif parts[0] == "list:myacmd":
            self.list_my_accommodations(client_addr)
        elif parts[0] == "list:acmd":
            self.list_accommodations(client_addr)
        elif parts[0] == "list:myrsv":
            self.list_my_reservations(client_addr)
        elif parts[0] == "book":
            self.book_accommodation(msg, client_addr)
        elif parts[0] == "cancel":
            self.cancel_reservation(msg, client_addr)
        else:
            print("Comando desconhecido:", parts[0])
        if self.send_count % 2 == 0:
            self.rdt.seq_num = 1 - self.rdt.seq_num
        self.send_count = 0

    def login(self, msg, addr):
        print("Entrou no login do servidor")
        _, username = msg.split()  # Divide a mensagem recebida, login primeiro e nome de usuário depois
        if username in self.users.values():  # Verifica se o nome de usuário já existe
            self.rdt.send(addr, b"Nome de usuario ja esta em uso.")
            self.send_count += 1
        else:  # Se não adiciona adiciona o endereço e nome do cliente na lista de usuários
            self.users[addr] = username
            self.rdt.send(addr, b"Voce esta online!")  # mensagem de 
            self.send_count += 1
            print(f"{username} logou com sucesso em {addr}")
            print(f"lista de usuarios: {self.users}")

    def logout(self, addr):
        if addr in self.users:  # Verifica se está nos usuários ativos
            username = self.users.pop(addr)  # remove da lista de usuários ativos
            self.rdt.send(addr, b"Logout bem-sucedido.")  # mensagem de confirmação
            self.send_count += 1
            print(f"{username} deslogou de {addr}")

    def create_accommodation(self, msg, addr):
        parts = msg.split()  # Divide a mensagem recebida, cada parte é separada por espaços
        if len(parts) < 4:  # Verifica se tem tudo que precisa pra criar
            self.rdt.send(addr, b"Argumentos insuficientes para criar acomodacao.")
            self.send_count += 1
            return

        # Atribui as partes da mensagem às variáveis da acomodação
        _, name, location, description = parts[0], parts[1], parts[2], ' '.join(parts[3:])
        user = self.users[addr]  # pega o número de usuário de quem está criando a acomodação
        key = (name, location)  # cria uma chave de identificação usando a tupla de nome e localização
        if key in self.accommodations:  # verifica se a acomodação existe
            self.rdt.send(addr, b"Acomodacao ja existe.")  # se existir, avisa ao cliente que tentou
            self.send_count += 1
        else:
            self.accommodations[key] = {  # se não existir, cria a nova
                'owner': user,  # usuário
                'location': location,  # localização
                'description': description,  # descrição
                'availability': [f"{i:02d}/07/2024" for i in range(17, 23)]  # dias disponíveis
            }
            print(f"acomodacao criada {self.accommodations[key]}")
            self.rdt.send(addr, f"Acomodação {name} criada com sucesso!".encode('utf-8'))  # Envia uma mensagem dizendo que criou
            self.send_count += 1
            self.notify_all_users(f"{user} criou a acomodação {name} em {location}.", exclude_addr=addr)  # Notifica para todos os usuários que uma acomodação foi criada

    def list_my_accommodations(self, addr):
        user = self.users[addr]  # pegar o nome do usuário desse endereço

        # Cria lista das acomodações que o usuário tem
        user_accommodations = [f"{name} em {loc}: {data}" for (name, loc), data in self.accommodations.items() if data['owner'] == user]
        # Converte em uma única string e envia para o cliente
        self.rdt.send(addr, '\n'.join(user_accommodations).encode('utf-8'))
        self.send_count += 1

    def list_accommodations(self, addr):
        # Cria uma lista com todas as acomodações disponíveis e suas informações
        all_accommodations = [f"{name} em {loc}: {data}" for (name, loc), data in self.accommodations.items()]
        # Converte em uma única string e envia para o cliente
        self.rdt.send(addr, '\n'.join(all_accommodations).encode('utf-8'))
        self.send_count += 1

    def list_my_reservations(self, addr):
        # Pegar o nome do usuário do endereço do cliente
        # Cria uma lista de reservas feita pelo usuário
        user = self.users[addr]
        user_reservations = [f"Reservado {name} em {loc} no dia {day}" for (name, loc, day), res in self.reservations.items() if res['user'] == user]
        # Converte em uma única string e envia para o cliente
        self.rdt.send(addr, '\n'.join(user_reservations).encode('utf-8'))
        self.send_count += 1

    def book_accommodation(self, msg, addr):
        parts = msg.split()  # Divide a mensagem em partes
        if len(parts) < 5:
            self.rdt.send(addr, b"Argumentos insuficientes para reservar acomodacao.")  # envia uma mensagem de erro se não mandou todas as partes
            self.send_count += 1
            return  # não continua na reserva
        _, owner, name, location, day = parts  # Só reserva um dia por vez
        key = (name, location)  # cria chave
        if key not in self.accommodations:  # Vê se a acomodação existe
            self.rdt.send(addr, b"Acomodacao nao encontrada.")  # se não existir, avisa ao cliente
            self.send_count += 1
            return  # não continua na reserva
        if day not in self.accommodations[key]['availability']:  # Vê se o dia está disponível
            self.rdt.send(addr, b"Dia indisponivel.")  # se não estiver, avisa ao cliente
            self.send_count += 1
            return
        user = self.users[addr]
        if self.accommodations[key]['owner'] == user:  # vê se o proprietário está tentando alugar para si mesmo
            self.rdt.send(addr, b"Voce nao pode reservar sua propria acomodacao.")
            self.send_count += 1
            return
        self.accommodations[key]['availability'].remove(day)  # remove o dia dos dias disponíveis
        self.reservations[(name, location, day)] = {'user': user, 'owner': owner}  # Adiciona as reservas
        self.rdt.send(addr, f"Reserva confirmada: {name} em {location} no dia {day}".encode('utf-8'))
        self.send_count += 1
        self.notify_user(owner, f"{user} reservou sua acomodação {name} em {location} no dia {day}")
        self.send_count += 1

    def cancel_reservation(self, msg, addr):
        parts = msg.split()
        if len(parts) < 4:
            self.rdt.send(addr, b"Argumentos insuficientes para cancelar reserva.")
            self.send_count += 1
            return
        _, owner, name, location, day = parts
        key = (name, location, day)
        if key not in self.reservations:
            self.rdt.send(addr, b"Reserva nao encontrada.")
            self.send_count += 1
            return
        user = self.users[addr]
        if self.reservations[key]['user'] != user:
            self.rdt.send(addr, b"Voce nao pode cancelar uma reserva que nao fez.")
            self.send_count += 1
            return
        self.accommodations[(name, location)]['availability'].append(day)
        self.reservations.pop(key)
        self.rdt.send(addr, f"Reserva cancelada: {name} em {location} no dia {day}".encode('utf-8'))
        self.send_count += 1
        self.notify_user(owner, f"{user} cancelou a reserva da sua acomodação {name} em {location} no dia {day}")
        self.send_count += 1
        self.notify_all_users(f"Acomodação {name} em {location} agora está disponível no dia {day}", exclude_addr=addr)

    def notify_user(self, user, message):
        for addr, username in self.users.items():
            if username == user:
                self.rdt.send(addr, message.encode('utf-8'))
                break

    def notify_all_users(self, message, exclude_addr=None):
        for addr in self.users:
            if addr != exclude_addr:
                self.send_count += 1
                self.rdt.send(addr, message.encode('utf-8'))


def main_servidor():
    server = Servidor(skt.AF_INET, skt.SOCK_DGRAM, ADDR_BIND, MAX_BUFFER)
    print(f"Servidor escutando em {ADDR_BIND}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        try:
            while True:
                msg, client_addr = server.rdt.receive()
                executor.submit(server.handle_client, msg, client_addr)
        except KeyboardInterrupt:
            print("Encerrando o servidor...")


if __name__ == "__main__":
    main_servidor()
