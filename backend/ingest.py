import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DATA_PATH = "../data"
CHROMA_PATH = "./chroma_db"

ALLOWED_EXTENSIONS = [".md", ".txt", ".tsx", ".ts", ".js", ".jsx", ".py"]


def load_files():
    documents = []

    for root, _, files in os.walk(DATA_PATH):
        for file in files:
            if any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                path = os.path.join(root, file)

                loader = TextLoader(path, encoding="utf-8")
                docs = loader.load()

                for doc in docs:
                    doc.metadata["source"] = path
                    doc.metadata["file_name"] = file
                    doc.metadata["file_extension"] = os.path.splitext(file)[1]
                    doc.metadata["folder"] = os.path.basename(root)
                    doc.metadata["relative_path"] = os.path.relpath(path, DATA_PATH)

                documents.extend(docs)

    return documents


def split_documents(documents):
    chunks = []

    for doc in documents:
        source = doc.metadata.get("source", "")
        extension = os.path.splitext(source)[1]

        if extension in [".ts", ".tsx", ".js", ".jsx", ".py"]:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100
            )
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=900,
                chunk_overlap=150
            )

        chunks.extend(splitter.split_documents([doc]))

    return chunks


def create_vector_store(chunks):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )

    return db


if __name__ == "__main__":
    documents = load_files()
    chunks = split_documents(documents)
    create_vector_store(chunks)

    print(f"Indexed {len(chunks)} chunks into ChromaDB")