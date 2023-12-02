import socket
import threading
import sys, os
import pickle

host = '127.0.0.1'
port = 5051

files_directory = './files'

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[*] Servidor escutando em {host}:{port}")

    while True:
        client, address = server.accept()
        print(f"[*] Conexão aceita de {address[0]}:{address[1]}")

        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()
    


def handle_client(client_socket):
    while True:
        try:
            request = client_socket.recv(2048)
            
            request = pickle.loads(request)

            if request["request"] == 'LIST':
                response = list()
                client_socket.send(response)

            elif request["request"] == 'UPLOAD':
                upload(client_socket, request)

            elif request["request"] == 'DOWNLOAD':
                download(client_socket, request)

        except KeyboardInterrupt:
            print('Saindo...')
            sys.exit(0)
        except pickle.UnpicklingError:
            print("Arquivo corrompido recebido")
        except Exception as e:
            print(f"Erro desconhecido: {e}")



def upload(client_socket, request):
    file_name = request["file_name"]

    print(f"[*] Recebendo {file_name}...")

    file = b''

    while True:
        data = client_socket.recv(1000000)
        if not data:
            break
        if b'EOF' in data:
            # Remover o marcador 'EOF' dos dados recebidos
            file += data.replace(b'EOF', b'')
            break
        else:
            file += data

    print(f"[*] Arquivo {file_name} recebido com sucesso")
        
    file_path = os.path.join(files_directory, file_name)

    with open(file_path, 'wb') as f:
        f.write(file)



def download(client_socket, request):
    file_name = request["file_name"]
    file_path = os.path.join(files_directory, file_name)

    with open(file_path, 'rb') as file:
        while True:
            data = file.read(1000000)
            if not data:
                break
            client_socket.sendall(data)

        # Enviar marcador de final de arquivo
        client_socket.sendall(b'EOF')




def listDirectoryContents(directory):
    content = os.listdir(directory)
    files = [item for item in content if os.path.isfile(os.path.join(directory, item))]
    subdirectories = [item for item in content if os.path.isdir(os.path.join(directory, item))]
    return files, subdirectories

def list():
    files_directories = listDirectoryContents(files_directory)

    directory_structure = {'Arquivos': files_directories[0], 'Diretorios': {}}

    for subdirectory in files_directories[1]:
        subdirectory_path = os.path.join(files_directory, subdirectory)
        subdirectory_content = listDirectoryContents(subdirectory_path)
        directory_structure['Diretorios'][subdirectory] = {'Arquivos': subdirectory_content[0], 'Diretorios': {}}

    return  pickle.dumps(directory_structure)



if __name__ == '__main__':
    main()

