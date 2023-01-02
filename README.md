# Minhas Finanças

Minhas finanças é um aplicação web que tem a finalidade de auxiliar na organização financeira de seus usuários.
#### Funcionalidades

- Funções de login/registro e recuperação de senha
- Capacidade de adicionar cartões, investimentos e dívidas
- Capacidade de adicionar categorias e novas fontes de gasto e renda
- Ver transações realizadas com fontes especifícas como cartões e investimentos
- Entre outras funcões..

#### Ferramentas Utilizadas

- Python3 
- Flask
- Sqlite3

#### Guia de uso

Para replicar esse projeto na sua máquina algumas observações devem ser realizadas:
- Setar corretamente os dados do email fonte da aplicação logo no início do ```app.py```
- Definir a chave para encriptação dos tokens por meio da variável de ambiente ```TOKEN_KEY```
- Criar o arquivo ```minhasfinancas.db```

Além disso, temos o ```generate.py``` que renova o campo de bancos e gera entradas para testes das funcionalidades da aplicação.

#### Agradecimentos

Esta é a versão 0 dessa aplicação, então ainda há muito a ser feito para melhora-lá. Agradeço imensamente à [Fundação Estudar](https://www.estudar.org.br/) por ter feito o trabalho de legendar o **CS50 2020** de Harvard e por Harvard disponibilizar esse curso ao público!

[![Versão - 0](https://img.shields.io/badge/Versão-0-2ea44f)](https://github.com/AllanRPereira/MinhasFinancas/)
