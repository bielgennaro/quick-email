import logging
import re
from typing import Dict, Optional
from functools import lru_cache

import pdfplumber
import os

from transformers import pipeline, Pipeline
from transformers.pipelines.base import PipelineException

from .config import get_settings

logger = logging.getLogger(__name__)

class AIModelService:
    def __init__(self):
        self.settings = get_settings()
        self._pipeline: Optional[Pipeline] = None
        self._load_model()

    def extract_text_from_attachment(self, file_path: str) -> str:
        """
        Extrai texto de arquivos PDF ou .txt.
        """
        if not os.path.isfile(file_path):
            return ""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            try:
                with pdfplumber.open(file_path) as pdf:
                    return "\n".join(page.extract_text() or "" for page in pdf.pages)
            except Exception as e:
                logger.error(f"Erro ao ler PDF: {e}")
                return ""
        elif ext == ".txt":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Erro ao ler TXT: {e}")
                return ""
        else:
            logger.warning(f"Tipo de anexo não suportado: {ext}")
            return ""
    
    def _load_model(self) -> None:
        try:
            logger.info(f"Carregando modelo: {self.settings.ai_model}")
            
            self._pipeline = pipeline(
                "text-generation",
                model=self.settings.ai_model,
                device=-1,
                return_full_text=True,
                pad_token_id=50256,
                max_new_tokens=350,
                temperature=0.3,
                do_sample=True,
                top_p=10,
                repetition_penalty=1.1  
            )
            
            logger.info("Modelo carregado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            self._pipeline = None
            raise RuntimeError(f"Falha ao carregar modelo de IA: {e}")
    
    def is_model_loaded(self) -> bool:
        return self._pipeline is not None
    
    def _build_response_prompt(self, email_text: str, attachment_text: str = "") -> str:
        """
        Constrói o prompt para geração de resposta ao email considerando anexos.
        """
        base_prompt = (
            "Você é um assistente de e-mails. Leia atentamente o conteúdo do e-mail e dos anexos (se houver). "
            "Gere uma resposta clara, objetiva e útil, considerando o contexto e o objetivo do remetente. "
            "Se o anexo contiver informações relevantes, utilize-as para enriquecer sua resposta. "
            "Se não for possível responder, peça mais informações de forma educada.\n"
        )
        prompt = f"{base_prompt}\n\nTexto do e-mail:\n\"{email_text}\"\n"
        if attachment_text:
            prompt += f"\nConteúdo do anexo:\n\"{attachment_text[:1500]}\"\n"  # Limita tamanho do anexo
        prompt += "\nResposta: "
        return prompt
    def generate_email_response(self, email_text: str, attachment_path: Optional[str] = None) -> Dict[str, any]:
        """
        Gera uma resposta automática ao e-mail considerando o texto e o anexo (PDF ou .txt).
        """
        if not self.is_model_loaded():
            raise RuntimeError("Modelo de IA não está carregado")
        if not email_text or not email_text.strip():
            logger.warning("Texto vazio fornecido para resposta")
            return {
                'response': 'Não foi possível gerar uma resposta pois o texto do e-mail está vazio.',
                'raw_response': '',
                'used_attachment': False
            }
        attachment_text = ""
        used_attachment = False
        if attachment_path:
            attachment_text = self.extract_text_from_attachment(attachment_path)
            used_attachment = bool(attachment_text.strip())
        try:
            prompt = self._build_response_prompt(email_text, attachment_text)
            if len(prompt) > 2000:
                logger.warning("Prompt muito longo, truncando...")
                prompt = prompt[:2000] + "..."
            logger.debug(f"Enviando prompt para modelo: {prompt[:100]}...")
            result = self._pipeline(
                prompt,
                max_new_tokens=200,
                num_return_sequences=1,
                temperature=0.3,
                pad_token_id=self._pipeline.tokenizer.eos_token_id
            )
            if not result or len(result) == 0:
                raise PipelineException("Modelo retornou resultado vazio")
            raw_response = result[0].get('generated_text', '').strip()
            # Remove o prompt do início da resposta, se presente
            response = raw_response[len(prompt):].strip() if raw_response.startswith(prompt) else raw_response
            logger.debug(f"Resposta do modelo: {response}")
            return {
                'response': response,
                'raw_response': raw_response,
                'used_attachment': used_attachment
            }
        except Exception as e:
            logger.error(f"Erro na geração de resposta com IA: {e}")
            return self._fallback_response(email_text, attachment_text)

    def _fallback_response(self, email_text: str, attachment_text: str = "") -> Dict[str, any]:
        """
        Geração de resposta de fallback usando heurísticas simples.
        """
        logger.info("Usando resposta de fallback")
        if attachment_text:
            return {
                'response': 'Recebemos seu e-mail e o anexo. Em breve retornaremos com uma resposta detalhada.',
                'raw_response': '',
                'used_attachment': True
            }
        else:
            return {
                'response': 'Recebemos seu e-mail. Em breve retornaremos com uma resposta.',
                'raw_response': '',
                'used_attachment': False
            }
    
    def _extract_classification(self, response_text: str) -> tuple[str, float]:
        """
        Extrai a classificação e confiança da resposta do modelo.
        
        Args:
            response_text: Texto de resposta do modelo
            
        Returns:
            Tupla com (categoria, confiança)
        """
        response_text = response_text.upper().strip()
        
        produtivo_patterns = [
            r'PRODUTIVO',
            r'PRODUCTIVE',
            r'POSITIVO',
            r'ÚTIL',
            r'RELEVANTE'
        ]
        
        improdutivo_patterns = [
            r'IMPRODUTIVO',
            r'UNPRODUCTIVE', 
            r'NEGATIVO',
            r'SPAM',
            r'IRRELEVANTE'
        ]
        
        produtivo_score = sum(1 for pattern in produtivo_patterns if re.search(pattern, response_text))
        improdutivo_score = sum(1 for pattern in improdutivo_patterns if re.search(pattern, response_text))
        
        if produtivo_score > improdutivo_score:
            confidence = min(0.9, 0.6 + (produtivo_score * 0.1))
            return "Produtivo", confidence
        elif improdutivo_score > produtivo_score:
            confidence = min(0.9, 0.6 + (improdutivo_score * 0.1))
            return "Improdutivo", confidence
        else:
            if any(word in response_text.lower() for word in ['pergunta', 'solicitação', 'interesse', 'comprar', 'preço']):
                return "Produtivo", 0.5
            else:
                return "Improdutivo", 0.5
    
    def classify_text(self, text: str) -> Dict[str, any]:
        if not self.is_model_loaded():
            raise RuntimeError("Modelo de IA não está carregado")
        
        if not text or not text.strip():
            logger.warning("Texto vazio fornecido para classificação")
            return {
                'category': 'Improdutivo',
                'confidence': 0.3,
                'raw_response': 'Texto vazio'
            }
        
        try:
            prompt = self._build_classification_prompt(text)
            
            if len(prompt) > 2000:
                logger.warning("Prompt muito longo, truncando...")
                prompt = prompt[:2000] + "..."
            
            logger.debug(f"Enviando prompt para modelo: {prompt[:100]}...")
            
            result = self._pipeline(
                prompt,
                max_new_tokens=20,
                num_return_sequences=1,
                temperature=0.3,
                pad_token_id=self._pipeline.tokenizer.eos_token_id
            )
            
            if not result or len(result) == 0:
                raise PipelineException("Modelo retornou resultado vazio")
            
            raw_response = result[0].get('generated_text', '').strip()
            logger.debug(f"Resposta do modelo: {raw_response}")
            
            category, confidence = self._extract_classification(raw_response)
            
            return {
                'category': category,
                'confidence': confidence,
                'raw_response': raw_response
            }
            
        except Exception as e:
            logger.error(f"Erro na classificação com IA: {e}")
            
            return self._fallback_classification(text)
    
    def _fallback_classification(self, text: str) -> Dict[str, any]:
        """
        Classificação de fallback usando heurísticas simples.
            
        Returns:
            Dicionário com classificação de fallback
        """
        logger.info("Usando classificação de fallback")
        
        text_lower = text.lower()
        
        productive_keywords = [
            'pergunta', 'dúvida', 'informação', 'orçamento', 'preço',
            'comprar', 'adquirir', 'contratar', 'serviço', 'produto',
            'reunião', 'agenda', 'proposta', 'projeto', 'colaboração'
        ]
        
        unproductive_keywords = [
            'promoção', 'desconto', 'oferta', 'grátis', 'ganhar',
            'clique', 'cadastre', 'newsletter', 'spam', 'marketing'
        ]
        
        productive_score = sum(1 for word in productive_keywords if word in text_lower)
        unproductive_score = sum(1 for word in unproductive_keywords if word in text_lower)
        
        if productive_score > unproductive_score:
            return {
                'category': 'Produtivo',
                'confidence': min(0.7, 0.4 + (productive_score * 0.1)),
                'raw_response': 'Classificação por fallback (heurística)'
            }
        else:
            return {
                'category': 'Improdutivo', 
                'confidence': min(0.7, 0.4 + (unproductive_score * 0.1)) if unproductive_score > 0 else 0.3,
                'raw_response': 'Classificação por fallback (heurística)'
            }
    
    def reload_model(self) -> None:
        logger.info("Recarregando modelo de IA...")
        self._pipeline = None
        self._load_model()
    
    def __del__(self):
        if self._pipeline:
            del self._pipeline
