import os

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# Configurações de endpoint e chave da API
ENDPOINT = "https://visiondocument01.cognitiveservices.azure.com/"
API_KEY = "e30f60769b204e79ade3cd9ac8d1f389"

def analyze_document(client, document_path, model_id):
    with open(document_path, "rb") as fd:
        document = fd.read()

    poller = client.begin_analyze_document(model_id, document)
    result = poller.result()

    for doc in result.documents:
        print("Document detected:")
        for field in doc.fields.values():
            print(field)

def main(dataset_path, model_id):
    client = DocumentAnalysisClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))

    for root, _, files in os.walk(dataset_path):
        for file in files:
            if file.endswith((".jpg", ".jpeg", ".png", ".pdf")):
                document_path = os.path.join(root, file)
                print(f"Processing document: {document_path}")
                analyze_document(client, document_path, model_id)

if __name__ == "__main__":
    dataset_path = r"C:\Users\Dell\Documents\SDLabs\AI_Document_Parser\AI_Vision\Document_data_sample\BID Sample Dataset"
    model_id = "custom-cnh-model"
    main(dataset_path, model_id)
