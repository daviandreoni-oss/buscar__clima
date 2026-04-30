from datetime import datetime, timedelta
import os
import requests


def fahrenheit_to_celsius(temp):
    if temp is not None:
        celcius = (temp - 32) * 5.0 / 9.0
        return round(celcius, 2)
    return None


def mph_to_kmph(v_mph):
    if v_mph is not None:
        v_kmph = v_mph * 1.609
        return round(v_kmph, 2)
    return None


def validar_nome_cidade(cidade):
    if not cidade or not isinstance(cidade, str):
        return 'O nome da cidade é obrigatório.'
    if len(cidade.strip()) < 2:
        return 'O nome da cidade deve conter pelo menos 2 caracteres.'
    return None


def trasformar_dados_clima(dado_clima):
    clima_atual = dado_clima.get('currentConditions', {})
    dias = dado_clima.get('days', [])[:7]

    data_atual = datetime.now().strftime('%Y-%m-%d')

    clima_formatado = {
        'data': data_atual,
        'cidade': dado_clima.get('resolvedAddress', dado_clima.get('address', 'Desconhecido')),
        'hora': clima_atual.get('datetime'),
        'temperatura': fahrenheit_to_celsius(clima_atual.get('temp')),
        'precipitacao': clima_atual.get('precip') or 0,
        'umidade': clima_atual.get('humidity'),
        'vento': mph_to_kmph(clima_atual.get('windspeed')),
        'icon': clima_atual.get('icon', ''),
        'previsao': []
    }

    for dia in dias:
        dia_processado = {
            'data': datetime.strptime(dia.get('datetime'), '%Y-%m-%d').strftime('%d/%m/%Y'),
            'temperatura_max': fahrenheit_to_celsius(dia.get('tempmax')),
            'temperatura_min': fahrenheit_to_celsius(dia.get('tempmin')),
            'umidade': dia.get('humidity'),
            'vento': mph_to_kmph(dia.get('windspeed')),
            'precipitacao': dia.get('precip') or 0,
            'icon': dia.get('icon', '')
        }
        clima_formatado['previsao'].append(dia_processado)

    return clima_formatado


def buscar_clima_por_cidade(cidade):
    msg_erro = validar_nome_cidade(cidade)
    if msg_erro:
        return {'error': True, 'message': msg_erro, 'status': 400}

    base_url = os.getenv('BASE_URL_VISUAL_CROSSING')
    api_key = os.getenv('VISUAL_CROSSING_API_KEY')

    if not base_url or not api_key:
        return {'error': True, 'message': 'Configurações de API ausentes.', 'status': 500}

    data_inicio = datetime.now().strftime('%Y-%m-%d')
    data_fim = (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')

    url = f"{base_url}{cidade}/{data_inicio}/{data_fim}?key={api_key}&unitGroup=us&include=days,current"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            return {
                'error': True,
                'message': f"Cidade '{cidade}' não encontrada.",
                'status': 404
            }

        response.raise_for_status()
        dados_clima = response.json()

        dados_transformados = trasformar_dados_clima(dados_clima)
        return {
            'error': False,
            'data': dados_transformados,
            'status': 200
        }

    except requests.exceptions.Timeout:
        return {'error': True, 'message': 'Tempo limite da requisição excedido.', 'status': 504}

    except requests.exceptions.RequestException as ex:
        return {'error': True, 'message': f'Erro ao conectar com o serviço de clima: {str(ex)}', 'status': 502}

    except Exception as ex:
        return {'error': True, 'message': f'Erro inesperado: {str(ex)}', 'status': 500}