CREATE DATABASE IF NOT EXISTS NoteKeeperDB DEFAULT CHARACTER SET utf8;

CREATE TABLE IF NOT EXISTS Users (
    id int NOT NULL AUTO_INCREMENT,
    email varchar(50) NOT NULL UNIQUE,
    password varchar(260) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS Notes (
    id int NOT NULL AUTO_INCREMENT,
    user_id int NOT NULL,
    note varchar(2048) NOT NULL,
    time_created DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

