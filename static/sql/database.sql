CREATE TABLE users (
    id INT NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    PRIMARY KEY(id)
);

CREATE TABLE categorys (
    id INT NOT NULL,
    name VARCHAR(25),
    description VARCHAR(100),
    PRIMARY KEY(id)
);

CREATE TABLE payment_methods (
    id INT NOT NULL,
    type VARCHAR(15),
    id_user INT NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(id_user) REFERENCES user(id)
);

CREATE TABLE transactions (
    id INT NOT NULL,
    value REAL NOT NULL,
    id_to INT NOT NULL,
    id_from INT DEFAULT -1,
    id_category INT NOT NULL,
    id_user INT NOT NULL,
    FOREIGN KEY(id_to) REFERENCES payment_methods(id),
    FOREIGN KEY(id_from) REFERENCES payment_methods(id),
    FOREIGN KEY(id_category) REFERENCES categorys(id),
    FOREIGN KEY(id_user) REFERENCES user(id)
);

CREATE TABLE payment_content (
    id INT NOT NULL,
    name VARCHAR(25),
    balance REAL,
    description VARCHAR(100),
    FOREIGN KEY(id) REFERENCES payment_methods(id)
);

CREATE TABLE tokens (
    id INT NOT NULL,
    id_user INT, 
    type INT,
    PRIMARY KEY(id),
    FOREIGN KEY(id_user) REFERENCES users(id)
);