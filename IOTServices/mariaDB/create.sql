CREATE DATABASE dso_db;
USE dso_db;

grant all privileges on dso_db.* TO 'dso_db_user'@'%' identified by 'dso_db_password';
flush privileges;


CREATE TABLE device_state (
    id MEDIUMINT NOT NULL AUTO_INCREMENT,
    room varchar(10) NOT NULL,
    type varchar(25) NOT NULL,
    value INT NOT NULL,
    date DATETIME(3) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE device_registration (
    name varchar(25) NOT NULL,
    active TINYINT NOT NULL,
    room_state JSON NOT NULL,
    UNIQUE(name)
);
