import socket
import json
import pickle
import sys
import os

#Lista os arquivos disponíveis no servidor
def list(client_socket):
    message = createMessage(resquest='listar')

    client_socket.send(message)

    response = client_socket.recv(1024)

    files = pickle.loads(response)
    imprimir_lista(files)

    #print_directory_structure(response)

def imprimir_lista(diretorio, nivel=0):
    prefixo = "  " * nivel  # Prefixo para a indentação

    # Imprimir arquivos
    for arquivo in diretorio.get("Arquivos", []):
        print(f"{prefixo}- {arquivo}")

    # Recursivamente imprimir diretórios
    for subdir, subdir_content in diretorio.get("Diretorios", {}).items():
        print(f"{prefixo}+ {subdir}/")
        imprimir_lista(subdir_content, nivel + 1)


#Envia um arquivo para o servidor
def send(client_socket):
    file_path = input('Digite o caminho do arquivo: ')

    if not os.path.isfile(file_path):
        print('Arquivo não encontrado')
        return
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    message = createMessage(resquest='enviar', file_name=file_name, file_size=file_size)
    client_socket.sendall(message)

    send_file(client_socket, file_path)

# def send_file(client_socket, file_path):
#     file = open(file_path, 'rb').read()
#     client_socket.sendall(pickle.dumps(file))
#     client_socket.sendall(b'EOF')

def send_file(client_socket, file_path):
    with open(file_path, 'rb') as file:
        while True:
            data = file.read(1024)
            if not data:
                break
            client_socket.sendall(data)

        # Enviar marcador de final de arquivo
        client_socket.sendall(b'EOF')

#Baixa um arquivo do servidor
def download():
    pass


#Cria uma mensagem no formato:
# {resquest: <request>, file_name: <file_name>, file_size: <file_size>, file_path: <file_path> file: <file>}
#
def createMessage(resquest, file_name = "", file_size = ""):
    message = {'request': resquest, 'file_name': file_name, 'file_size': file_size}

    return pickle.dumps(message)


def menu(client_socket):
    while True:
        print('1 - Listar arquivos')
        print('2 - Enviar')
        print('3 - Baixar')
        print('4 - Sair')
        print('Digite a opção desejada: ', end='')

        opcao = int(input())

        if opcao == 1:
            list(client_socket)
        elif opcao == 2:
            send(client_socket)
        elif opcao == 3:
            download(client_socket)
        elif opcao == 4:
            break
        else:
            print('Opção inválida')

def main():
    host = '127.0.0.1'
    port = 5050

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    menu(client)

    print('Desconectando...')
    sys.exit(0)

if __name__ == '__main__':
    main()

