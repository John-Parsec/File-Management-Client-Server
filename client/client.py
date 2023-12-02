import socket
import pickle
import sys
import os

import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

downloads_directory = './download'

def main():
    host = '127.0.0.1'
    port = 5051

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    menu(client)

    print('Desconectando...')
    sys.exit(0)


def menu(client_socket):
    mainWindow = tk.Tk()
    mainWindow.title("Menu")

    mainWindow.minsize(200,200)
    mainWindow.maxsize(300, 250)

    def onListFiles():
        list(client_socket)

    def onSendFile():
        upload(client_socket)

    def onDownloadFile():
        download(client_socket)

    # Botões para cada opção do menu
    btn_listar = tk.Button(mainWindow, text="Listar Arquivos", command=onListFiles)
    btn_enviar = tk.Button(mainWindow, text="Enviar Arquivo", command=onSendFile)
    btn_baixar = tk.Button(mainWindow, text="Baixar Arquivo", command=onDownloadFile)
    btn_sair = tk.Button(mainWindow, text="Sair", command=mainWindow.quit)

    # Posicionamento dos botões na janela
    btn_listar.pack(pady=10)
    btn_enviar.pack(pady=10)
    btn_baixar.pack(pady=10)
    btn_sair.pack(pady=10)

    mainWindow.mainloop()



#Cria uma mensagem no formato:
# {resquest: <request>, file_name: <file_name>, file_size: <file_size>, file_path: <file_path>}
def createMessage(resquest, file_name = "", file_size = ""):
    message = {'request': resquest, 'file_name': file_name, 'file_size': file_size}

    return pickle.dumps(message)




#Lista os arquivos disponíveis no servidor
def list(client_socket):
    message = createMessage(resquest='LIST')

    client_socket.send(message)

    response = client_socket.recv(2048)

    files = pickle.loads(response)
    printFiles(files)


def printFiles(directory, level=0, tree=None, parent=""):
    if tree is None:
        # Cria a janela principal
        root = tk.Tk()
        root.title("Exibição de Diretório")

        # Cria uma árvore (Treeview) para exibir os arquivos e diretórios
        tree = tk.ttk.Treeview(root)
        tree.heading("#0", text="Arquivos e Diretórios")
        tree.pack(expand=True, fill=tk.BOTH)

    prefix = "  " * level  # Prefixo para a indentação

    # Adiciona arquivos à árvore
    for file in directory.get("Arquivos", []):
        tree.insert(parent, "end", text=f"{prefix}- {file}")

    # Adiciona diretórios à árvore e chama a função recursivamente
    for subdir, subdir_content in directory.get("Diretorios", {}).items():
        item_id = tree.insert(parent, "end", text=f"{prefix}+ {subdir}/")
        printFiles(subdir_content, level + 1, tree, item_id)




#Envia um arquivo para o servidor
def upload(client_socket):
    file_path = filedialog.askopenfilename()

    if not os.path.isfile(file_path):
        print('Arquivo não encontrado')
        return
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    message = createMessage(resquest='UPLOAD', file_name=file_name, file_size=file_size)
    client_socket.sendall(message)

    uploadFile(client_socket, file_path)


def uploadFile(client_socket, file_path):
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
    def getSelectedFile():
        selected_item = tree.selection()
        if selected_item:
            selected_text = tree.item(selected_item, "text")
            if selected_text.startswith("+ "):  # Ignora os diretórios
                return
            file_name = selected_text.split("- ")[1]
            downloadFile(client_socket, file_name)
            root.destroy()
    
    message = createMessage(resquest='LIST')

    client_socket.send(message)

    response = client_socket.recv(2048)

    directory = pickle.loads(response)

    # Adiciona os itens à árvore
    printFiles(directory, tree=tree)

    # Adiciona botão de download
    download_button = ttk.Button(root, text="Download", command=getSelectedFile)
    download_button.pack()

    root.mainloop()


#Baixa um arquivo do servidor
def downloadFile(client_socket, file_path):
    message = createMessage(resquest='DOWNLOAD', file_name=file_path)
    client_socket.send(message)

    file_name = os.path.basename(file_path)

    file_name = os.path.join(downloads_directory, file_name)    

    file = b''

    while True:
        data = client_socket.recv(2048)
        if not data:
            break
        if b'EOF' in data:
            # Remover o marcador 'EOF' dos dados recebidos
            file += data.replace(b'EOF', b'')
            break
        else:
            file += data

    with open(file_name, 'wb') as f:
        f.write(file)

    print('Arquivo baixado com sucesso')



if __name__ == '__main__':
    main()

