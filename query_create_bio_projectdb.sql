-- 1. Create the database (schema) itself. 
-- 'IF NOT EXISTS' prevents errors if you run it twice.
CREATE SCHEMA IF NOT EXISTS bio_project DEFAULT CHARACTER SET utf8 ;

-- 2. Tell MySQL to use this new database
USE bio_project;

-- 3. Create your tables
-- Note the 'INT' and 'AUTO_INCREMENT' syntax for MySQL

CREATE TABLE IF NOT EXISTS protein (
    uniprot_id VARCHAR(255) PRIMARY KEY,
    name TEXT,
    sequence TEXT
);

CREATE TABLE IF NOT EXISTS pdb_structure (
    pdb_id VARCHAR(255) PRIMARY KEY,
    method TEXT,
    resolution FLOAT,
    title TEXT
);

CREATE TABLE IF NOT EXISTS protein_structure_map (
    map_id INT PRIMARY KEY AUTO_INCREMENT,
    uniprot_id VARCHAR(255),
    pdb_id VARCHAR(255),
    FOREIGN KEY (uniprot_id) REFERENCES protein (uniprot_id),
    FOREIGN KEY (pdb_id) REFERENCES pdb_structure (pdb_id),
    UNIQUE(uniprot_id, pdb_id)
);