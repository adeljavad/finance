import os
import json
from typing import List, Dict, Any, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

# مسیر پیش‌فرض برای ذخیره‌سازی داده‌های RAG
CHROMA_DIR = os.path.join(os.getcwd(), "data", "chroma")

# تلاش برای استفاده از تنظیمات Django اگر موجود باشد
try:
    from django.conf import settings
    CHROMA_DIR = getattr(settings, 'CHROMA_DIR', CHROMA_DIR)
except ImportError:
    pass
except Exception as e:
    logger.warning(f"خطا در بارگیری تنظیمات Django: {e}")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ChromaDB not available: {e}")
    CHROMA_AVAILABLE = False

class StableRAGEngine:
    """
    موتور RAG پایدار با fallback خودکار
    """

    def __init__(self, chroma_dir: str = CHROMA_DIR):
        self.chroma_dir = chroma_dir
        os.makedirs(chroma_dir, exist_ok=True)
        
        if CHROMA_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(path=chroma_dir)
                self.collection = self._get_or_create_collection()
                self.use_chroma = True
                logger.info("ChromaDB initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self.use_chroma = False
                self._init_fallback()
        else:
            self.use_chroma = False
            self._init_fallback()

    def _get_or_create_collection(self):
        """ایجاد یا بازیابی collection"""
        try:
            return self.client.get_collection("finance_rag")
        except Exception:
            return self.client.create_collection(
                name="finance_rag",
                metadata={"description": "سیستم RAG اسناد مالی"}
            )

    def _init_fallback(self):
        """راه‌اندازی سیستم fallback"""
        logger.info("Using fallback storage system")
        self.documents = []
        self.fallback_file = os.path.join(self.chroma_dir, "fallback_documents.json")
        self._load_fallback_documents()

    def _load_fallback_documents(self):
        """لود اسناد از فایل fallback"""
        try:
            if os.path.exists(self.fallback_file):
                with open(self.fallback_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
        except Exception as e:
            logger.error(f"Error loading fallback documents: {e}")
            self.documents = []

    def _save_fallback_documents(self):
        """ذخیره اسناد در فایل fallback"""
        try:
            with open(self.fallback_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving fallback documents: {e}")

    def ingest_documents(self, docs: List[Dict[str, Any]]):
        """افزودن اسناد به سیستم"""
        if not docs:
            return

        texts = []
        ids = []
        metadatas = []
        
        for doc in docs:
            if not doc.get("text") or not doc.get("text").strip():
                continue
                
            texts.append(doc["text"])
            ids.append(doc.get("id", f"doc_{uuid.uuid4().hex[:8]}"))
            metadatas.append(doc.get("metadata", {}))
        
        if not texts:
            return

        try:
            if self.use_chroma:
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )
            else:
                # استفاده از fallback
                for i, text in enumerate(texts):
                    self.documents.append({
                        'id': ids[i],
                        'text': text,
                        'metadata': metadatas[i]
                    })
                self._save_fallback_documents()
            
            logger.info(f"{len(texts)} documents added successfully")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            # Fallback به سیستم ساده
            if self.use_chroma:
                logger.info("Switching to fallback system")
                self.use_chroma = False
                self._init_fallback()
                self.ingest_documents(docs)

    def ingest_pdf_text(self, title: str, text: str, metadata: Optional[Dict] = None):
        """افزودن متن PDF به سیستم"""
        if not text or not text.strip():
            return
            
        doc_metadata = {
            "type": "pdf",
            "title": title,
            "source": "pdf_upload",
            **(metadata or {})
        }
        
        self.ingest_documents([{
            "id": f"pdf_{title}_{uuid.uuid4().hex[:6]}",
            "text": text,
            "metadata": doc_metadata
        }])

    def search(self, query: str, k: int = 4) -> str:
        """جستجو در اسناد"""
        if not query or not query.strip():
            return "لطفاً یک سوال معتبر وارد کنید."

        try:
            if self.use_chroma:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=k
                )
                
                if results['documents'] and results['documents'][0]:
                    documents = results['documents'][0]
                    context = "\n\n".join([f"📄 {doc}" for doc in documents[:2]])
                    return context
                else:
                    return "پاسخ مرتبطی در اسناد یافت نشد."
            else:
                # جستجوی fallback
                return self._fallback_search(query, k)
                
        except Exception as e:
            logger.error(f"Error in search: {e}")
            if self.use_chroma:
                # سوئیچ به fallback
                self.use_chroma = False
                self._init_fallback()
                return self.search(query, k)
            return f"خطا در پردازش جستجو: {str(e)}"

    def _fallback_search(self, query: str, k: int) -> str:
        """جستجوی fallback ساده"""
        if not self.documents:
            return "هنوز هیچ سندی اضافه نشده است."
        
        query_words = set(query.lower().split())
        scored_docs = []
        
        for doc in self.documents:
            text = doc['text'].lower()
            common_words = query_words.intersection(set(text.split()))
            score = len(common_words)
            
            if score > 0:
                scored_docs.append((score, doc['text']))
        
        scored_docs.sort(reverse=True)
        
        if scored_docs:
            best_results = [text for _, text in scored_docs[:k]]
            return "\n\n".join([f"📄 {text}" for text in best_results])
        else:
            return "هیچ سند مرتبطی یافت نشد."

    def get_collection_info(self) -> Dict[str, Any]:
        """دریافت اطلاعات سیستم"""
        try:
            if self.use_chroma:
                count = self.collection.count()
                return {
                    "total_documents": count,
                    "chroma_path": self.chroma_dir,
                    "status": "active",
                    "engine": "chromadb"
                }
            else:
                return {
                    "total_documents": len(self.documents),
                    "data_path": self.chroma_dir,
                    "status": "active", 
                    "engine": "fallback"
                }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error",
                "engine": "unknown"
            }
