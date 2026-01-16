from rag_docs.loader import load_docs, split_docs
from app.deps import get_vs

def main():
	docs = split_docs(load_docs("./data/docs"))
	get_vs().add_documents(docs)
	print(f"Indexed {len(docs)} chunks into Chroma.")

if __name__ == "__main__":
	main()