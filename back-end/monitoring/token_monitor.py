from tiktoken import get_encoding
from prometheus_client import Counter, Gauge, Histogram
from langchain.callbacks import get_openai_callback
import logging
from typing import Dict, Any

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 핸들러가 없으면 추가
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Prometheus 메트릭 정의
TOKEN_USAGE = Counter(
    'openai_token_usage_total',
    'Total number of tokens used',
    ['model', 'operation']
)
TOKEN_COST = Counter(
    'openai_token_cost_total',
    'Total cost of tokens used in USD',
    ['model', 'operation']
)
RESPONSE_TIME = Histogram(
    'openai_response_time_seconds',
    'Response time for OpenAI API calls',
    ['model', 'operation']
)
CURRENT_TOKENS = Gauge(
    'openai_current_tokens',
    'Current number of tokens being used',
    ['model', 'operation']
)

class TokenMonitor:
    def __init__(self):
        self.encoding = get_encoding("cl100k_base")  # GPT-4, GPT-3.5-turbo용 인코딩
        logger.info("TokenMonitor initialized")
        
    def count_tokens(self, text: str) -> int:
        token_count = len(self.encoding.encode(text))
        logger.info(f"Counted {token_count} tokens in text")
        return token_count
    
    def track_usage(self, func):
        async def wrapper(*args, **kwargs):
            logger.info(f"Starting token usage tracking for function: {func.__name__}")
            with get_openai_callback() as cb:
                logger.info("OpenAI callback initialized")
                with RESPONSE_TIME.labels(model="gpt-3.5-turbo", operation=func.__name__).time():
                    result = await func(*args, **kwargs)
                    
                    # 토큰 사용량 기록
                    token_count = cb.total_tokens
                    prompt_tokens = cb.prompt_tokens
                    completion_tokens = cb.completion_tokens
                    cost = cb.total_cost
                    
                    # 상세 로깅
                    logger.info("="*50)
                    logger.info(f"Token Usage Report for {func.__name__}")
                    logger.info("="*50)
                    logger.info(f"Total Tokens Used: {token_count}")
                    logger.info(f"Prompt Tokens: {prompt_tokens}")
                    logger.info(f"Completion Tokens: {completion_tokens}")
                    logger.info(f"Total Cost: ${cost:.6f}")
                    logger.info("="*50)
                    
                    # Prometheus 메트릭 업데이트
                    logger.info("Updating Prometheus metrics...")
                    TOKEN_USAGE.labels(
                        model="gpt-3.5-turbo",
                        operation=func.__name__
                    ).inc(token_count)
                    
                    TOKEN_COST.labels(
                        model="gpt-3.5-turbo",
                        operation=func.__name__
                    ).inc(cost)
                    
                    CURRENT_TOKENS.labels(
                        model="gpt-3.5-turbo",
                        operation=func.__name__
                    ).set(token_count)
                    
                    logger.info("Token usage tracking completed")
                    return result
        return wrapper

# 싱글톤 인스턴스 생성
token_monitor = TokenMonitor() 