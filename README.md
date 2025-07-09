# flashcards_ai_test
Sistema gamificado de flashcards para ensino, com painel de professor, ranking, timer, pontuação dinâmica e geração fácil de questões por JSON.
## **1. requirements.txt**

Inclui os pacotes mínimos para rodar o projeto em qualquer ambiente Python 3.8+.

```
flask
flask-cors
```

Se quiser fixar versões mais seguras/testadas (opcional):

```
flask==3.0.3
flask-cors==4.0.1
```

---

## **2. README.md (para o GitHub)**

````markdown
# Flashcards IA - Sistema de Quiz Gamificado

Este é um sistema de jogo de flashcards gamificado para uso em sala de aula, com backend em Flask/Python e frontend HTML/CSS/JS, pensado para fácil uso em rede local (acesso via navegador, sem necessidade de instalação de apps).

## Funcionalidades

- Professores criam rodadas de quiz (definindo número de questões e tempo limite)
- Alunos acessam pelo navegador, participam apenas uma vez por rodada
- Cronômetro ao vivo e controle automático do tempo
- Pontuação automática e desempate por tempo de conclusão
- Ranking e desempenho em tempo real
- Painel do professor com detalhes de cada aluno, exportação em CSV e gráficos dinâmicos (via Chart.js e TailwindCSS)
- Pronto para rodar localmente, em laboratório, rede de escola, universidade ou pequenos eventos

## Instalação

1. **Clone o repositório:**

```bash
git clone https://github.com/kramires/flashcards_ai_test.git
cd flashcards-ia
````

2. **Crie o ambiente virtual e ative:**

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

4. **Coloque suas perguntas no arquivo `questoes.json`**
   (Formato de exemplo disponível no repositório.)

5. **Rode o servidor:**

```bash
python app.py
```

Acesse via navegador:

* **Professor:** `http://SEU_IP_LOCAL:8080/admin`
* **Aluno:** `http://SEU_IP_LOCAL:8080/`

## Estrutura dos arquivos

```
flashcards-ia/
├── app.py               # Backend Flask
├── requirements.txt     # Dependências Python
├── questoes.json        # Banco de perguntas
└── static/
    ├── index.html       # Interface do aluno
    └── admin.html       # Painel do professor
```

## Personalização

* Para trocar a senha do professor, altere a constante `SENHA` nos arquivos HTML.
* Para editar perguntas, use o arquivo `questoes.json`.
* O visual pode ser customizado facilmente com TailwindCSS.

## Segurança

* Não recomendado expor para a internet pública sem firewall/controle de acesso.
* Ideal para uso local em laboratórios, ambientes de ensino ou eventos.

---

````markdown
## Como editar as questões do quiz

O arquivo `questoes.json` contém todas as perguntas usadas no sistema.  
**Você pode alterar, adicionar ou remover questões livremente**, desde que mantenha o formato JSON original.

Cada questão pode ser do tipo:

- **Multipla escolha**  
- **Associação**
- **Resposta aberta** (palavra ou termo único)

Exemplo de formato de uma questão de múltipla escolha:

```json
{
  "id": 1,
  "pergunta": "Qual a capital do Brasil?",
  "tipo": "multipla_escolha",
  "opcoes": [
    "Rio de Janeiro",
    "Brasília",
    "São Paulo",
    "Belo Horizonte"
  ],
  "resposta_correta": 1,
  "dificuldade": "facil",
  "peso": 1,
  "explicacao": "Brasília é a capital do Brasil."
}
````

> **Dica:** Use IDs únicos e atualize o campo `resposta_correta` para o índice correto da opção.

---

### **Gerando perguntas automaticamente com IA**

Você pode gerar um novo arquivo de perguntas para qualquer assunto com a ajuda de ChatGPT, Copilot ou outra IA, usando o prompt abaixo:

```
Gere 10 questões no formato JSON para o seguinte tema: [INCLUA O ASSUNTO AQUI].
Use apenas os tipos 'multipla_escolha', 'associacao' ou 'resposta_aberta'.
Cada questão deve seguir exatamente o seguinte formato:

{
  "id": (número sequencial único),
  "pergunta": "...",
  "tipo": "multipla_escolha" ou "associacao" ou "resposta_aberta",
  "opcoes": [ ... ],                  # Apenas para múltipla escolha
  "associacoes": [ { "termo": "", "conceito": "" }, ... ], # Apenas para associação
  "resposta_correta": (índice ou valor correto),           # índice para múltipla escolha, lista ou string para aberta
  "dificuldade": "facil" | "media" | "dificil",
  "peso": (número inteiro, default 1),
  "explicacao": "..."
}

Não adicione comentários, apenas a lista JSON válida. O arquivo deve ser um array de questões.
```

Exemplo de uso:

```
Gere 10 questões no formato JSON para o tema: Fundamentos de Machine Learning.
[Siga o formato acima]
```

Depois, basta substituir o conteúdo do arquivo `questoes.json` por este novo conjunto, mantendo a estrutura.

---

**Importante:**

* Sempre valide o JSON antes de usar (você pode usar ferramentas online como [jsonlint.com](https://jsonlint.com/)).
* O sistema lê o arquivo automaticamente ao iniciar o servidor.
