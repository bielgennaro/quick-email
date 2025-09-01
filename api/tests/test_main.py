import pytest
import json
from unittest.mock import patch, MagicMock

from api.main import create_app, get_email_classifier, get_reply_generator

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def mock_ai_service():
    with patch('app.AIModelService') as mock:
        mock_instance = MagicMock()
        mock_instance.classify_text.return_value = {
            'category': 'Produtivo',
            'confidence': 0.8,
            'raw_response': 'PRODUTIVO'
        }
        mock_instance.is_model_loaded.return_value = True
        mock.return_value = mock_instance
        yield mock_instance

class TestEmailAnalysis:
    
    def test_health_check(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'version' in data
        assert 'model_loaded' in data
    
    def test_index_route(self, client):
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'name' in data
        assert 'endpoints' in data
    
    def test_docs_route(self, client):
        response = client.get('/docs')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'Email Analysis API' in data
    
    def test_analyze_email_valid_request(self, client, mock_ai_service):
        test_email = {
            "content": "Gostaria de saber mais sobre seus produtos e preços. Podem me enviar um orçamento?"
        }
        
        response = client.post('/analyze', 
                             data=json.dumps(test_email),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'category' in data
        assert 'confidence' in data
        assert 'suggested_reply' in data
    
    def test_analyze_email_empty_content(self, client):
        test_email = {"content": ""}
        
        response = client.post('/analyze',
                             data=json.dumps(test_email),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_email_missing_content(self, client):
        test_email = {}
        
        response = client.post('/analyze',
                             data=json.dumps(test_email),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_email_too_long(self, client):
        long_content = "a" * 15000 
        test_email = {"content": long_content}
        
        response = client.post('/analyze',
                             data=json.dumps(test_email),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_email_whitespace_only(self, client):
        test_email = {"content": "   \n\t   "}
        
        response = client.post('/analyze',
                             data=json.dumps(test_email),
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_analyze_email_invalid_json(self, client):
        response = client.post('/analyze',
                             data="invalid json",
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_analyze_email_wrong_content_type(self, client):
        test_email = {"content": "Teste"}
        
        response = client.post('/analyze',
                             data=json.dumps(test_email),
                             content_type='text/plain')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Content-Type' in data['error']
    
    def test_not_found_error(self, client):

        response = client.get('/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_method_not_allowed(self, client):
        response = client.put('/analyze')
        assert response.status_code == 405
        
        data = json.loads(response.data)
        assert 'error' in data
    
    @pytest.mark.parametrize("test_input,expected_status", [
        ({"content": "Promoção imperdível! Clique aqui!"}, 200),
        ({"content": "Tenho interesse em seus serviços de consultoria"}, 200),
        ({"content": "Spam marketing newsletter cadastre-se"}, 200),
        ({"content": "Reunião projeto orçamento proposta comercial"""}, 200),
    ])
    def test_analyze_email_parametrized(self, client, mock_ai_service, test_input, expected_status):
        response = client.post('/analyze',
                             data=json.dumps(test_input),
                             content_type='application/json')
        assert response.status_code == expected_status