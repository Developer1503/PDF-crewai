"""Quick smoke-test for the VectorStoreManager."""
from utils.vector_store import VectorStoreManager

vsm = VectorStoreManager()
print("Backend:", vsm.backend_name)

dummy_text = " ".join(
    ["This is a test document about machine learning and neural networks."] * 100
)

fp, chunks = vsm.index_document("test_doc.pdf", dummy_text)
print(f"First index  -> fingerprint={fp[:12]}... chunks_added={chunks}")

fp2, chunks2 = vsm.index_document("test_doc.pdf", dummy_text)
print(f"Second index -> chunks_added={chunks2}  (should be 0 — deduplicated)")

results = vsm.search("machine learning", n_results=3, doc_fingerprint=fp)
top_score = results[0]["score"] if results else "N/A"
print(f"Search returned {len(results)} result(s), top score={top_score}")

vsm.delete_document(fp)
print("Cleanup done.")
print(vsm.get_stats())
