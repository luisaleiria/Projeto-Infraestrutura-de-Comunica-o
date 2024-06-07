import socket as skt
import os
import time


MAX_BUFFER = 1024 #tam max dos dados
addr_bind = ('hostLocal', 8080) #end e porta que o cliente esta vinculado
addr_target = ('127.0.0.1', 7070) #end e porta do servidor


class cliente():
    def __init__(self, sckt_family, sckt_type, sckt_binding, MAX_BUFFER):
        self.sckt = skt.socket(sckt_family, sckt_type)
        self.sckt.bind(sckt_binding) # socket vinculado ao endereço de sckt_binding
        self.sckt.settimeout(0.1) # se passar desse tempo da um timeOut (tempo de espera)

        if self.sckt is None: # entra aqui se o socket nao puder ser criado
            raise Exception ("Socket indisponivel")
        
        self.MAX_BUFFER = MAX_BUFFER # mesmo tam max do buffer original

    def listen(self):
            # Recebe o nome do arquivo renomeado do servidor
        data, _ = self.sckt.recvfrom(self.MAX_BUFFER)
        new_filename = data.decode('utf-8') # abre um novo arquivo com o nome recebido para que ele possa ser escrito em modo binario
        print(f"Recendo o arquivo: {new_filename}") #avisa que a file foi recebida

        with open(new_filename, 'wb') as f:
            while True:
                try:
                    data, _ = self.sckt.recvfrom(self.MAX_BUFFER)
                    if data == b'EOF': #quando parar de falar (recebe ate o fim (EOF))
                        print("Recepção do arquivo concluída.") # avisa que terminou de receber
                        self.sckt.close()
                        break # fecha o socket e sai do loop
                    f.write(data)
                except:
                    continue # ta ignorando o erro para continuar escutando
        
    def send(self, server_addr: tuple[str,str], msg:bytes):
            self.sckt.sendto(msg, server_addr) # envia msg (uma mensagem) para o end de servidor
            time.sleep(0.0001) # pequena pausa para evitar congestionamento de rede

    def send_file (self, server_addr: tuple[str, int], filepath: str): # Extrai o nome do arquivo do caminho (filepath) e envia esse nome para o servidor.
        filename = os.path.basename(filepath)
        self.send(server_addr, filename.encode('utf-8'))

        with open(filepath, 'rb') as f: #Abre o arquivo em modo de leitura binária.
            while True:
                data = f.read(self.MAX_BUFFER) # le o arquivo de 1024 em 1024 bytes
                if not data:
                    break
                self.send(server_addr, data)
        
        # Notifica o servidor que o envio do arquivo terminou
        self.send(server_addr, b'EOF')

def main():
    client = cliente(skt.AF_INET, skt.SOCK_DGRAM, addr_bind, MAX_BUFFER) #Cria uma instância da classe cliente.
    
    filename = input("Digite o nome do arquivo a ser enviado: ")
    if not os.path.isfile(filename): #Verifica se o arquivo existe; se não existir, imprime uma mensagem de erro e sai.
        print(f"File {filename} does not exist.")
        return
    
    client.send_file(addr_target, filename) # se existir Envia o arquivo especificado para o servidor.
    client.listen()  # para colocar ele para escutar

if __name__ == "__main__":
    main()





