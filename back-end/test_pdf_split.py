import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import DOCS_PATH

def test_pdf_splitting():
    # PDF 파일 경로
    pdf_path = os.path.join(DOCS_PATH, "간이투자설명서_신한SOL미국AI반도체칩메이커증권상장지수투자신탁[주식](2025년02월21일).pdf")
    
    # PDF 로드
    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()
    
    print(f"\n=== PDF 파일 정보 ===")
    print(f"문서 수: {len(documents)}")
    print(f"첫 번째 문서 길이: {len(documents[0].page_content)}")
    print(f"첫 번째 문서 내용 (처음 500자):")
    print(documents[0].page_content[:500])
    
    # 텍스트 분할
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    texts = text_splitter.split_documents(documents)
    
    print(f"\n=== 분할 결과 ===")
    print(f"총 청크 수: {len(texts)}")
    
    # 첫 3개 청크 출력
    for i, text in enumerate(texts[:3]):
        print(f"\n--- 청크 {i+1} ---")
        print(f"길이: {len(text.page_content)}")
        print(f"내용: {text.page_content}")
        print(f"메타데이터: {text.metadata}")

if __name__ == "__main__":
    test_pdf_splitting() 