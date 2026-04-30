from flask import Flask, request, render_template
from flask.cli import load_dotenv

from weather_service import buscar_clima_por_cidade
from database import buscar_no_banco, salvar_historico, listar_historico


load_dotenv()

app = Flask(__name__)


def _montar_weather_do_banco(registro: dict) -> dict:
    return {
        'cidade'      : registro.get('cidade'),
        'data'        : registro.get('data'),
        'umidade'     : registro.get('umidade'),
        'vento'       : registro.get('vento'),
        'precipitacao': registro.get('precipitacao'),
        'temperatura' : None,
        'hora'        : None,
        'icon'        : '',
        'previsao'    : [{
            'temperatura_min': registro.get('temp_min'),
            'temperatura_max': registro.get('temp_max'),
        }],
        'fonte'       : 'banco',
    }


@app.route("/buscar-historico", methods=["GET"])
def buscar_historico():
    historico = listar_historico()
    return render_template(
        "index.html",
        weather=None,
        error=None,
        cidade='',
        fonte=None,
        historico=historico,
    )


@app.route("/", methods=["GET"])
def home():
    cidade    = request.args.get("cidade", '').strip()
    weather   = None
    error     = None
    fonte     = None
    historico = listar_historico()

    if cidade:
        registro = buscar_no_banco(cidade)

        if registro:
            weather = _montar_weather_do_banco(registro)
            fonte   = 'banco'
        else:
            resultado = buscar_clima_por_cidade(cidade)

            if resultado['error']:
                error = resultado['message']
            else:
                weather = resultado['data']
                fonte   = 'api'
                salvar_historico(weather)
                historico = listar_historico()

    return render_template(
        "index.html",
        weather=weather,
        error=error,
        cidade=cidade,
        fonte=fonte,
        historico=historico,
    )


if __name__ == "__main__":
    app.run(debug=True)