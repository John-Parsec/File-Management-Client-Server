import socket
import threading
import sys, os
import json
import pickle


host = '127.0.0.1'
port = 5050

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)

    while True:
        client, address = server.accept()
        print(f"[*] Conexão aceita de {address[0]}:{address[1]}")

        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()
    

def handle_client(client_socket):
    while True:
        try:
            request = client_socket.recv(1024)
            
            request = pickle.loads(request)

            if request["request"] == 'listar':
                response = list()
                client_socket.send(response.encode('utf-8'))

            elif request["request"] == 'enviar':
                file_name = request["file_name"]

                print(f"[*] Recebendo {file_name}...")

                file = b''

                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    file += data

                print(f"[*] Arquivo {file_name} recebido com sucesso")
                    
                file = pickle.loads(file)

                dest = 'teste/{}'.format(request['file_name'])
                with open(request['file_name'], 'wb') as f:
                    f.write(file)
                
                print('success on receiving and saving {} for {}'.format(request['file_name']))
                
                print(f"[*] Arquivo {file_name} salvo com sucesso")

        except KeyboardInterrupt:
            print('Saindo...')
            sys.exit(0)


def list_directory_contents(directory):
    content = os.listdir(directory)
    files = [item for item in content if os.path.isfile(os.path.join(directory, item))]
    subdirectories = [item for item in content if os.path.isdir(os.path.join(directory, item))]
    return files, subdirectories

def list():
    current_directory = os.path.dirname(__file__)

    files_directories = list_directory_contents(current_directory)

    directory_structure = {'Arquivos': files_directories[0], 'Diretorios': {}}

    for subdirectory in files_directories[1]:
        subdirectory_path = os.path.join(current_directory, subdirectory)
        subdirectory_content = list_directory_contents(subdirectory_path)
        directory_structure['Diretorios'][subdirectory] = {'Arquivos': subdirectory_content[0], 'Diretorios': {}}

    return  pickle.dumps(directory_structure, indent=2)



if __name__ == '__main__':
    main()

