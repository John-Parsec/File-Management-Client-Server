import socket
import pickle
import sys
import os

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

downloads_directory = './download'


#Lista os arquivos disponíveis no servidor
def list(client_socket):
    message = createMessage(resquest='listar')

    client_socket.send(message)

    response = client_socket.recv(2048)

    files = pickle.loads(response)
    print_list(files)



# def print_list(diretorio, nivel=0):
#     prefixo = "  " * nivel  # Prefixo para a indentação

#     # Imprimir arquivos
#     for arquivo in diretorio.get("Arquivos", []):
#         print(f"{prefixo}- {arquivo}")

#     # Recursivamente imprimir diretórios
#     for subdir, subdir_content in diretorio.get("Diretorios", {}).items():
#         print(f"{prefixo}+ {subdir}/")
#         print_list(subdir_content, nivel + 1)


def print_list(diretorio, nivel=0, tree=None, parent=""):
    if tree is None:
        # Cria a janela principal
        root = tk.Tk()
        root.title("Exibição de Diretório")

        # Cria uma árvore (Treeview) para exibir os arquivos e diretórios
        tree = tk.ttk.Treeview(root)
        tree.heading("#0", text="Arquivos e Diretórios")
        tree.pack(expand=True, fill=tk.BOTH)

    prefixo = "  " * nivel  # Prefixo para a indentação

    # Adiciona arquivos à árvore
    for arquivo in diretorio.get("Arquivos", []):
        tree.insert(parent, "end", text=f"{prefixo}- {arquivo}")

    # Adiciona diretórios à árvore e chama a função recursivamente
    for subdir, subdir_content in diretorio.get("Diretorios", {}).items():
        item_id = tree.insert(parent, "end", text=f"{prefixo}+ {subdir}/")
        print_list(subdir_content, nivel + 1, tree, item_id)

    






#Envia um arquivo para o servidor
def send(client_socket):
    file_path = filedialog.askopenfilename()

    if not os.path.isfile(file_path):
        print('Arquivo não encontrado')
        return
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    message = createMessage(resquest='enviar', file_name=file_name, file_size=file_size)
    client_socket.sendall(message)

    send_file(client_socket, file_path)


def send_file(client_socket, file_path):
    with open(file_path, 'rb') as file:
        while True:
            data = file.read(2048)
            if not data:
                break
            client_socket.sendall(data)

        # Enviar marcador de final de arquivo
        client_socket.sendall(b'EOF')


def download(client_socket):
    root = tk.Tk()
    root.title("Selecionar Arquivo para Download")

    tree = ttk.Treeview(root)
    tree.heading("#0", text="Arquivos e Diretórios")
    tree.pack(expand=True, fill=tk.BOTH)

    # Função para obter o caminho do arquivo selecionado
    def get_selected_file():
        selected_item = tree.selection()
        if selected_item:
            selected_text = tree.item(selected_item, "text")
            if selected_text.startswith("+ "):  # Ignora os diretórios
                return
            file_name = selected_text.split("- ")[1]
            download_file(client_socket, file_name)
            root.destroy()
    
    message = createMessage(resquest='listar')

    client_socket.send(message)

    response = client_socket.recv(2048)

    diretorio = pickle.loads(response)

    # Adiciona os itens à árvore
    print_list(diretorio, tree=tree)

    # Adiciona botão de download
    download_button = ttk.Button(root, text="Download", command=get_selected_file)
    download_button.pack()

    root.mainloop()



#Baixa um arquivo do servidor
def download_file(client_socket, file_path):
    #file_name = input('Digite o nome do arquivo: ')

    message = createMessage(resquest='baixar', file_name=file_path)
    client_socket.send(message)

    file_name = os.path.basename(file_path)

    file_name = os.path.join(downloads_directory, file_name)    

    file_data = b''

    with open(file_name, 'wb') as file:
        while True:
            data = client_socket.recv(2048)

            if not data or b'EOF' in data:
                break
                
            file_data += data
        
        file.write(data)

        print('Arquivo baixado com sucesso')

    


#Cria uma mensagem no formato:
# {resquest: <request>, file_name: <file_name>, file_size: <file_size>, file_path: <file_path>}
#
def createMessage(resquest, file_name = "", file_size = ""):
    message = {'request': resquest, 'file_name': file_name, 'file_size': file_size}

    return pickle.dumps(message)



def menu(client_socket):
    mainWindow = tk.Tk()
    mainWindow.title("Menu")

    def on_list_files():
        list(client_socket)

    def on_send_file():
        send(client_socket)

    def on_download_file():
        download(client_socket)

    # Botões para cada opção do menu
    btn_listar = tk.Button(mainWindow, text="Listar Arquivos", command=on_list_files)
    btn_enviar = tk.Button(mainWindow, text="Enviar Arquivo", command=on_send_file)
    btn_baixar = tk.Button(mainWindow, text="Baixar Arquivo", command=on_download_file)
    btn_sair = tk.Button(mainWindow, text="Sair", command=mainWindow.quit)

    # Posicionamento dos botões na janela
    btn_listar.pack(pady=10)
    btn_enviar.pack(pady=10)
    btn_baixar.pack(pady=10)
    btn_sair.pack(pady=10)

    mainWindow.mainloop()

def main():
    host = '127.0.0.1'
    port = 5051

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    menu(client)

    print('Desconectando...')
    sys.exit(0)

if __name__ == '__main__':
    main()

