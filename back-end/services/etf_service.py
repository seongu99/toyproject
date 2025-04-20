import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from langchain_community.document_loaders import PyMuPDFLoader, DirectoryLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from schemas import FinancialStatus, CustomerProfile, ETFRecommendation
from config import *
import logging
import shutil
from datetime import datetime
from monitoring.token_monitor import token_monitor
from sentence_transformers import CrossEncoder  # Rerank 모델 추가

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETFVectorDB:
    def __init__(self):
        self.vector_db_path = os.path.join(BASE_DIR, "data", "vector_db")
        self.last_update = {}
        self.vectordb = None
        self.embeddings = None
        self.rerank_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')  # Rerank 모델 초기화
        self._initialize_embeddings()
        self._load_or_create_db()

    def _initialize_embeddings(self):
        """OpenAI Embeddings 초기화"""
        try:
            logger.info("OpenAI Embeddings 초기화 시작")
            self.embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=OPENAI_API_KEY
            )
            logger.info("OpenAI Embeddings 초기화 완료")
        except Exception as e:
            logger.error(f"Embeddings 초기화 실패: {str(e)}")
            raise

    def _load_or_create_db(self):
        """기존 DB 로드 또는 새로 생성"""
        try:
            if os.path.exists(self.vector_db_path):
                logger.info("기존 Vector DB 로드")
                self.vectordb = FAISS.load_local(
                    self.vector_db_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                self._load_last_update_times()
            else:
                logger.info("새로운 Vector DB 생성")
                self._create_initial_db()
        except Exception as e:
            logger.error(f"Vector DB 로드/생성 실패: {str(e)}")
            raise

    def _load_last_update_times(self):
        """마지막 업데이트 시간 로드"""
        try:
            update_file = os.path.join(self.vector_db_path, "last_update.json")
            if os.path.exists(update_file):
                with open(update_file, 'r') as f:
                    self.last_update = json.load(f)
        except Exception as e:
            logger.warning(f"마지막 업데이트 시간 로드 실패: {str(e)}")
            self.last_update = {}

    def _save_last_update_times(self):
        """마지막 업데이트 시간 저장"""
        try:
            update_file = os.path.join(self.vector_db_path, "last_update.json")
            with open(update_file, 'w') as f:
                json.dump(self.last_update, f)
        except Exception as e:
            logger.warning(f"마지막 업데이트 시간 저장 실패: {str(e)}")

    def _create_initial_db(self):
        """초기 Vector DB 생성"""
        try:
            documents = []
            
            # PDF 파일 로딩
            try:
                pdf_loader = DirectoryLoader(DOCS_PATH, glob="**/*.pdf", loader_cls=PyMuPDFLoader)
                pdf_docs = pdf_loader.load()
                documents.extend(pdf_docs)
                logger.info(f"PDF 문서 {len(pdf_docs)}개 로드 완료")
            except Exception as e:
                logger.warning(f"PDF 문서 로딩 중 오류 발생: {str(e)}")

            # CSV 파일 로딩
            try:
                csv_path = os.path.join(DOCS_PATH, "etf_info.csv")
                if os.path.exists(csv_path):
                    csv_docs = self._load_csv_documents(csv_path)
                    documents.extend(csv_docs)
                    logger.info(f"CSV 문서 {len(csv_docs)}개 로드 완료")
                else:
                    logger.warning(f"CSV 파일을 찾을 수 없음: {csv_path}")
            except Exception as e:
                logger.error(f"CSV 파일 로딩 중 오류 발생: {str(e)}")

            if not documents:
                raise Exception("로드된 문서가 없음")
                
            logger.info("문서 벡터화 시작")
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            texts = text_splitter.split_documents(documents)
            logger.info(f"문서 {len(texts)}개로 분할 완료")
            
            # 벡터 DB 생성
            logger.info("FAISS 벡터 DB 생성 시작")
            self.vectordb = FAISS.from_documents(texts, self.embeddings)
            logger.info("FAISS 벡터 DB 생성 완료")
            
            # 벡터 DB 저장
            logger.info("벡터 DB 저장 시작")
            self.vectordb.save_local(self.vector_db_path)
            logger.info("벡터 DB 저장 완료")
            
            # 마지막 업데이트 시간 저장
            self._save_last_update_times()
            
        except Exception as e:
            logger.error(f"Vector DB 생성 실패: {str(e)}")
            raise

    def _load_csv_documents(self, csv_path: str) -> List[Document]:
        """CSV 파일에서 Document 객체 생성"""
        try:
            documents = []
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():
                # ETF 정보를 텍스트로 변환
                content = f"""
                ETF 코드: {row['etf_code']}
                ETF 이름: {row['etf_name']}
                기초지수: {row['base_index_name']}
                상장일: {row['listing_date']}
                투자목적: {row['investment_object']}
                투자전략: {row['investment_strategy']}
                설명: {row['description']}
                위험도: {row['risk_level']}
                """
                
                # 메타데이터 설정
                metadata = {
                    'source': f"{row['etf_code']} - {row['etf_name']}",
                    'etf_code': row['etf_code'],
                    'etf_name': row['etf_name'],
                    'base_index_name': row['base_index_name'],
                    'listing_date': row['listing_date'],
                    'risk_level': row['risk_level'],  # 위험도 추가
                    'expense_ratio': row['expense_ratio']  # 수수료 추가
                }
                
                # Document 생성
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            
            logger.info(f"CSV에서 {len(documents)}개의 문서 생성 완료")
            return documents
            
        except Exception as e:
            logger.error(f"CSV 문서 변환 실패: {str(e)}")
            return []

    def update_etf_data(self, pdf_path: str) -> bool:
        """
        PDF 파일을 사용하여 ETF 데이터를 업데이트합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            logger.info(f"ETF 데이터 업데이트 시작: {pdf_path}")
            
            # PDF 파일 로드
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()
            
            if not documents:
                logger.warning(f"PDF 파일에서 문서를 로드할 수 없습니다: {pdf_path}")
                return False
            
            # 문서 분할
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            texts = text_splitter.split_documents(documents)
            
            # Vector DB 업데이트
            self.vectordb.add_documents(texts)
            
            # 업데이트 상태 저장
            self.vectordb.save_local(self.vector_db_path)
            self.last_update[pdf_path] = os.path.getmtime(pdf_path)
            self._save_last_update_times()
            
            logger.info(f"ETF 데이터 업데이트 완료: {len(texts)}개 문서 추가")
            return True
            
        except Exception as e:
            logger.error(f"ETF 데이터 업데이트 실패: {str(e)}")
            return False

def check_openai_api_key() -> bool:
    """OpenAI API 키의 유효성을 확인합니다."""
    try:
        # 간단한 테스트 쿼리를 통해 API 키 유효성 확인
        test_embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY
        )
        test_embeddings.embed_query("test")
        return True
    except Exception as e:
        logger.error(f"OpenAI API 키 확인 실패: {str(e)}")
        return False

# 전역 변수로 vector_db 인스턴스 생성
vector_db = ETFVectorDB()

# Initialize the vector DB manager
try:
    logger.info("ETF Vector DB 관리자 초기화 시작")
    vector_db_manager = ETFVectorDB()
    logger.info("ETF Vector DB 관리자 초기화 완료")
    
    # Initialize QA chain
    logger.info("ChatOpenAI 초기화 시작")
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY
    )
    logger.info("ChatOpenAI 초기화 완료")
    
    # Create a prompt template
    logger.info("프롬프트 템플릿 생성 시작")
    prompt_template = """다음 질문에 대해 자세히 답변해주세요:

    {context}

    질문: {question}
    답변:"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    logger.info("프롬프트 템플릿 생성 완료")
    
    # Initialize QA chain
    logger.info("QA 체인 초기화 시작")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db_manager.vectordb.as_retriever(
            search_kwargs={"k": 10}  # 상위 10개 문서 검색
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    logger.info("QA 체인 초기화 완료")
    
    logger.info("서비스 초기화 완료")
except Exception as e:
    logger.error(f"서비스 초기화 실패: {str(e)}")
    raise

@token_monitor.track_usage
async def recommend_etf(
    customer_id: str,
    risk_tolerance: str,
    age: int,
    financial_status: Dict[str, Any],
    etfs_owned: Optional[str] = None
) -> Dict[str, Any]:
    """
    고객 프로필에 기반한 ETF 추천을 생성합니다.
    
    Args:
        customer_id: 고객 ID
        risk_tolerance: 위험 감내도
        age: 나이
        financial_status: 재무 상태 (수입, 저축, 월 투자액)
        etfs_owned: 현재 보유 중인 ETF 목록 (선택적)
        
    Returns:
        Dict[str, Any]: ETF 추천 결과
    """
    try:
        # 위험 감내도와 월 투자액을 강조하는 쿼리 생성
        query = f"""
        고객님의 프로필을 기반으로 ETF를 추천해주세요.
        
        [중요] 위험 감내도: {risk_tolerance}
        [중요] 월 투자액: {financial_status.get('monthly_investment', 0):,}원
        
        추가 고객 정보:
        - 나이: {age}세
        - 월 수입: {financial_status.get('income', 0):,}원
        - 저축: {financial_status.get('savings', 0):,}원
        """
        
        if etfs_owned:
            query += f"\n현재 보유 ETF: {etfs_owned}"
        
        # 위험 감내도에 따른 가중치 부여
        risk_weights = {
            "낮음": 0.8,  # 낮은 위험 감내도는 더 보수적인 ETF에 가중치
            "중간": 0.5,
            "높음": 0.2   # 높은 위험 감내도는 더 공격적인 ETF에 가중치
        }
        
        # 월 투자액에 따른 가중치 부여
        monthly_investment = financial_status.get('monthly_investment', 0)
        investment_weights = {
            "낮음": 0.2,  # 낮은 투자액은 저비용 ETF에 가중치
            "중간": 0.5,
            "높음": 0.8   # 높은 투자액은 다양한 ETF에 가중치
        }
        
        # 투자액 구간 설정
        if monthly_investment < 500000:
            investment_level = "낮음"
        elif monthly_investment < 2000000:
            investment_level = "중간"
        else:
            investment_level = "높음"
        
        # Vector DB에서 관련 ETF 검색 (상위 5개)
        docs = vector_db.vectordb.similarity_search(query, k=5)
        
        if not docs:
            logger.warning(f"고객 ID {customer_id}에 대한 ETF 추천 결과가 없습니다.")
            return {
                "recommendations": [],
                "reasons": ["죄송합니다. 현재 고객님의 프로필에 맞는 ETF를 찾을 수 없습니다."]
            }
        
        # 위험 감내도와 투자액에 따른 가중치 적용
        weighted_docs = []
        for doc in docs:
            # ETF의 위험도와 고객의 위험 감내도 매칭
            etf_risk_level = doc.metadata.get('risk_level', '중간')
            risk_match = 1.0 if etf_risk_level == risk_tolerance else 0.5
            
            # ETF의 수수료와 투자액 매칭
            expense_ratio = float(doc.metadata.get('expense_ratio', 0))
            expense_match = 1.0 if expense_ratio < 0.5 else 0.5
            
            # 최종 가중치 계산
            weight = (
                risk_weights.get(risk_tolerance, 0.5) * risk_match +
                investment_weights.get(investment_level, 0.5) * expense_match
            ) / 2
            
            weighted_docs.append((doc, weight))
        
        # 가중치에 따라 정렬
        weighted_docs.sort(key=lambda x: x[1], reverse=True)
        docs = [doc for doc, _ in weighted_docs[:3]]  # 상위 3개 선택
        
        # OpenAI에 추천 요청
        etf_info = "\n".join([doc.page_content for doc in docs])
        prompt = f"""
        다음 고객 정보와 ETF 정보를 바탕으로 정확히 3개의 ETF를 추천해주세요.
        
        [중요] 고객의 위험 감내도: {risk_tolerance}
        [중요] 월 투자액: {financial_status.get('monthly_investment', 0):,}원
        
        추가 고객 정보:
        - 나이: {age}세
        - 월 수입: {financial_status.get('income', 0):,}원
        - 저축: {financial_status.get('savings', 0):,}원
        
        ETF 정보:
        {etf_info}
        
        다음 형식으로 정확히 응답해주세요. 3개의 ETF와 3개의 이유를 모두 포함해야 합니다:
        
        [추천 ETF]
        1. ETF 코드 - ETF 이름
        2. ETF 코드 - ETF 이름
        3. ETF 코드 - ETF 이름
        
        [추천 이유]
        1. 첫 번째 ETF의 추천 이유 (위험 감내도와 월 투자액을 고려하여 설명)
        2. 두 번째 ETF의 추천 이유 (위험 감내도와 월 투자액을 고려하여 설명)
        3. 세 번째 ETF의 추천 이유 (위험 감내도와 월 투자액을 고려하여 설명)
        
        중요: 정확히 3개의 ETF와 3개의 이유를 제공해주세요. 더 많거나 적으면 안됩니다.
        """
        
        # OpenAI API 호출
        response = await llm.ainvoke(prompt)
        content = response.content
        
        # 응답 파싱
        recommendations = []
        reasons = []
        
        # 응답을 줄 단위로 분리
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line == '[추천 ETF]':
                current_section = 'recommendations'
                continue
            elif line == '[추천 이유]':
                current_section = 'reasons'
                continue
            
            if current_section == 'recommendations' and line[0].isdigit():
                # "1. ETF 코드 - ETF 이름" 형식에서 실제 내용만 추출
                recommendation = line.split('.', 1)[1].strip()
                recommendations.append(recommendation)
            elif current_section == 'reasons' and line[0].isdigit():
                # "1. 추천 이유" 형식에서 실제 내용만 추출
                reason = line.split('.', 1)[1].strip()
                reasons.append(reason)
        
        # 정확히 3개의 추천과 이유가 있는지 확인
        if len(recommendations) != 3 or len(reasons) != 3:
            logger.warning(f"고객 ID {customer_id}에 대한 ETF 추천이 3개가 아닙니다. (추천: {len(recommendations)}, 이유: {len(reasons)})")
            # 부족한 경우 기본 추천 추가
            while len(recommendations) < 3:
                recommendations.append("추천 정보를 준비 중입니다.")
            while len(reasons) < 3:
                reasons.append("추천 이유를 준비 중입니다.")
        
        # 응답 구성
        response = {
            "recommendations": recommendations[:3],  # 최대 3개만 반환
            "reasons": reasons[:3]  # 최대 3개만 반환
        }
        
        # ETF 보유 고객의 경우 추가 정보 포함
        if etfs_owned:
            response.update({
                "portfolio_analysis": "현재 포트폴리오 분석 결과를 기반으로 한 리밸런싱이 필요합니다.",
                "rebalancing_needed": True,
                "rebalancing_suggestions": [
                    "현재 포트폴리오의 리스크를 줄이기 위해 일부 ETF를 매도하고 새로운 ETF를 매수하는 것을 고려해보세요.",
                    "추천된 ETF들을 현재 포트폴리오에 추가하여 분산 투자를 강화하세요."
                ]
            })
        
        return response
        
    except Exception as e:
        logger.error(f"ETF 추천 중 오류 발생: {str(e)}")
        raise

async def query_llm(prompt: str) -> str:
    """
    OpenAI API를 사용하여 LLM에 쿼리를 보내고 응답을 받습니다.
    
    Args:
        prompt: LLM에 보내는 프롬프트
        
    Returns:
        str: LLM의 응답
    """
    try:
        response = await llm.ainvoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"LLM 쿼리 중 오류 발생: {str(e)}")
        return "죄송합니다. 현재 서비스에 일시적인 문제가 있습니다. 잠시 후 다시 시도해주세요."

@token_monitor.track_usage
async def generate_rebalance_report(
    customer_id: str,
    etfs_owned: List[str],
    risk_tolerance: str,
    age: int,
    financial_status: Dict[str, Any]
) -> Dict[str, Any]:
    """
    고객의 ETF 포트폴리오에 대한 리밸런싱 리포트를 생성합니다.
    
    Args:
        customer_id: 고객 ID
        etfs_owned: 현재 보유 중인 ETF 목록
        risk_tolerance: 고객의 위험 감내도
        age: 고객의 나이
        financial_status: 고객의 재무 상태 (수입, 저축 등)
    
    Returns:
        Dict[str, Any]: 리밸런싱 리포트
    """
    try:
        # 고객 프로필 정보를 포함한 성과 분석 쿼리
        performance_query = f"""
        안녕하세요! {age}세의 고객님의 ETF 포트폴리오를 분석해드리겠습니다.
        
        고객님의 투자 성향:
        - 나이: {age}세
        - 위험 감내도: {risk_tolerance}
        - 재무 상태: 월 수입 {financial_status.get('income', 0)}만원, 저축 {financial_status.get('savings', 0)}만원
        
        현재 보유하신 ETF: {', '.join(etfs_owned)}
        
        다음 내용을 쉽고 친절하게 설명해주세요:
        1. 각 ETF의 최근 1년간 성과와 특징을 알기 쉽게 설명
        2. 현재 포트폴리오가 얼마나 잘 분산되어 있는지 설명
        3. 고객님의 상황(나이, 위험 감내도, 재무 상태)에 맞는지 평가
        
        설명 시 다음을 유의해주세요:
        - 전문 용어 대신 쉬운 말을 사용
        - 구어체로 친근하게 설명
        - 구체적인 예시를 들어 설명
        - 긍정적이고 격려하는 톤으로 작성
        """
        
        # 리밸런싱 필요성 분석 쿼리
        rebalancing_query = f"""
        안녕하세요! {age}세의 고객님의 포트폴리오 리밸런싱 필요성을 분석해드리겠습니다.
        
        고객님의 투자 성향:
        - 나이: {age}세
        - 위험 감내도: {risk_tolerance}
        - 재무 상태: 월 수입 {financial_status.get('income', 0)}만원, 저축 {financial_status.get('savings', 0)}만원
        
        현재 보유하신 ETF: {', '.join(etfs_owned)}
        
        다음 내용을 쉽고 친절하게 설명해주세요:
        1. 현재 포트폴리오의 리밸런싱이 필요한지 여부
        2. 리밸런싱이 필요한 이유 또는 필요하지 않은 이유
        3. 고객님의 상황에 맞는 조언
        
        설명 시 다음을 유의해주세요:
        - 전문 용어 대신 쉬운 말을 사용
        - 구어체로 친근하게 설명
        - 구체적인 예시를 들어 설명
        - 긍정적이고 격려하는 톤으로 작성
        """
        
        # 구체적인 리밸런싱 제안 쿼리
        suggestions_query = f"""
        안녕하세요! {age}세의 고객님께 포트폴리오 조정 방안을 제안드리겠습니다.
        
        고객님의 투자 성향:
        - 나이: {age}세
        - 위험 감내도: {risk_tolerance}
        - 재무 상태: 월 수입 {financial_status.get('income', 0)}만원, 저축 {financial_status.get('savings', 0)}만원
        
        현재 보유하신 ETF: {', '.join(etfs_owned)}
        
        다음 내용을 쉽고 친절하게 설명해주세요:
        1. 포트폴리오 조정 전략을 구체적으로 설명
        2. 각 ETF의 적정 비중을 제안
        3. 매수/매도가 필요한 경우 구체적인 제안
        4. 포트폴리오 조정 시기와 주기에 대한 권장사항
        
        설명 시 다음을 유의해주세요:
        - 전문 용어 대신 쉬운 말을 사용
        - 구어체로 친근하게 설명
        - 구체적인 예시를 들어 설명
        - 긍정적이고 격려하는 톤으로 작성
        """
        
        # 성과 분석
        performance_analysis = await query_llm(performance_query)
        
        # 리밸런싱 필요성 분석
        rebalancing_analysis = await query_llm(rebalancing_query)
        rebalancing_needed = "필요하다" in rebalancing_analysis or "권장된다" in rebalancing_analysis
        
        # 구체적인 리밸런싱 제안
        suggestions = await query_llm(suggestions_query)
        
        # 종합 리포트 생성
        report = f"""
        고객 ID: {customer_id}
        분석일자: {datetime.now().strftime('%Y-%m-%d')}
        
        1. 포트폴리오 성과 분석
        {performance_analysis}
        
        2. 리밸런싱 필요성
        {rebalancing_analysis}
        
        3. 리밸런싱 제안
        {suggestions}
        """
        
        return {
            "report": report,
            "performance_analysis": performance_analysis,
            "rebalancing_needed": rebalancing_needed,
            "suggestions": suggestions,
            "customer_id": customer_id,
            "analysis_date": datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        logger.error(f"리밸런싱 리포트 생성 중 오류 발생: {str(e)}")
        raise 