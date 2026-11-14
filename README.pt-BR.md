# Crewcraft

*English: [README.md](README.md)*

**Um plugin do Claude Code que pergunta antes de construir, mostra o visual antes de programar e conversa no seu nível. Uma equipe de cargos especialistas está planejada.**

> Estado: inicial (v0.1.0). Cinco skills, uma equipe de nove agentes, um portão de liberação e um escritório pixel opcional funcionam hoje. A pesquisa do projeto (concorrentes, ferramentas, documentação atual) está planejada e **não** faz parte desta versão.

## Por quê

Peça "uma calculadora" a uma IA e você recebe a ideia **dela** de calculadora. Você corrige, ela refaz, e você se frustra. O Crewcraft inverte isso: antes de construir, ele descobre o que **você** quer dizer, mostra as opções que você não sabia que existiam e deixa você aprovar o visual.

![Uma conversa curta: o pedido "quero uma calculadora para Linux" recebe uma pergunta com cinco tipos de calculadora, e não um programa](docs/img/conversa.png)

## O que tem na 0.1.0

| Peça | O que faz |
|---|---|
| `conversa` | Conversa primeiro. Uma pergunta por vez, mostra os tipos que existem, grava cada decisão como sua ou como sugestão, e não constrói nada até as escolhas estarem fechadas. |
| `ficha-do-projeto` | Guarda tudo de um projeto dentro dele, numa pasta `.crewcraft/`: decisões, perguntas em aberto, perfil visual. Nunca sobrescreve o que você editou. |
| `prototipo-visual` | Mostra o visual em duas rodadas separadas, primeiro a estrutura, depois tema e cores, e bloqueia a construção até você aprovar. |
| `gerente` | O gerente: transforma suas decisões em tarefas, mantém uma fila com prioridades (Urgente para tudo), permite uma tarefa por cargo de cada vez e informa com honestidade: só o que está pronto e testado conta na porcentagem. |
| `ambiente` | Descobre o que está instalado neste computador e, para cada função (teste em ambiente limpo, checagem no navegador, controle de versão), lista as opções em ordem com a fraqueza de cada uma em palavras simples. Não instala nada sem aprovação. |
| `/crewcraft:escritorio` | Escritório pixel opcional (desligado até você iniciar): cada cargo na sua mesa, a tarefa em cima da cabeça de quem trabalha, e quem está parado passeia, bebe água e conversa. Só lê e é local. |
| `/crewcraft:comecar` | Comando que inicia a conversa: `/crewcraft:comecar quero um painel para minha equipe` |

O Claude costuma iniciar a conversa sozinho quando você pede para construir algo, mas isso não é garantido. `/crewcraft:comecar` sempre inicia.

Os nomes das skills estão em português. O Claude responde no **seu** idioma.

## A equipe e o portão de liberação

Cada cargo é um agente separado, com instruções próprias: `dev`, `design`, `qa`, `security`, `support`, `marketing`, e os supervisores `supervisor-dev`, `supervisor-design` e `supervisor-teste`. Os supervisores não podem editar nada: só rodam as conferências eles mesmos e aprovam ou reprovam. Cada cargo faz uma tarefa por vez, e só o que um supervisor aprovou conta como pronto. A terceira reprovação da mesma tarefa chega até você.

Um gancho bloqueia comandos de liberação (`git push`, `npm publish`, deploys) num projeto com fila do Crewcraft até que toda tarefa de Dev, Design, QA e Segurança esteja aprovada e você tenha registrado o seu teste final. O gancho precisa de Python no PATH; sem Python ele deixa tudo passar, para nunca te prender.

### Primeiro a estrutura, depois o tema

Três layouts que diferem na estrutura, sem nenhuma cor escrita neles:

![Três layouts de painel lado a lado: Estrutura A, B e C](docs/img/estruturas.png)

Depois, a mesma estrutura com três temas bem diferentes. Só o arquivo de tema muda:

![O mesmo layout em três temas: claro de sistema, claro com destaque vermelho e escuro](docs/img/temas.png)

Se você disser "parece feito por IA", o Crewcraft muda de direção em vez de ajustar a mesma paleta, pede uma referência e anota o que você não gostou numa lista de proibidos do perfil visual do projeto.

## Ele se adapta a você

Seu nível é guardado por área (desenvolvimento, design, segurança, infraestrutura, IA) como `novice` (iniciante), `intermediate` (intermediário) ou `expert` (especialista). Iniciante recebe palavras simples e analogias. Especialista recebe respostas curtas e os prós e contras técnicos. Diga "fale mais simples" ou "pode ser técnico" quando quiser. Um termo técnico solto nunca faz o Crewcraft tratar você como especialista: ele pergunta antes.

## Instalação

No Claude Code:

```
/plugin marketplace add <owner>/crewcraft
/plugin install crewcraft@crewcraft
```

Troque `<owner>` pela conta do GitHub que hospeda este repositório. Python 3 é opcional: serve só para um pequeno auxiliar que cria a pasta `.crewcraft/`, e o Crewcraft copia os arquivos à mão se não houver Python.

## Privacidade

O Crewcraft não faz nenhuma chamada de rede por conta própria. Tudo do seu projeto fica na pasta `.crewcraft/` dele, e o seu perfil de nível fica no seu computador, nunca dentro do plugin. O auxiliar e as skills não gravam dentro de nenhuma pasta chamada "Não mexer", e perguntam qual pasta é o projeto antes de criar a `.crewcraft/`. Os logs de clientes são mascarados (documentos, e-mails, senhas, endereços) antes de o cargo de suporte lê-los, e a página opcional do escritório escuta só em 127.0.0.1.

## Planejado, ainda não incluído

Pesquisa do projeto (concorrentes, ferramentas, documentação atual, papers) que termina num relatório curto para você aprovar, e skills sob medida para cada projeto a partir dessa pesquisa.

## Licença

A definir antes da primeira versão pública.
