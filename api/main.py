from bson import ObjectId, errors as bson_errors
import logging
import os
from functools import wraps
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from marshmallow import Schema, fields, ValidationError, validates, validate
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

from utils.ai_model import AIModelService
from utils.config import get_settings
from utils.mongo import get_mongo_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_nltk():
    resources = ['punkt_tab', 'punkt', 'stopwords', 'wordnet', 'omw-1.4']
    for resource in resources:
        try:
            nltk.download(resource, quiet=True)
        except Exception as e:
            logger.warning(f"Falha ao baixar '{resource}': {e}")

initialize_nltk()

def validate_non_empty_content(value):
    """Função de validação personalizada para conteúdo não vazio"""
    if not value.strip():
        raise ValidationError('Conteúdo não pode estar vazio')
    return value

class EmailRequestSchema(Schema):
    email = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=10000),
            validate_non_empty_content  
        ],
        error_messages={
            'required': 'Email é obrigatório',
            'invalid': 'Email deve ser uma string válida'
        }
    )
    content = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=10000),
            validate_non_empty_content  
        ],
        error_messages={
            'required': 'Conteúdo é obrigatório',
            'invalid': 'Conteúdo deve ser uma string válida'
        }
    )
    snippet = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=10000),
            validate_non_empty_content  
        ],
        error_messages={
            'required': 'Assunto é obrigatório',
            'invalid': 'Assunto deve ser uma string válida'
        }
    )
    
    @validates('content')
    def validate_content(self, value, **kwargs):
        if not value.strip():
            raise ValidationError('Conteúdo não pode estar vazio')
    def validate_snippet(self, value, **kwargs):
        if not value.strip():
            raise ValidationError('Assunto não pode estar vazio')
    def validate_email(self, value, **kwargs):
        if not value.strip():
            raise ValidationError('Email não pode estar vazio')

class EmailResponseSchema(Schema):
    category = fields.Str(required=True)
    confidence = fields.Float(required=True)
    suggested_reply = fields.Str(required=True)
    processed_content = fields.Str(allow_none=True)

class HealthResponseSchema(Schema):
    status = fields.Str(required=True)
    version = fields.Str(required=True)
    model_loaded = fields.Bool(required=True)

email_request_schema = EmailRequestSchema()
email_response_schema = EmailResponseSchema()
health_response_schema = HealthResponseSchema()

def create_app():
    app = Flask(__name__)
    settings = get_settings()
    app.config.update({
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'JSON_AS_ASCII': False,
        'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,  # 10MB
        'DEBUG': settings.debug_mode
    })
    CORS(app, origins=settings.allowed_hosts if settings.allowed_hosts != ["*"] else "*")
    return app

app = create_app()

@app.before_request
def before_request_mongo():
    from flask import g
    if not hasattr(g, 'mongo_client'):
        g.mongo_client = get_mongo_client()

@app.before_request
def before_request_mongo():
    from flask import g
    if not hasattr(g, 'mongo_client'):
        g.mongo_client = get_mongo_client()

_stop_words_cache = None
_lemmatizer_cache = None

def get_stop_words():
    global _stop_words_cache
    if _stop_words_cache is None:
        try:
            _stop_words_cache = set(stopwords.words('portuguese'))
        except Exception as e:
            logger.error(f"Erro ao carregar stopwords: {e}")
            _stop_words_cache = set()
    return _stop_words_cache

def get_lemmatizer():
    global _lemmatizer_cache
    if _lemmatizer_cache is None:
        _lemmatizer_cache = WordNetLemmatizer()
    return _lemmatizer_cache

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Erro de validação: {e.messages}")
            return jsonify({
                'error': 'Dados inválidos',
                'details': e.messages
            }), 400
        except Exception as e:
            logger.error(f"Erro interno: {e}", exc_info=True)
            return jsonify({
                'error': 'Erro interno do servidor',
                'message': 'Tente novamente em alguns momentos'
            }), 500
    return decorated_function

def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Requisição {request.method} {request.endpoint} de {request.remote_addr}")
        response = f(*args, **kwargs)
        logger.info(f"Resposta enviada com status {response[1] if isinstance(response, tuple) else 200}")
        return response
    return decorated_function

class TextPreprocessor:
    
    def __init__(self):
        self.stop_words = get_stop_words()
        self.lemmatizer = get_lemmatizer()
    
    def preprocess_text(self, text: str) -> str:
        try:
            if not text or not text.strip():
                return ""
            
            tokens = word_tokenize(text.lower())
            
            tokens = [
                token for token in tokens 
                if token.isalpha() and token not in self.stop_words
            ]
            
            tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
            
            return ' '.join(tokens)
            
        except Exception as e:
            logger.error(f"Erro no pré-processamento: {e}")
            return text.strip()

class EmailClassifier:
    
    def __init__(self):
        self.ai_service = AIModelService()
        self.preprocessor = TextPreprocessor()
    
    def classify_email(self, prompt: str) -> tuple[str, float]:
        """
        Classifica um email como produtivo ou improdutivo, usando um prompt estruturado.
        """
        try:
            processed_text = self.preprocessor.preprocess_text(prompt)
            if not processed_text:
                logger.warning("Texto vazio após pré-processamento")
                return "Improdutivo", 0.5
            result = self.ai_service.classify_text(processed_text)
            category = result.get('category', 'Improdutivo')
            confidence = result.get('confidence', 0.5)
            return category, confidence
        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return "Improdutivo", 0.3

class ReplyGenerator:
    
    @staticmethod
    def generate_reply(category: str, confidence: float) -> str:
        """
        Gera resposta sugerida baseada na categoria e confiança.
            
        Returns:
            Resposta sugerida
        """
        replies = {
            "Produtivo": [
                "Obrigado pelo seu email! Analisaremos sua solicitação e retornaremos em breve com mais informações. Estamos à disposição para esclarecer qualquer dúvida.",
                "Agradecemos seu contato. Sua mensagem foi recebida e será analisada pela nossa equipe. Retornaremos assim que possível.",
                "Prezado(a), recebemos sua mensagem e agradecemos o interesse. Nossa equipe fará a análise necessária e entrará em contato em breve."
            ],
            "Improdutivo": [
                "Agradecemos seu contato. Para melhor atendê-lo, solicitamos que forneça mais detalhes específicos sobre sua necessidade.",
                "Obrigado por entrar em contato. Para agilizar nosso atendimento, por favor, seja mais específico sobre o que precisa.",
                "Recebemos sua mensagem. Para oferecer a melhor assistência, precisamos de informações mais detalhadas sobre sua solicitação."
            ]
        }

        category_replies = replies.get(category, replies["Improdutivo"])
        
        if confidence > 0.8:
            return category_replies[0]
        elif confidence > 0.6:
            return category_replies[1]
        else:
            return category_replies[2] 

_email_classifier = None
_reply_generator = None

def get_email_classifier():
    global _email_classifier
    if _email_classifier is None:
        _email_classifier = EmailClassifier()
    return _email_classifier

def get_reply_generator():
    global _reply_generator
    if _reply_generator is None:
        _reply_generator = ReplyGenerator()
    return _reply_generator

@app.route('/health', methods=['GET'])
@handle_errors
@log_request
def health_check():
    try:
        classifier = get_email_classifier()
        model_status = classifier.ai_service.is_model_loaded()
        
        response_data = {
            'status': 'healthy' if model_status else 'degraded',
            'version': '1.0.0',
            'model_loaded': model_status
        }
        
        return jsonify(health_response_schema.dump(response_data))
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return jsonify({
            'error': 'Serviço temporariamente indisponível'
        }), 503
        
@app.route('/list', methods=['GET'])
@handle_errors
@log_request
def list_emails():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        if page < 1 or per_page < 1:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'Parâmetros de paginação inválidos'}), 400

    collection = g.mongo_client.quick_email.emails
    total = collection.count_documents({})
    emails_cursor = collection.find({"$or": [{"deleted": {"$exists": False}}, {"deleted": False}]}) \
        .skip((page - 1) * per_page) \
        .limit(per_page)
    emails = []
    for doc in emails_cursor:
        doc["_id"] = str(doc["_id"])
        emails.append(doc)

    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': total,
        'emails': emails
    })


import io
import PyPDF2

def extract_text_from_file(file_storage):
    filename = file_storage.filename.lower()
    if filename.endswith('.pdf'):
        try:
            pdf_reader = PyPDF2.PdfReader(file_storage.stream)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            logger.error(f"Erro ao ler PDF: {e}")
            return ""
    elif filename.endswith('.txt'):
        try:
            return file_storage.stream.read().decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Erro ao ler TXT: {e}")
            return ""
    else:
        return ""

@app.route('/analyzis', methods=['POST'])
@handle_errors
@log_request
def analyzis_email():
    """
    Analisa um email e retorna categoria e resposta sugerida, aceitando texto e arquivo (PDF ou TXT).
    O prompt enviado ao modelo inclui o assunto, o conteúdo do email e o texto extraído do arquivo.
    """
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        form = request.form
        file = request.files.get('file')
        email = form.get('email', '')
        snippet = form.get('subject', '')
        content = form.get('content', '')
        file_text = ""
        if file:
            file_text = extract_text_from_file(file)
    else:
        json_data = request.get_json(force=True)
        email = json_data.get('email', '')
        snippet = json_data.get('subject', '')
        content = json_data.get('content', '')
        file_text = ""

    if not email or not snippet or not (content and content.strip() or file_text and file_text.strip()):
        return jsonify({'error': 'Campos obrigatórios ausentes'}), 400

    prompt = f"""Assunto: {snippet}\n\nConteúdo do email:\n{content}\n"""
    if file_text and file_text.strip():
        prompt += f"\nTexto extraído do arquivo:\n{file_text}"

    logger.info(f"Analisando email (analyzis) com {len(prompt)} caracteres (content: {len(content or '')}, file: {len(file_text or '')})")
    classifier = get_email_classifier()
    category, confidence = classifier.classify_email(prompt)
    reply_generator = get_reply_generator()
    suggested_reply = reply_generator.generate_reply(category, confidence)
    settings = get_settings()
    processed_content = None
    if settings.debug_mode:
        processed_content = classifier.preprocessor.preprocess_text(prompt)

    g.mongo_client.quick_email.emails.insert_one({
        'email': email,
        'snippet': snippet,
        'content': content,
        'category': category,
        'confidence': confidence,
        'suggested_reply': suggested_reply
    })

    response_data = {
        'category': category,
        'confidence': confidence,
        'suggested_reply': suggested_reply,
        'processed_content': processed_content
    }
    return jsonify(email_response_schema.dump(response_data))

@app.route('/delete/<email_id>', methods=['POST'])
@handle_errors
@log_request
def soft_delete_email(email_id):
    """
    Soft delete de email: marca o campo 'deleted' como True.
    """
    collection = g.mongo_client.quick_email.emails
    try:
        try:
            obj_id = ObjectId(email_id)
        except (bson_errors.InvalidId, Exception):
            return jsonify({"error": "ID inválido"}), 400
        result = collection.update_one({"_id": obj_id}, {"$set": {"deleted": True}})
        if result.matched_count == 0:
            return jsonify({"error": "Email não encontrado"}), 404
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Erro ao fazer soft delete: {e}")
        return jsonify({"error": "Erro ao deletar email"}), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'name': 'Quick Email',
        'version': '1.0.0',
        'description': 'API para análise e classificação automática de emails',
        'endpoints': {
            'health': '/health',
            'analyze': '/analyze (POST)',
            'docs': '/docs'
        }
    })

@app.route('/docs', methods=['GET'])
def api_docs():
    return jsonify({
        'Email Analysis API': {
            'version': '1.0.0',
            'endpoints': {
                'GET /health': {
                    'description': 'Verifica saúde da aplicação',
                    'response': {
                        'status': 'healthy|degraded',
                        'version': '1.0.0',
                        'model_loaded': True
                    }
                },
                'POST /analyze': {
                    'description': 'Analisa email e retorna classificação',
                    'request': {
                        'content': 'Texto do email a ser analisado'
                    },
                    'response': {
                        'category': 'Produtivo|Improdutivo',
                        'confidence': 0.85,
                        'suggested_reply': 'Resposta sugerida...',
                        'processed_content': 'Texto processado (debug)'
                    }
                }
            }
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint não encontrado',
        'message': 'Verifique a URL e tente novamente'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Método não permitido',
        'message': f'Método {request.method} não é permitido para este endpoint'
    }), 405

@app.errorhandler(413)
def payload_too_large(error):
    return jsonify({
        'error': 'Payload muito grande',
        'message': 'O conteúdo enviado excede o limite permitido'
    }), 413

def run_app():
    settings = get_settings()
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 4000)),
        debug=settings.debug_mode,
        threaded=True
    )

if __name__ == '__main__':
    import time
    run_app()
