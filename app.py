import matplotlib
matplotlib.use('Agg')  # backend para gerar imagens sem precisar abrir janela
import matplotlib.pyplot as plt

from flask import Flask, render_template, request
import requests
from datetime import datetime
import os
import uuid

app = Flask(__name__)
API_KEY = os.environ.get("API_KEY")

times_disponiveis = {
    #premier legue

    "arsenal": 57,
    "aston villa": 58,
    "bournemouth": 1044,
    "brentford": 402,
    "brighton": 397,
    "chelsea": 61,
    "crystal palace": 354,
    "everton": 62,
    "fulham": 63,
    "liverpool": 64,
    "manchester city": 65,
    "manchester united": 66,
    "newcastle united": 67,
    "tottenham hotspur": 73,
    "west ham united": 563,
    "wolverhampton wanderers": 76,
    "leicester city": 338,

    #la liga
    "real madrid": 86,
    "barcelona": 81,
    "atletico madrid": 78,
    "sevilla": 559,
    "real betis": 90,
    "real sociedad": 92,
    "villarreal": 94,
    "athletic bilbao": 77,
    "valencia": 95,
    "girona": 298,
    "rayo vallecano": 89,
    "osasuna": 79,
    "las palmas": 275,

    # Serie A tim
    "juventus": 109,
    "inter de milão": 108,
    "milan": 98,
    "napoli": 113,
    "roma": 100,
    "lazio": 110,
    "atalanta": 102,
    "fiorentina": 99,
    "bologna": 103,
    "cagliari": 104,
    "verona": 450,
    "empoli": 445,

#bundesliga

    "bayern de munique": 5,
    "borussia dortmund": 4,
    "rb leipzig": 721,
    "bayer leverkusen": 3,
    "wolfsburg": 12,
    "eintracht frankfurt": 19,
    "freiburg": 18,
    "hoffenheim": 7211,
    "mainz 05": 15,
    "werder bremen": 11,
    "stuttgart": 16,
    "bochum": 36,
    "augsburg": 17,
    "union berlin": 28,

#ligue one

    "psg": 524,
    "marseille": 516,
    "lille": 521,
    "lyon": 523,
    "montpellier": 518,
    "nice": 522,
    "rennes": 529,
    "reims": 543,
    "nantes": 532,
    "strasbourg": 541,
    "lorient": 528,
    "clermont": 547,
    "toulouse": 531,
    "angers": 5325,

 # brasileirão

    "flamengo": 1837,
    "palmeiras": 1766,
    "são paulo": 1770,
    "corinthians": 1768,
    "grêmio": 1774,
    "internacional": 1775,
    "cruzeiro": 1771,
    "atlético mineiro": 1772,
    "bahia": 1776,
    "fortaleza": 1827,
    "botafogo": 1767,
    "vasco": 1773,
    "santos": 1777,
    "goiás": 1838,
    "cuiabá": 1879,
    "athletico paranaense": 1859,
    "bragantino": 1860,
    "américa mineiro": 1839,
    "coritiba": 1780,
    "juventude": 1769,
#adicionais
    "sporting": 498,
    "porto": 503,
    "benfica": 1903,

}

def carregar_jogos_csv(nome_time):
    arquivos = ["data/E0.csv", "data/F1.csv"]
    jogos_encontrados = []

    for arquivo in arquivos:
        try:
            df = pd.read_csv(arquivo)
            for _, row in df.iterrows():
                home = row.get("HomeTeam", "").lower()
                away = row.get("AwayTeam", "").lower()
                if nome_time in [home, away]:
                    resultado = {
                        "data": row["Date"],
                        "mandante": home,
                        "visitante": away,
                        "placar": f"{row.get('FTHG', '?')}x{row.get('FTAG', '?')}",
                        "resultado": row.get("FTR", "?")  # H, D ou A
                    }
                    jogos_encontrados.append(resultado)
        except Exception as e:
            print(f"Erro ao ler {arquivo}: {e}")
    
    return jogos_encontrados[:5] 

def ultimos_5_jogos_validos(matches, id_time):
    resultados = []
    rotulos = []

    for jogo in matches:
        score = jogo["score"]["fullTime"]
        if score["home"] is None or score["away"] is None:
            continue

        eh_casa = jogo["homeTeam"]["id"] == id_time
        gols_pro = score["home"] if eh_casa else score["away"]
        gols_contra = score["away"] if eh_casa else score["home"]
        adversario = jogo["awayTeam"]["name"] if eh_casa else jogo["homeTeam"]["name"]

        # Resultado numérico
        if gols_pro > gols_contra:
            resultado = 3
        elif gols_pro == gols_contra:
            resultado = 1
        else:
            resultado = 0

        resultados.append(resultado)
        rotulos.append(f"{gols_pro}x{gols_contra}\nvs {adversario}")

        if len(resultados) == 5:
            break

    return list(reversed(resultados)), list(reversed(rotulos))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nome_time1 = request.form["time1"].strip().lower()
        nome_time2 = request.form["time2"].strip().lower()

        if nome_time1 not in times_disponiveis or nome_time2 not in times_disponiveis:
            return render_template("index.html", erro="Um dos times não está na lista.", times=list(times_disponiveis.keys()))

        id1, id2 = times_disponiveis[nome_time1], times_disponiveis[nome_time2]
        headers = {"X-Auth-Token": API_KEY}

        # Pegar jogos dos dois times
        url1 = f"https://api.football-data.org/v4/teams/{id1}/matches?status=FINISHED&limit=100"
        url2 = f"https://api.football-data.org/v4/teams/{id2}/matches?status=FINISHED&limit=100"
        res1 = requests.get(url1, headers=headers)
        res2 = requests.get(url2, headers=headers)
        if res1.status_code != 200 or res2.status_code != 200:
            return "Erro ao buscar dados de um dos times."

        matches1 = res1.json().get("matches", [])
        matches2 = res2.json().get("matches", [])

        resultados1, rotulos1 = ultimos_5_jogos_validos(matches1, id1)
        resultados2, rotulos2 = ultimos_5_jogos_validos(matches2, id2)

        # Gerar gráfico
        plt.figure(figsize=(10, 5))
        x = list(range(5))

        plt.plot(x, resultados1, marker="o", linestyle="--", color="green", label=nome_time1.title())
        plt.plot(x, resultados2, marker="o", linestyle="--", color="blue", label=nome_time2.title())

        for i in x:
            plt.text(i, resultados1[i] + 0.1, rotulos1[i], ha='center', va='bottom', fontsize=8, color="green")
            plt.text(i, resultados2[i] - 0.3, rotulos2[i], ha='center', va='top', fontsize=8, color="blue")

        plt.title(f"Evolução dos últimos 5 jogos")
        plt.xticks(x, [f"J{i+1}" for i in x])
        plt.yticks([0, 1, 3], ["Derrota", "Empate", "Vitória"])
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        nome_arquivo = f"grafico_{uuid.uuid4().hex}.png"
        caminho = os.path.join("static", nome_arquivo)
        plt.savefig(caminho)
        plt.close()

        # Confrontos diretos
        url_h2h = f"https://api.football-data.org/v4/teams/{id1}/matches?status=FINISHED&limit=100"
        res_h2h = requests.get(url_h2h, headers=headers)
        matches = res_h2h.json().get("matches", [])
        h2h = [j for j in matches if j["homeTeam"]["id"] == id2 or j["awayTeam"]["id"] == id2][:10]

        stats = {
            "v1": 0, "v2": 0, "empates": 0, "over25": 0, "btts": 0, "confrontos": []
        }

        for jogo in h2h:
            score_home = jogo["score"]["fullTime"]["home"]
            score_away = jogo["score"]["fullTime"]["away"]
            total_gols = score_home + score_away
            resultado = jogo["score"]["winner"]
            if resultado == "DRAW":
                stats["empates"] += 1
            elif resultado == "HOME_TEAM" and jogo["homeTeam"]["id"] == id1:
                stats["v1"] += 1
            elif resultado == "AWAY_TEAM" and jogo["awayTeam"]["id"] == id1:
                stats["v1"] += 1
            else:
                stats["v2"] += 1
            if total_gols > 2.5:
                stats["over25"] += 1
            if score_home > 0 and score_away > 0:
                stats["btts"] += 1
            stats["confrontos"].append({
                "data": datetime.strptime(jogo["utcDate"], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y"),
                "home": jogo["homeTeam"]["name"],
                "away": jogo["awayTeam"]["name"],
                "score_home": score_home,
                "score_away": score_away
            })

        jogos_csv1 = carregar_jogos_csv(nome_time1)
        jogos_csv2 = carregar_jogos_csv(nome_time2)
        return render_template("resultado.html", time1=nome_time1.title(), time2=nome_time2.title(), stats=stats, grafico=nome_arquivo, jogos_csv1=jogos_csv1,
        jogos_csv2=jogos_csv2)

    return render_template("index.html", erro=None, times=list(times_disponiveis.keys()))

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
