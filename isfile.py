import os

# Defina o caminho para a pasta
path = r"C:\Users\Dell\Documents\SDLabs\AI_Document_Parser\AI_Vision\Document_data_sample\BID Sample Dataset\CNH_Aberta"

# Iterar sobre os arquivos na pasta e imprimir o nome de cada um
for filename in os.listdir(path):
    file_path = os.path.join(path, filename)
    if os.path.isfile(file_path):
        print(filename)
