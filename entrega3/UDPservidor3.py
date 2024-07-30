import socket as skt  
import random  
import threading
import time  


MAX_BUFFER = 1024  # Define o tamanho máximo dos dados a serem recebidos pelo socket
ADDR_BIND = ('localhost', 7070)  # Define o endereço e a porta onde o servidor se vinculará
LOSS_PROBABILITY = 0.0  # Define a probabilidade de perda de pacotes (0.0 = sem perda)

# Classe RDT 3.0 (Feita nas etapas anteriores) para gerenciar a transferência confiável de dados
class RDT:
    def __init__(self, socket, max_buffer):
        self.socket = socket  # Armazena o socket para comunicação
        self.max_buffer = max_buffer  # Armazena o tamanho máximo do buffer
        self.seq_num = 0  # Inicializa o número de sequência

    def send(self, addr, msg):
        # Simula a perda de pacotes com a probabilidade definida
        if random.random() < LOSS_PROBABILITY:
            return  # Simula a perda do pacote, não enviando nada

        # Cria um pacote com o número de sequência e a mensagem
        time.sleep(0.1)  # Adiciona um atraso para simulação
        packet = f"{self.seq_num}|".encode('utf-8') + msg
        self.socket.sendto(packet, addr)  # Envia o pacote para o endereço especificado
        self.seq_num = 1 - self.seq_num  # Alterna o número de sequência entre 0 e 1

    def receive(self):
        while True:
            data, addr = self.socket.recvfrom(self.max_buffer)  # Recebe dados do socket
            if b'|' not in data:
                continue  # Ignora pacotes malformados
            header, msg = data.split(b'|', 1)  # Separa o cabeçalho da mensagem
            recv_seq_num = int(header.decode('utf-8'))  # Decodifica o número de sequência
            if recv_seq_num == self.seq_num:
                # Envia um ACK confirmando o recebimento
                time.sleep(0.1)  # Adiciona um atraso para simulação
                self.socket.sendto(f"ACK{recv_seq_num}".encode('utf-8'), addr)
                self.seq_num = 1 - self.seq_num  # Alterna o número de sequência
                return msg, addr  # Retorna a mensagem e o endereço

# Classe Servidor para gerenciar as operações do servidor
class Servidor:
    def __init__(self, sckt_family, sckt_type, sckt_binding, max_buffer):
        self.sckt = skt.socket(sckt_family, sckt_type)  # Cria o socket
        self.sckt.bind(sckt_binding)  # Vincula o socket ao endereço fornecido
        self.rdt = RDT(self.sckt, max_buffer)  # Instancia a classe RDT
        self.users = {}  # Dicionário para armazenar usuários
        self.accommodations = {}  # Dicionário para armazenar acomodações
        self.reservations = {}  # Dicionário para armazenar reservas
        self.send_count = 0  # Contador de envios

    def handle_client(self):
        # Lida com as mensagens do cliente
        msg, client_addr = self.rdt.receive()  # Recebe mensagem do cliente
        # print("Entrou na função do switch")
        msg = msg.decode('utf-8')  # Decodifica a mensagem recebida
        parts = msg.split()  # Divide a mensagem em partes
        print(f"Mensagem recebida de {client_addr}: {msg}")
        print(f"parts é {parts[0]}")

        # Switch case para entrada nos comandos certos
        if parts[0] == "login":
            # print("Entrou no login do switch")
            self.login(msg, client_addr)  # Chama o método login
        elif parts[0] == "logout":
            self.logout(client_addr)  # Chama o método logout
        elif parts[0] == "create":
            self.create_accommodation(msg, client_addr)  # Chama o método create_accommodation
        elif parts[0] == "list:myacmd":
            self.list_my_accommodations(client_addr)  # Chama o método list_my_accommodations
        elif parts[0] == "list:acmd":
            self.list_accommodations(client_addr)  # Chama o método list_accommodations
        elif parts[0] == "list:myrsv":
            self.list_my_reservations(client_addr)  # Chama o método list_my_reservations
        elif parts[0] == "book":
            self.book_accommodation(msg, client_addr)  # Chama o método book_accommodation
        elif parts[0] == "cancel":
            self.cancel_reservation(msg, client_addr)  # Chama o método cancel_reservation
        else:
            print("Comando desconhecido:", parts[0])  # Mensagem para comando desconhecido
        if(self.send_count % 2 == 0):
            self.rdt.send(client_addr, b"")  # Envia pacote vazio para sincronização de ACK
        self.send_count = 0  # Reseta contador de envios

    def login(self, msg, addr):
        _, username = msg.split()  # Divide a mensagem recebida
        if username in self.users.values():  # Verifica se o nome de usuário já existe
            self.rdt.send(addr, b"Nome de usuario ja esta em uso.")
            self.send_count += 1
        else:  # Se não, adiciona o endereço e nome do cliente na lista de usuários
            self.users[addr] = username
            self.rdt.send(addr, b"Voce esta online!")  # Mensagem de confirmação de login
            self.send_count += 1
            print(f"{username} logou com sucesso em {addr}")
            print(f"lista de usuarios: {self.users}")

    def logout(self, addr):
        if addr in self.users:  # Verifica se o endereço está na lista de usuários
            username = self.users.pop(addr)  # Remove o usuário da lista
            self.rdt.send(addr, b"Logout bem-sucedido.")  # Mensagem de confirmação de logout
            self.send_count += 1
            print(f"{username} deslogou de {addr}")

    def create_accommodation(self, msg, addr):
        parts = msg.split()  # Divide a mensagem recebida
        if len(parts) < 4:  # Verifica se há argumentos suficientes
            self.rdt.send(addr, b"Argumentos insuficientes para criar acomodacao.")
            self.send_count += 1
            return

        # Atribui as partes da mensagem às variáveis da acomodação
        _, name, location, description = parts[0], parts[1], parts[2], ' '.join(parts[3:])
        user = self.users[addr]  # Pega o nome do usuário que está criando a acomodação
        key = (name, location)  # Cria uma chave única para a acomodação
        if key in self.accommodations:  # Verifica se a acomodação já existe
            self.rdt.send(addr, b"Acomodacao ja existe.")  # Mensagem de erro
            self.send_count += 1
        else:
            self.accommodations[key] = {  # Adiciona a nova acomodação
                'owner': user,
                'location': location,
                'description': description,
                'availability': [f"{i:02d}/07/2024" for i in range(17, 23)]  # Dias disponíveis
            }
            print(f"acomodacao criada {self.accommodations[key]}")
            self.rdt.send(addr, f"Acomodação {name} criada com sucesso!".encode('utf-8'))  # Mensagem de sucesso
            self.send_count += 1
            self.notify_all_users(f"{user} criou a acomodação {name} em {location}.", exclude_addr=addr)  # Notifica todos os usuários

    def list_my_accommodations(self, addr):
        user = self.users[addr]  # Pega o nome do usuário

        # Cria uma lista das acomodações do usuário
        user_accommodations = [f"{name} em {loc}: {data}" for (name, loc), data in self.accommodations.items() if data['owner'] == user]
        # Converte a lista em uma string e envia para o cliente
        self.rdt.send(addr, '\n'.join(user_accommodations).encode('utf-8'))
        self.send_count += 1

    def list_accommodations(self, addr):
        # Cria uma lista com todas as acomodações disponíveis
        all_accommodations = [f"{name} em {loc}: {data}" for (name, loc), data in self.accommodations.items()]
        # Converte a lista em uma string e envia para o cliente
        self.rdt.send(addr, '\n'.join(all_accommodations).encode('utf-8'))
        self.send_count += 1

    def list_my_reservations(self, addr):
        # Pega o nome do usuário
        user = self.users[addr]
        # Cria uma lista de reservas feitas pelo usuário
        user_reservations = [f"Reservado {name} em {loc} no dia {day}" for (name, loc, day), res in self.reservations.items() if res['user'] == user]
        # Converte a lista em uma string e envia para o cliente
        self.rdt.send(addr, '\n'.join(user_reservations).encode('utf-8'))
        self.send_count += 1

    def book_accommodation(self, msg, addr):
        parts = msg.split()  # Divide a mensagem em partes
        if len(parts) < 5:
            self.rdt.send(addr, b"Argumentos insuficientes para reservar acomodacao.")  # Mensagem de erro
            self.send_count += 1
            return  # Não continua na reserva
        _, owner, name, location, day = parts  # Atribui as partes da mensagem às variáveis
        key = (name, location)  # Cria chave única para a acomodação
        if key not in self.accommodations:  # Verifica se a acomodação existe
            self.rdt.send(addr, b"Acomodacao nao encontrada.")  # Mensagem de erro
            self.send_count += 1
            return  # Não continua na reserva
        if day not in self.accommodations[key]['availability']:  # Verifica se o dia está disponível
            self.rdt.send(addr, b"Dia indisponivel.")  # Mensagem de erro
            self.send_count += 1
            return
        user = self.users[addr]
        if self.accommodations[key]['owner'] == user:  # Verifica se o proprietário está tentando reservar para si mesmo
            self.rdt.send(addr, b"Voce nao pode reservar sua propria acomodacao.")
            self.send_count += 1
            return
        self.accommodations[key]['availability'].remove(day)  # Remove o dia da disponibilidade
        self.reservations[(name, location, day)] = {'user': user, 'owner': owner}  # Adiciona a reserva
        self.rdt.send(addr, f"Reserva confirmada: {name} em {location} no dia {day}".encode('utf-8'))  # Mensagem de confirmação
        self.send_count += 1
        self.notify_user(owner, f"{user} reservou sua acomodação {name} em {location} no dia {day}")
        self.send_count += 1

    def cancel_reservation(self, msg, addr):
        parts = msg.split()
        if len(parts) < 4: # Verifica se há a quantidade necessária de argumentos
            self.rdt.send(addr, b"Argumentos insuficientes para cancelar reserva.")
            self.send_count += 1
            return # Se não houver retorna um erro
        _, owner, name, location, day = parts
        key = (name, location, day)
        if key not in self.reservations: # Verifica se a reserva existe
            self.rdt.send(addr, b"Reserva nao encontrada.") # Se ela não existir, envia um erro 
            self.send_count += 1
            return
        user = self.users[addr]
        if self.reservations[key]['user'] != user: # Verifica se o usuário que quer cancelar a reserva é o mesmo que fez a reserva
            self.rdt.send(addr, b"Voce nao pode cancelar uma reserva que nao fez.") # Se não for, retorna um erro
            self.send_count += 1
            return
        self.accommodations[(name, location)]['availability'].append(day)  # Adiciona o dia de volta à disponibilidade
        self.reservations.pop(key)  # Remove a reserva
        self.rdt.send(addr, f"Reserva cancelada: {name} em {location} no dia {day}".encode('utf-8'))
        self.send_count += 1
        self.notify_user(owner, f"{user} cancelou a reserva da sua acomodação {name} em {location} no dia {day}")
        self.send_count += 1
        self.notify_all_users(f"Acomodação {name} em {location} agora está disponível no dia {day}", exclude_addr=addr)

    def notify_user(self, user, message): # Função um usuário específico
        for addr, username in self.users.items():
            if username == user:
                self.rdt.send(addr, message.encode('utf-8'))
                break

    def notify_all_users(self, message, exclude_addr=None): # Função para notificar todos os usuários (exceto o que ativa a função)
        for addr in self.users:
            if addr != exclude_addr: #Não envia nada para o usuário que ativa a função
                self.send_count += 1
                self.rdt.send(addr, message.encode('utf-8'))

# Função principal para iniciar o servidor
def main_servidor():
    server = Servidor(skt.AF_INET, skt.SOCK_DGRAM, ADDR_BIND, MAX_BUFFER)  # Cria o servidor
    print(f"Servidor escutando em {ADDR_BIND}")

    try:
        while True:
            threading.Thread(target=server.handle_client).start()  # Inicia uma nova thread para cada cliente
    except KeyboardInterrupt:
        print("Encerrando o servidor...")  # Mensagem ao encerrar

# Verifica se o script está sendo executado diretamente
if __name__ == "__main__":
    main_servidor()  # Chama a função principal para iniciar o servidor
