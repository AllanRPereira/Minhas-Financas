BEGIN;

CREATE TABLE users (
    id INTEGER NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    PRIMARY KEY(id)
);

-- Categorias possíveis para Tellers e Incomes
-- Symbol será utilizado para armazenar um link para um ícone da categoria
CREATE TABLE categorys (
    id INTEGER NOT NULL,
    name VARCHAR(25),
    symbol VARCHAR(50),
    PRIMARY KEY(id)
);

-- Utilizado para armazenar as transações.
CREATE TABLE transactions (
    id INTEGER NOT NULL,
    name VARCHAR(25) NOT NULL,
    value REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    description VARCHAR(100) DEFAULT "",
    id_to INTEGER NOT NULL,
    id_from INTEGER NOT NULL,
    id_user INTEGER NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(id_to) REFERENCES payer(id),
    FOREIGN KEY(id_from) REFERENCES yield(id),
    FOREIGN KEY(id_user) REFERENCES user(id)
);

-- Métodos de pagamento, como cartão, dívidas e investimentos
-- Extra data:
    -- Cartão de crédito: Vencimento
    -- Investimento: Rendimento
    -- Dívida: Data para pagamento
CREATE TABLE payment_content (
    id INTEGER NOT NULL,
    id_user INTEGER NOT NULL,
    type INTEGER NOT NULL,
    name VARCHAR(25),
    balance REAL DEFAULT 0,
    extra_data REAL DEFAULT -1,
    PRIMARY KEY(id),
    FOREIGN KEY(id_user) REFERENCES users(id)
);

CREATE TABLE tokens (
    id INTEGER NOT NULL,
    id_user INTEGER, 
    type INTEGER,
    PRIMARY KEY(id),
    FOREIGN KEY(id_user) REFERENCES users(id)
);

-- Um objeto que atua como uma fonte de gasto
CREATE TABLE teller (
    id INTEGER NOT NULL,
    name VARCHAR(20) UNIQUE NOT NULL,
    id_user INTEGER NOT NULL,
    id_category INTEGER,
    PRIMARY KEY(id),
    FOREIGN KEY(id_user) REFERENCES users(id),
    FOREIGN KEY(id_category) REFERENCES categorys(id)
);

-- Tabela que liga as transações ao agente dos gastos
-- podendo ser um Teller ou outro Payment
CREATE TABLE payer (
    id INTEGER NOT NULL,
    id_teller INTEGER DEFAULT -1,
    id_payment INTEGER DEFAULT -1,
    PRIMARY KEY(id),
    FOREIGN KEY(id_teller) REFERENCES teller(id),
    FOREIGN KEY(id_payment) REFERENCES payment_content(id)
);


-- Análogo ao payer porém referindo-se à fonte de renda ou entrada
-- dos valores.
CREATE TABLE yield (
    id INTEGER NOT NULL,
    id_payment INTEGER DEFAULT -1,
    id_income INTEGER DEFAULT -1,
    PRIMARY KEY(id),
    FOREIGN KEY(id_payment) REFERENCES payment_content(id)
    FOREIGN KEY(id_income) REFERENCES incomes(id)
);

-- Objeto que representa as fontes de renda que um usuário pode ter
CREATE TABLE incomes (
    id INTEGER NOT NULL,
    name VARCHAR(25),
    id_user INTEGER NOT NULL,
    id_category INTEGER,
    PRIMARY KEY(id),
    FOREIGN KEY(id_user) REFERENCES users(id),
    FOREIGN KEY(id_category) REFERENCES categorys(id)
);

COMMIT;