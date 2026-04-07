from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import json
import random
import csv
import io
import time

app = Flask(__name__, static_folder='static')
CORS(app)

# --- Carrega perguntas do arquivo JSON ---
with open('questoes.json', 'r', encoding='utf-8') as f:
    QUESTOES = json.load(f)

status_jogo = {
    "estado": "aguardando",    # 'aguardando' ou 'iniciado'
    "qtd_perguntas": 5,
    "tempo_limite": 180,       # segundos
    "timestamp_inicio": None,  # início da rodada (epoch)
    "questoes_rodada": []      # questões fixadas no início da rodada
}
pontuacao_alunos = {}
alunos_que_jogaram = set()
alunos_info = {}  # {usuario: {"status":..., "pontuacao":..., "respostas": [...], "tempo_gasto":...} }

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/admin')
def admin_home():
    return send_from_directory('static', 'admin.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/status_jogo')
def get_status_jogo():
    if status_jogo["estado"] == "iniciado":
        tempo_decorrido = int(time.time()) - status_jogo["timestamp_inicio"]
        tempo_restante = max(0, status_jogo["tempo_limite"] - tempo_decorrido)
        return jsonify({**status_jogo, "tempo_restante": tempo_restante})
    else:
        return jsonify(status_jogo)

@app.route('/api/admin/iniciar', methods=['POST'])
def iniciar_jogo():
    global status_jogo, pontuacao_alunos, alunos_que_jogaram, alunos_info
    dados = request.json
    qtd = int(dados.get('qtd_perguntas', 5))
    tempo = int(dados.get('tempo_limite', 180))  # segundos
    # Sorteia as questões UMA VEZ e fixa para toda a rodada
    n = min(qtd, len(QUESTOES))
    questoes_da_rodada = random.sample(QUESTOES, n)
    status_jogo = {
        "estado": "iniciado",
        "qtd_perguntas": n,
        "tempo_limite": tempo,
        "timestamp_inicio": int(time.time()),
        "questoes_rodada": questoes_da_rodada
    }
    pontuacao_alunos.clear()
    alunos_que_jogaram.clear()
    alunos_info.clear()
    return jsonify({"ok": True})

@app.route('/api/admin/resetar', methods=['POST'])
def resetar_jogo():
    global status_jogo, pontuacao_alunos, alunos_que_jogaram, alunos_info
    status_jogo = {
        "estado": "aguardando",
        "qtd_perguntas": 5,
        "tempo_limite": 180,
        "timestamp_inicio": None,
        "questoes_rodada": []
    }
    pontuacao_alunos.clear()
    alunos_que_jogaram.clear()
    alunos_info.clear()
    return jsonify({"ok": True})

@app.route('/api/perguntas', methods=['GET'])
def get_perguntas():
    usuario = request.args.get('usuario')
    if status_jogo["estado"] != "iniciado":
        return jsonify({"erro": "O jogo ainda não foi liberado pelo instrutor."}), 403
    if usuario and usuario in alunos_que_jogaram:
        return jsonify({"erro": "Você já jogou esta rodada. Aguarde o instrutor liberar uma nova rodada."}), 403
    # Usa o conjunto fixado na rodada; embaralha a ordem para cada aluno
    perguntas = list(status_jogo["questoes_rodada"])
    random.shuffle(perguntas)
    perguntas_sem_resposta = []
    for p in perguntas:
        p_copia = p.copy()
        p_copia.pop('resposta_correta', None)
        perguntas_sem_resposta.append(p_copia)
    return jsonify(perguntas_sem_resposta)


# ---------------------------------------------------------------------------
# Fórmula de pontuação
#   pontos_base  = peso * 100          (fácil=100, médio=200, difícil=300, muito=400)
#   pontos_bonus = round(peso * 50 * max(0, 1 - tempo_resposta / JANELA_BONUS))
#                  → bônus máximo se respondido em 0 s, zero após JANELA_BONUS s
# ---------------------------------------------------------------------------
JANELA_BONUS = 30  # segundos — após esse tempo o bônus de velocidade é 0

def calcular_pontos(peso, tempo_resposta_s, correta):
    if not correta:
        return 0, 0, 0
    peso = max(1, int(peso))
    t = max(0.0, min(float(tempo_resposta_s), 60.0))
    base   = peso * 100
    bonus  = round(peso * 50 * max(0.0, 1.0 - t / JANELA_BONUS))
    return base + bonus, base, bonus

@app.route('/api/verifica', methods=['POST'])
def verifica_resposta():
    dados = request.json
    id_questao = dados['id']
    resposta = dados['resposta']
    usuario = dados.get('usuario', 'anonimo')
    tempo_resposta = float(dados.get('tempo_resposta', JANELA_BONUS))  # segundos

    # BLOQUEIO: aluno só pode jogar uma vez por rodada!
    if usuario in alunos_que_jogaram:
        return jsonify({
            "correta": False,
            "explicacao": "Você já completou esta rodada. Aguarde o instrutor liberar uma nova rodada.",
            "pontuacao": pontuacao_alunos.get(usuario, 0),
            "fim": True
        })

    # BLOQUEIO: rodada acabou por tempo (servidor manda travar!)
    if status_jogo["estado"] == "iniciado":
        tempo_decorrido = int(time.time()) - status_jogo["timestamp_inicio"]
        if tempo_decorrido >= status_jogo["tempo_limite"]:
            return jsonify({
                "correta": False,
                "explicacao": "Tempo esgotado!",
                "pontuacao": pontuacao_alunos.get(usuario, 0),
                "fim": True
            })

    if id_questao == -1:
        # Consulta "dummy" do frontend para checar se pode jogar
        return jsonify({"correta": False, "fim": False})

    questao = next((q for q in QUESTOES if q['id'] == id_questao), None)
    if not questao:
        return jsonify({"ok": False, "msg": "Questão não encontrada."})

    correta = False
    if questao['tipo'] == 'multipla_escolha':
        correta = (resposta == questao['resposta_correta'])
    elif questao['tipo'] == 'associacao':
        correta = all(
            r.get('conceito') == g.get('conceito') and r.get('termo') == g.get('termo')
            for r, g in zip(resposta, questao['associacoes'])
        )
    elif questao['tipo'] == 'resposta_aberta':
        if isinstance(questao['resposta_correta'], list):
            correta = resposta.strip().lower() in [r.lower() for r in questao['resposta_correta']]
        else:
            correta = resposta.strip().lower() == questao['resposta_correta'].lower()

    if usuario not in pontuacao_alunos:
        pontuacao_alunos[usuario] = 0
    if usuario not in alunos_info:
        alunos_info[usuario] = {
            "status": "jogando",
            "pontuacao": 0,
            "respostas": [],
            "tempo_gasto": None
        }

    peso = questao.get('peso', 1)
    pontos_ganhos, pontos_base, pontos_bonus = calcular_pontos(peso, tempo_resposta, correta)

    if correta:
        pontuacao_alunos[usuario] += pontos_ganhos
        alunos_info[usuario]["pontuacao"] += pontos_ganhos

    alunos_info[usuario]["respostas"].append({
        "id": id_questao,
        "acertou": correta,
        "resposta": resposta,
        "tempo_resposta": round(tempo_resposta, 1),
        "pontos_ganhos": pontos_ganhos,
        "pontos_base": pontos_base,
        "pontos_bonus": pontos_bonus
    })

    return jsonify({
        "correta": correta,
        "explicacao": questao.get('explicacao', ""),
        "pontuacao": pontuacao_alunos[usuario],
        "pontos_ganhos": pontos_ganhos,
        "pontos_base": pontos_base,
        "pontos_bonus": pontos_bonus
    })

@app.route('/api/finalizar', methods=['POST'])
def finalizar_partida():
    dados = request.json
    usuario = dados.get('usuario', 'anonimo')
    tempo_final = int(time.time())
    alunos_que_jogaram.add(usuario)
    tempo_gasto = None
    if status_jogo.get("timestamp_inicio"):
        tempo_gasto = tempo_final - status_jogo["timestamp_inicio"]
    if usuario in alunos_info:
        alunos_info[usuario]["status"] = "finalizado"
        alunos_info[usuario]["tempo_gasto"] = tempo_gasto
    else:
        alunos_info[usuario] = {
            "status": "finalizado",
            "pontuacao": pontuacao_alunos.get(usuario, 0),
            "respostas": [],
            "tempo_gasto": tempo_gasto
        }
    return jsonify({"ok": True})

@app.route('/api/ranking', methods=['GET'])
def ranking():
    # Ranking agora leva em conta tempo para desempate
    lista = []
    for k, v in pontuacao_alunos.items():
        tempo_gasto = alunos_info[k].get("tempo_gasto", None) if k in alunos_info else None
        lista.append({
            "usuario": k,
            "pontuacao": v,
            "tempo_gasto": tempo_gasto
        })
    # Ordena: 1º por pontuação desc, 2º por tempo asc
    lista = sorted(lista, key=lambda x: (-x["pontuacao"], x["tempo_gasto"] if x["tempo_gasto"] is not None else 99999))
    return jsonify(lista)

@app.route('/api/admin/respostas')
def admin_respostas():
    """Retorna lista de todos os alunos, status, pontuação, tempo e respostas."""
    finalizados = []
    jogando = []
    for usuario, info in alunos_info.items():
        data = {
            "usuario": usuario,
            "status": info["status"],
            "pontuacao": info["pontuacao"],
            "tempo_gasto": info.get("tempo_gasto"),
            "respostas": info["respostas"]
        }
        if info["status"] == "finalizado":
            finalizados.append(data)
        else:
            jogando.append(data)
    return jsonify({"finalizados": finalizados, "jogando": jogando})

@app.route('/api/admin/exportar')
def admin_exportar():
    """Exporta resultados em CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Aluno', 'Status', 'Pontuação Total', 'Tempo Rodada (s)',
                     'ID Pergunta', 'Acertou', 'Tempo Resposta (s)',
                     'Pts Base', 'Pts Bônus', 'Pts Ganhos', 'Resposta'])
    for usuario, info in alunos_info.items():
        if info['respostas']:
            for resp in info['respostas']:
                writer.writerow([
                    usuario, info['status'], info['pontuacao'], info.get('tempo_gasto', ''),
                    resp.get("id"), resp.get("acertou"),
                    resp.get("tempo_resposta", ''), resp.get("pontos_base", ''),
                    resp.get("pontos_bonus", ''), resp.get("pontos_ganhos", ''),
                    str(resp.get("resposta"))
                ])
        else:
            writer.writerow([
                usuario, info['status'], info['pontuacao'], info.get('tempo_gasto', ''),
                '', '', '', '', '', '', ''
            ])
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=resultado_flashcards.csv"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)