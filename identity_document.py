import os
import argparse
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# set `<your-endpoint>` and `<your-key>` variables with the values from the Azure portal
ENDPOINT = "https://visiondocument01.cognitiveservices.azure.com/"
API_KEY = "e30f60769b204e79ade3cd9ac8d1f389"

def analyze_document(client, document_path):
    with open(document_path, "rb") as fd:
        document = fd.read()

    poller = client.begin_analyze_document("prebuilt-idDocument", document)
    result = poller.result()

    for doc in result.documents:
        print("Document detected:")
        for field in doc.fields.values():
            print(f"{field.name}: {field.value} (confidence: {field.confidence})")


def main(dataset_path):
    client = DocumentAnalysisClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))

    for root, _, files in os.walk(dataset_path):
        for file in files:
            if file.endswith((".jpg", ".jpeg", ".png", ".pdf")):
                document_path = os.path.join(root, file)
                print(f"Processing document: {document_path}")
                analyze_document(client, document_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process identity documents using Azure Document Intelligence.")
    parser.add_argument("dataset_path", help="Path to the dataset containing identity documents.")

    args = parser.parse_args()

    main(args.dataset_path)
