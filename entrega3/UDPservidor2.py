import socket as skt
import os
import time
import random

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
          
    # Envia um arquivo 
    def send_file(self, addr, filepath):
        filename = os.path.basename(filepath) #recebe o nome do arquivo
        self.send(addr, filename.encode('utf-8')) #envia o nme do arquivo

        #Abre o arquivo em leitura binária
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(self.max_buffer - 2) #le o arquivo de 1024 em 1024 bytes
                if not data:
                    break #termina se n ouver dados
                self.send(addr, data) #envia oq foi lido
                time.sleep(0.1)  # tempo para evitar congestionamento

        self.send(addr, b'EOF') #avisa que chegou ao fim do arquivo

#recebe um arquivo e muda o nome especificado
    def receive_file(self, save_as):
        with open(save_as, 'wb') as f: #abre um arquivo
            while True:
                data, _ = self.receive() #recebe os dados
                if data == b'EOF':
                    print("Recepção do arquivo concluída.")
                    break #termina ao chegar no fim do arquivo
                f.write(data) # escreve os dados no arquivo



class Servidor:
    def __init__(self, sckt_family, sckt_type, sckt_binding, max_buffer):
        self.sckt = skt.socket(sckt_family, sckt_type) #cria o socket
        self.sckt.bind(sckt_binding) # vincula o socket ao endereço dado
        self.rdt = RDT(self.sckt, max_buffer) #cria uma instancia do rdt

    def receive_file(self):
        filename, client_addr = self.rdt.receive() #recebe o nome do arquivo
        filename = filename.decode('utf-8') #traduz nome do arquivo
        print(f"Arquivo recebido: {filename}")
        new_filename = 'retornado_' + filename #cria o nome com retornado
        self.rdt.receive_file('recebido_' + filename) #recebe o arquivo
        os.rename('recebido_' + filename, new_filename) #renomeia o arquivo
        return new_filename, client_addr #retorna o nome novo e o endereço do cliente

    def send_file(self, client_addr, filepath):
        self.rdt.send_file(client_addr, filepath) #envia o arquivo pro cliente


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
