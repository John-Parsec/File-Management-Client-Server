import socket
import threading
import os
import pickle

files_directory = './files'

def main():
    host = '127.0.0.1'
    port = 5050

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[*] Servidor escutando em {host}:{port}")

    while True:
        client, address = server.accept()
        print(f"[*] Conexão aceita de {address[0]}:{address[1]}")

        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()


def handle_client(client_socket: socket.socket):
    """
    Trata a conexão com um cliente e as requisições enviadas por ele.

    Recebe como parametro um socket conectado a um cliente.
    """

    while True:
        try:
            request = client_socket.recv(2048)                  # Recebe a requisição do cliente 
            
            request = pickle.loads(request)                     # Converte a requisição para um dicionário

            if request["request"] == 'LIST':
                response = list()
                client_socket.send(response)

            elif request["request"] == 'UPLOAD':
                upload(client_socket, request)

            elif request["request"] == 'DOWNLOAD':
                download(client_socket, request)

            elif request["request"] == 'DELETE':
                delete(request)

        except pickle.UnpicklingError:                      # Tratamento de erro para requisições corrompidas
            print("Arquivo corrompido recebido")

        except Exception as e:                              # Tratamento de erro para outros erros
            print(f"Erro: {e}")
            client_socket.close()
            break


def upload(client_socket: socket.socket, request: dict):
    """
    Recebe um arquivo enviado por um cliente e o salva no servidor.

    Recebe como parametros um socket conectado a um cliente e um dicionário com a requisição.
    """

    file_name = request["file_name"]                    # Extrai o nome do arquivo da requisição

    print(f"[*] Recebendo {file_name}...")

    file = b''

    while True:                                         # Loop para receber os dados do arquivo
        data = client_socket.recv(1000000)              # Recebe 1MB de dados
        
        if not data:
            break

        if b'EOF' in data:
            file += data.replace(b'EOF', b'')           # Remover o marcador 'EOF' dos dados recebidos
            break
        
        else:
            file += data

    print(f"[*] Arquivo {file_name} recebido com sucesso")
    
    file_path = os.path.join(files_directory, file_name)        # Caminho do arquivo no servidor

    with open(file_path, 'wb') as f:        
        f.write(file)                                           # Salva o arquivo no servidor


def download(client_socket: socket.socket, request: dict):
    """
    Envia um arquivo do servidor para um cliente.

    Recebe como parametros um socket conectado a um cliente e um dicionário com a requisição.
    """

    file_name = request["file_name"]                            # Extrai o nome do arquivo da requisição
    file_path = os.path.join(files_directory, file_name)        # Caminho do arquivo no servidor

    with open(file_path, 'rb') as file:
        while True:                                         # Loop para enviar os dados do arquivo
            data = file.read(1000000)                       # Lê 1MB do arquivo

            if not data:
                break
            
            client_socket.sendall(data)

        client_socket.sendall(b'EOF')                       # Enviar marcador de final de arquivo


def delete(request: dict):
    """
    Exclui um arquivo do servidor.

    Recebe como parametros um socket conectado a um cliente e um dicionário com a requisição.
    """

    file_name = request["file_name"]                    # Extrai o nome do arquivo da requisição
    print(f"[*] Excluindo {file_name}...")

    file_path = os.path.join(files_directory, file_name)        # Caminho do arquivo no servidor

    if os.path.isfile(file_path):
        os.remove(file_path)                            # Exclui o arquivo do servidor
        print(f"[*] Arquivo {file_name} excluido com sucesso")

    else:
        print(f"[*] Arquivo {file_name} não encontrado")


def listDirectoryContents(directory: str):
    """
    Recebe como parametro o caminho de um diretório.
    Retorna uma tupla com uma lista de arquivos e uma lista de subdiretórios.
    """

    content = os.listdir(directory)

    files = [item for item in content if os.path.isfile(os.path.join(directory, item))]
    subdirectories = [item for item in content if os.path.isdir(os.path.join(directory, item))]

    return files, subdirectories


def list():
    """
    Retorna um objeto serializavel com a estrutura de diretórios do servidor.
    """
    files_directories = listDirectoryContents(files_directory)

    directory_structure = {'Arquivos': files_directories[0], 'Diretorios': {}}      # Dicionário com a estrutura de diretórios

    for subdirectory in files_directories[1]:                                       # Loop para adicionar os subdiretórios
        subdirectory_path = os.path.join(files_directory, subdirectory)
        subdirectory_content = listDirectoryContents(subdirectory_path)
        directory_structure['Diretorios'][subdirectory] = {'Arquivos': subdirectory_content[0], 'Diretorios': {}}

    return  pickle.dumps(directory_structure)                                       # Serializa o dicionário e o retorna


if __name__ == '__main__':
    main()

