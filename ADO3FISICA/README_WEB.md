# Versão web — ADO-3 Física

`index.html` é uma versão web interativa do simulador. Ela funciona no navegador, sem instalar Python ou bibliotecas, e mantém os três casos, os cinco controles, a animação, o painel e os gráficos.

## Abrir localmente

Abra `index.html` no Chrome, Edge ou Firefox. Não é necessário servidor local.

## Publicar um link gratuito com GitHub Pages

O workflow `.github/workflows/pages.yml` publica automaticamente `index.html` quando há um push para a branch `main`.

1. Crie um repositório no GitHub (público, por exemplo `ado3-fisica`).
2. Envie `index.html` e a pasta `.github/workflows/` para a branch `main`.
3. No repositório, acesse **Settings → Pages** e em **Build and deployment → Source** selecione **GitHub Actions**.
4. Aguarde a execução verde em **Actions**. O endereço será `https://SEU-USUARIO.github.io/ado3-fisica/`.

O primeiro deploy pode levar alguns minutos. O repositório local ainda não tem um remoto Git configurado; por isso, é necessário criar/selecionar o repositório da equipe e enviar estes arquivos antes de existir um link público.

## Arquivos da entrega acadêmica

- `ADO3_Nicolas_Vinicius_Bruna.py`: versão Python exigida pelo enunciado.
- `RELATORIO_ADO3.pdf`: relatório de duas páginas com Q1–Q5.
- `index.html`: versão de acesso pelo navegador, sem instalação.
