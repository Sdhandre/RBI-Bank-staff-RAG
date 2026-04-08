from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader


def load_documents(pdf_directory: str):
    all_documents = []
    pdf_dir = Path(pdf_directory)

    pdf_files = list(pdf_dir.glob("**/*.pdf"))
    print(f"Found {len(pdf_files)} PDF files.")

    for pdf_file in pdf_files:
        try:
            loader = PyMuPDFLoader(str(pdf_file))
            documents = loader.load()

            for doc in documents:
                doc.metadata = {
                    "source": pdf_file.name,
                    "file_path": str(pdf_file),
                    "page": doc.metadata.get("page", None)
                }

            all_documents.extend(documents)

        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

    print(f"Total documents loaded: {len(all_documents)}")
    return all_documents