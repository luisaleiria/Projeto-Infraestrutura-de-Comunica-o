import socket as skt
import os
import time

MAX_BUFFER = 1024
ADDR_BIND = ('localhost', 7070)

class servidor:
    def __init__(self, sckt_family, sckt_type, sckt_binding, MAX_BUFFER):
        self.sckt = skt.socket(sckt_family, sckt_type)
        self.sckt.bind(sckt_binding) # Vincula o socket ao endereço sckt_binding.
        #self.sckt.settimeout(0.1)  # se passar desse tempo dá um timeout
        
        #if self.sckt is None: # se o socket nao puder ser criado
        #    raise Exception("Socket indisponível")
        
        self.MAX_BUFFER = MAX_BUFFER

    def receive_file(self): # Recebe o nome do arquivo enviado pelo cliente.
        data, client_address = self.sckt.recvfrom(self.MAX_BUFFER)
        filename = data.decode('utf-8')
        print(f"Arquivo recebido: {filename}")
        
        # Prepara para receber o arquivo
        with open('recebido_' + filename, 'wb') as f: # Abre um novo arquivo com um nome temporário (recebido_ + filename) para escrita em modo binário.
            while True:
                try:
                    data, addr = self.sckt.recvfrom(self.MAX_BUFFER)
                    if data == b'EOF': # recebe dados ate o eof
                        print("Recepção do arquivo concluída.")
                        break
                    f.write(data)
                except skt.timeout:
                    continue  # continua escutando em caso de timeout
        
        # Renomeia o arquivo
        new_filename = 'retornado_' + filename
        os.rename('recebido_' + filename, new_filename)
        
        return new_filename, client_address #Retorna o novo nome do arquivo e o endereço do cliente.

    def send(self, client_addr: tuple[str, int], msg: bytes):
        self.sckt.sendto(msg, client_addr) # Envia uma mensagem (msg) para o endereço do cliente (client_addr)
        time.sleep(0.0001)  # pequena pausa para evitar congestionamento de rede

    def send_file(self, client_addr: tuple[str, int], filepath: str):
        with open(filepath, 'rb') as f: # Abre o arquivo especificado (filepath) em modo de leitura binária.
            while True:
                data = f.read(self.MAX_BUFFER) # le o arquivo de 1024 em 1024 bytes
                if not data:
                    break
                self.send(client_addr, data)
        
        # Notifica o cliente que o envio do arquivo terminou
        self.send(client_addr, b'EOF')

def main():
    server = servidor(skt.AF_INET, skt.SOCK_DGRAM, ADDR_BIND, MAX_BUFFER) # criando a instancia da classe servidor
    print(f"Server está escutando no {ADDR_BIND}") # onde o servidor esta escutando
    
    while True: # entrando em looping infinito
        filename, client_address = server.receive_file() # recebendo arquivos de clientes
        
        # Envia o novo nome do arquivo para o cliente
        server.send(client_address, filename.encode('utf-8'))
        
        server.send_file(client_address, filename) # envia o arquivo renomeado para o cliente
        os.remove(filename) # remove arquivo apos o envio 

if __name__ == "__main__":
    main()
