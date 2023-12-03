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
    port = 5050

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    menu(client)

    print('Desconectando...')
    sys.exit(0)


def menu(client_socket: socket.socket):
    """
    Exibe o menu principal e trata as opções selecionadas pelo usuário.

    Recebe um socket conectado a um cliente.
    """

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
    
    def onExit():
        message = createMessage(resquest='DISCONNECT')
        client_socket.send(message)
        client_socket.close()
        mainWindow.quit()

    # Botões para cada opção do menu
    btn_listar = tk.Button(mainWindow, text="Listar Arquivos", command=onListFiles)
    btn_enviar = tk.Button(mainWindow, text="Enviar Arquivo", command=onSendFile)
    btn_baixar = tk.Button(mainWindow, text="Baixar Arquivo", command=onDownloadFile)
    btn_sair = tk.Button(mainWindow, text="Sair", command=onExit)

    # Posicionamento dos botões na janela
    btn_listar.pack(pady=10)
    btn_enviar.pack(pady=10)
    btn_baixar.pack(pady=10)
    btn_sair.pack(pady=10)

    mainWindow.mainloop()


def createMessage(resquest: dict, file_name: str = "", file_size: str = "") -> bytes:
    """
    Cria uma mensagem para o servidor no formato: {resquest: <request>, file_name: <file_name>, file_size: <file_size>, file_path: <file_path>}

    Retorna a mensagem serializada em bytes
    """
    message = {'request': resquest, 'file_name': file_name, 'file_size': file_size}

    return pickle.dumps(message)


def list(client_socket: socket.socket):
    """
    Busca a lista de arquivos e diretórios do servidor e exibe na tela.

    Recebe um socket conectado a um cliente
    """

    message = createMessage(resquest='LIST')

    client_socket.send(message)

    response = client_socket.recv(2048)

    files = pickle.loads(response)
    printFiles(files)


def printFiles(directory, level=0, tree=None, parent=""):
    """
    Exibe os arquivos e diretórios de um diretório na interface.

    Recebe um dicionário com os arquivos e diretórios, o nível de indentação e uma árvore (Treeview) para exibir os arquivos e diretórios.
    """
    
    if tree is None:
        # Cria a janela principal
        root = tk.Tk()
        root.title("Exibição de Diretório")

        # Cria uma árvore (Treeview) para exibir os arquivos e diretórios
        tree = tk.ttk.Treeview(root)
        tree.heading("#0", text="Arquivos e Diretórios")
        tree.pack(expand=True, fill=tk.BOTH)

    prefix = "  " * level  # Prefixo para a indentação
    
    for file in directory.get("Arquivos", []):                                  # Adiciona arquivos à árvore
        tree.insert(parent, "end", text=f"{prefix}- {file}")
    
    for subdir, subdir_content in directory.get("Diretorios", {}).items():      # Adiciona diretórios à árvore e chama a função recursivamente
        item_id = tree.insert(parent, "end", text=f"{prefix}+ {subdir}/")
        printFiles(subdir_content, level + 1, tree, item_id)


def upload(client_socket: socket.socket):
    """
    Exibe uma janela para selecionar um arquivo e envia o arquivo para o servidor.

    Recebe um socket conectado a um cliente
    """

    file_path = filedialog.askopenfilename()

    if not os.path.isfile(file_path):
        print('Arquivo não encontrado')
        return
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    message = createMessage(resquest='UPLOAD', file_name=file_name, file_size=file_size)
    client_socket.sendall(message)

    uploadFile(client_socket, file_path)


def uploadFile(client_socket: socket.socket, file_path: str):
    """
    Envia um arquivo para o servidor.

    Recebe um socket conectado a um cliente e o caminho do arquivo a ser enviado.
    """

    with open(file_path, 'rb') as file:
        while True:                         # Loop para enviar os dados do arquivo
            data = file.read(1000000)       # Lê 1MB do arquivo
            
            if not data:
                break
            
            client_socket.sendall(data)

        client_socket.sendall(b'EOF')       # Enviar marcador de final de arquivo


def download(client_socket: socket.socket):
    """
    Exibe uma janela para selecionar um arquivo e baixa o arquivo do servidor.

    Recebe um socket conectado a um cliente
    """
    root = tk.Tk()                                              # Cria uma nova janela
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


    message = createMessage(resquest='LIST')                # Envia uma requisição da lista de arquivos e diretórios para o servidor

    client_socket.send(message)

    response = client_socket.recv(2048)

    directory = pickle.loads(response)


    # Exibe os arquivos e diretórios na árvore
    printFiles(directory, tree=tree)                            

    # Adiciona botão de download
    download_button = ttk.Button(root, text="Download", command=getSelectedFile)
    download_button.pack()

    root.mainloop()


def downloadFile(client_socket: socket.socket, file_path: str):
    """
    Baixa um arquivo do servidor.
    
    Recebe um socket conectado a um cliente e o caminho do arquivo a ser baixado.
    """

    message = createMessage(resquest='DOWNLOAD', file_name=file_path)
    client_socket.send(message)

    file_name = os.path.basename(file_path)

    file_name = os.path.join(downloads_directory, file_name)        # Caminho do arquivo no cliente

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

    with open(file_name, 'wb') as f:                    # Salva o arquivo no cliente
        f.write(file)

    print('Arquivo baixado com sucesso')


if __name__ == '__main__':
    main()

