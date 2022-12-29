BEGIN;

CREATE TABLE users (
    id INTEGER NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE categorys (
    id INTEGER NOT NULL,
    name VARCHAR(25),
    symbol VARCHAR(50),
    PRIMARY KEY(id)
);

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

CREATE TABLE payment_content (
    id INTEGER NOT NULL,
    id_user INTEGER NOT NULL,
    type INTEGER NOT NULL,
    name VARCHAR(25),
    balance REAL DEFAULT 0,
    description VARCHAR(100),
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

CREATE TABLE teller (
    id INTEGER NOT NULL,
    name VARCHAR(20) UNIQUE NOT NULL,
    id_user INTEGER NOT NULL,
    id_category INTEGER,
    PRIMARY KEY(id),
    FOREIGN KEY(id_user) REFERENCES users(id),
    FOREIGN KEY(id_category) REFERENCES categorys(id)
);

CREATE TABLE payer (
    id INTEGER NOT NULL,
    id_teller INTEGER DEFAULT -1,
    id_payment INTEGER DEFAULT -1,
    PRIMARY KEY(id),
    FOREIGN KEY(id_teller) REFERENCES teller(id),
    FOREIGN KEY(id_payment) REFERENCES payment_content(id)
);

CREATE TABLE yield (
    id INTEGER NOT NULL,
    id_payment INTEGER DEFAULT -1,
    id_income INTEGER DEFAULT -1,
    PRIMARY KEY(id),
    FOREIGN KEY(id_payment) REFERENCES payment_content(id)
    FOREIGN KEY(id_income) REFERENCES incomes(id)
);

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