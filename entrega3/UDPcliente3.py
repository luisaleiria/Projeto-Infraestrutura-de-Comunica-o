import socket as skt  
import time  
import threading  
import random  


MAX_BUFFER = 1024  # Define o tamanho máximo dos dados que podem ser recebidos pelo socket
ADDR_BIND = ('localhost', 8080)  # Define o endereço e a porta onde o cliente se vinculará
ADDR_TARGET = ('127.0.0.1', 7070)  # Define o endereço e a porta do servidor de destino

LOSS_PROBABILITY = 0  # Define a probabilidade de perda de pacotes (0 = sem perda)

# Classe RDT 3.0 (Feita nas etapas anteriores) para gerenciar a transferência confiável de dados
class RDT:
    def __init__(self, socket, max_buffer):
        self.socket = socket  # Armazena o socket para comunicação
        self.max_buffer = max_buffer  # Armazena o tamanho máximo do buffer
        self.seq_num = 0  # Inicializa o número de sequência

    def send(self, addr, msg):
        # Simula a perda de pacotes com a probabilidade definida
        if random.random() < LOSS_PROBABILITY:
            
            return  # Simula a perda do pacote

        # Cria um pacote com o número de sequência e a mensagem
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
                self.socket.sendto(f"ACK{recv_seq_num}".encode('utf-8'), addr)
                self.seq_num = 1 - self.seq_num  # Alterna o número de sequência
                return msg, addr  # Retorna a mensagem e o endereço

# Classe Cliente para gerenciar as operações do cliente
class Cliente:
    def __init__(self, sckt_family, sckt_type, sckt_binding, max_buffer):
        self.sckt = skt.socket(sckt_family, sckt_type)  # Cria o socket
        self.sckt.bind(sckt_binding)  # Vincula o socket ao endereço fornecido
        self.rdt = RDT(self.sckt, max_buffer)  # Instancia a classe RDT
        self.server_addr = ADDR_TARGET  # Define o endereço do servidor
        self.running = True  # Flag para controle de execução

    def login(self, username):
        self.rdt.send(self.server_addr, f"login {username}".encode('utf-8'))  # Envia comando de login

    def logout(self):
        self.rdt.send(self.server_addr, b"logout")  # Envia comando de logout

    def create_accommodation(self, name, location, description):
        self.rdt.send(self.server_addr, f"create {name} {location} {description}".encode('utf-8'))  # Envia comando para criar acomodação

    def list_my_accommodations(self):
        self.rdt.send(self.server_addr, b"list:myacmd")  # Envia comando para listar acomodações do usuário

    def list_accommodations(self):
        self.rdt.send(self.server_addr, b"list:acmd")  # Envia comando para listar todas as acomodações

    def list_my_reservations(self):
        self.rdt.send(self.server_addr, b"list:myrsv")  # Envia comando para listar as reservas do usuário

    def book_accommodation(self, owner, name, location, day):
        self.rdt.send(self.server_addr, f"book {owner} {name} {location} {day}".encode('utf-8'))  # Envia comando para reservar uma acomodação

    def cancel_reservation(self, owner, name, location, day):
        self.rdt.send(self.server_addr, f"cancel {owner} {name} {location} {day}".encode('utf-8'))  # Envia comando para cancelar uma reserva
        msg, _ = self.rdt.receive()  # Recebe a resposta do servidor

    def listen_for_messages(self):
        while self.running:
            msg, addr = self.rdt.receive()  # Recebe mensagens do servidor
            print(f"Mensagem do servidor: {msg.decode('utf-8')}")  # Imprime a mensagem recebida

    def start_listener(self):
        # Inicia uma thread para escutar mensagens do servidor
        self.listener_thread = threading.Thread(target=self.listen_for_messages)
        self.listener_thread.start()

    def stop_listener(self):
        self.running = False  # Para o loop de escuta
        self.listener_thread.join()  # Espera a thread terminar

# Função principal para iniciar o cliente
def main_cliente():
    client = Cliente(skt.AF_INET, skt.SOCK_DGRAM, ADDR_BIND, MAX_BUFFER)  # Cria o cliente
    client.start_listener()  # Inicia o listener de mensagens

    try:
        while True:
            command = input("> ")  # Lê comandos do usuário
            if command.startswith("login"):
                _, username = command.split()
                client.login(username)  # Realiza login
            elif command == "logout":
                client.logout()  # Realiza logout
            elif command.startswith("create"):
                _, name, location, *description = command.split()
                client.create_accommodation(name, location, ' '.join(description))  # Cria uma acomodação
            elif command == "list:myacmd":
                client.list_my_accommodations()  # Lista acomodações do usuário
            elif command == "list:acmd":
                client.list_accommodations()  # Lista todas as acomodações
            elif command == "list:myrsv":
                client.list_my_reservations()  # Lista reservas do usuário
            elif command.startswith("book"):
                _, owner, name, location, day = command.split()
                client.book_accommodation(owner, name, location, day)  # Reserva uma acomodação
            elif command.startswith("cancel"):
                _, owner, name, location, day = command.split()
                client.cancel_reservation(owner, name, location, day)  # Cancela uma reserva
    except KeyboardInterrupt:
        print("Encerrando o cliente...")  # Mensagem ao encerrar
        client.stop_listener()  # Para o listener

# Verifica se o script está sendo executado diretamente
if __name__ == "__main__":
    main_cliente()  # Chama a função principal para iniciar o cliente