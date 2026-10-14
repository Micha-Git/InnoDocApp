CREATE TABLE nodes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES nodes(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('folder', 'file')),

    -- No files at root-level
    CHECK (type = 'folder' OR parent_id IS NOT NULL),

    UNIQUE (parent_id, name)
);

-- Only folders can be parent at nodes
CREATE OR REPLACE FUNCTION enforce_folder_parent()
RETURNS TRIGGER AS $$
DECLARE
    parent_type TEXT;
BEGIN

    IF NEW.parent_id IS NULL THEN
        IF NEW.type = 'file' THEN
            RAISE EXCEPTION 'Files cannot have NULL parent_id';
        END IF;
        RETURN NEW;
    END IF;

    SELECT type INTO parent_type FROM nodes WHERE id = NEW.parent_id;

    IF parent_type <> 'folder' THEN
        RAISE EXCEPTION 'Parent (id=%) must be a folder, but is type=%',
            NEW.parent_id, parent_type;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_folder_parent
BEFORE INSERT OR UPDATE ON nodes
FOR EACH ROW EXECUTE FUNCTION enforce_folder_parent();


CREATE TABLE file_contents (
    id SERIAL PRIMARY KEY,
    file_id INTEGER UNIQUE NOT NULL,
    content TEXT NOT NULL,

    FOREIGN KEY (file_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Only files are allowed to have content
CREATE OR REPLACE FUNCTION enforce_file_type()
RETURNS TRIGGER AS $$
DECLARE
    node_type TEXT;
BEGIN
    SELECT type INTO node_type FROM nodes WHERE id = NEW.file_id;

    IF node_type <> 'file' THEN
        RAISE EXCEPTION 'file_id (%) refers to a node of type %, but required type is file',
            NEW.file_id, node_type;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_file_type
BEFORE INSERT OR UPDATE ON file_contents
FOR EACH ROW EXECUTE FUNCTION enforce_file_type();


-- Returns id, filepath and content of all files
CREATE VIEW file_paths AS
WITH RECURSIVE path_build AS (

    SELECT
        n.id,
        n.name,
        n.parent_id,
        n.type,
        n.name AS path
    FROM nodes n
    WHERE parent_id IS NULL

    UNION ALL

    SELECT
        c.id,
        c.name,
        c.parent_id,
        c.type,
        (p.path || '/' || c.name) AS path
    FROM nodes c
    JOIN path_build p ON p.id = c.parent_id
)
SELECT
    p.id AS file_id,
    p.path AS file_path,
    fc.content
FROM path_build p
JOIN file_contents fc ON fc.file_id = p.id
WHERE p.type = 'file';

-- Example Data
INSERT INTO nodes (id, name, parent_id, type) VALUES
(1, 'Horizon', NULL, 'folder'),
(2, 'Orion', NULL, 'folder'),
(3, '0_Project_Description', 1, 'folder'),
(4, 'project_overview.docx', 3, 'file'),
(5, 'stakeholder_list.xslx', 3, 'file'),
(6, 'overview.txt', 2, 'file'),
(7, 'summary.pdf', 2, 'file'),
-- Adding more documents to be able to test better
(100, 'Document 100.txt', 1, 'file'),
(101, 'Document 101.txt', 2, 'file'),
(102, 'Document 102.txt', 1, 'file'),
(103, 'Document 103.txt', 2, 'file'),
(104, 'Document 104.txt', 1, 'file'),
(105, 'Document 105.txt', 2, 'file'),
(106, 'Document 106.txt', 1, 'file'),
(107, 'Document 107.txt', 2, 'file'),
(108, 'Document 108.txt', 1, 'file'),
(109, 'Document 109.txt', 2, 'file'),
(110, 'Document 110.txt', 1, 'file'),
(111, 'Document 111.txt', 2, 'file'),
(112, 'Document 112.txt', 1, 'file'),
(113, 'Document 113.txt', 2, 'file'),
(114, 'Document 114.txt', 1, 'file'),
(115, 'Document 115.txt', 2, 'file'),
(116, 'Document 116.txt', 1, 'file'),
(117, 'Document 117.txt', 2, 'file'),
(118, 'Document 118.txt', 1, 'file'),
(119, 'Document 119.txt', 2, 'file'),
(120, 'Document 120.txt', 1, 'file');

INSERT INTO file_contents (id, file_id, content) VALUES
(8, 4, 'content_of_Project_Horizon_0_Project_Description_project_overview.docx'),
(9, 5, 'content_of_Project_Horizon_0_Project_Description_stakeholder_list.xslx'),
(10, 6, 'content_of_Project_Orion_overview.txt'),
(11, 7, 'content_of_Project_Horizon_summary.pdf'),
-- Document contents for the "file_contents" table
(100,100, 'This is the content of document 100.'),
(101,101, 'This is the content of document 101.'),
(102,102, 'This is the content of document 102.'),
(103,103, 'This is the content of document 103.'),
(104,104, 'This is the content of document 104.'),
(105,105, 'This is the content of document 105.'),
(106,106, 'This is the content of document 106.'),
(107,107, 'This is the content of document 107.'),
(108,108, 'This is the content of document 108.'),
(109,109, 'This is the content of document 109.'),
(110,110, 'This is the content of document 110.'),
(111,111, 'This is the content of document 111.'),
(112,112, 'This is the content of document 112.'),
(113,113, 'This is the content of document 113.'),
(114,114, 'This is the content of document 114.'),
(115,115, 'This is the content of document 115.'),
(116,116, 'This is the content of document 116.'),
(117,117, 'This is the content of document 117.'),
(118,118, 'This is the content of document 118.'),
(119,119, 'This is the content of document 119.'),
(120,120, 'This is the content of document 120.');

-- Table for document attributes
CREATE TABLE document_seclevel (
    -- Delete entry if reference is deleted on referenced table
    file_id INTEGER PRIMARY KEY REFERENCES nodes(id) ON DELETE CASCADE,
    seclevel INTEGER NOT NULL
);

-- Table for document sources
CREATE TABLE document_source (
    file_id INTEGER PRIMARY KEY REFERENCES nodes(id) ON DELETE CASCADE,
    source TEXT NOT NULL
);

-- SecLevel Attributes
INSERT INTO document_seclevel (file_id, seclevel) VALUES
(4, 2),
(5, 3),
(6, 3),
(7, 4),
(100, 1),
(101, 1),
(102, 2),
(103, 2),
(104, 3),
(105, 3),
(106, 4),
(107, 4),
(108, 5),
(109, 5),
(110, 6),
(111, 6),
(112, 7),
(113, 7),
(114, 8),
(115, 8),
(116, 9),
(117, 9),
(118, 1),
(119, 1),
(120, 2);

-- Sources for each document (add as many as needed)
INSERT INTO document_source (file_id, source) VALUES
(4, 'Horizon'),
(5, 'Horizon'),
(100, 'Horizon'),
(102, 'Horizon'),
(104, 'Horizon'),
(106, 'Horizon'),
(108, 'Horizon'),
(110, 'Horizon'),
(112, 'Horizon'),
(114, 'Horizon'),
(116, 'Horizon'),
(118, 'Horizon'),
(120, 'Horizon'),

(6, 'Orion'),
(7, 'Orion'),
(101, 'Orion'),
(103, 'Orion'),
(105, 'Orion'),
(107, 'Orion'),
(109, 'Orion'),
(111, 'Orion'),
(113, 'Orion'),
(115, 'Orion'),
(117, 'Orion'),
(119, 'Orion');



-- Resources under this schema will be exposed per API.
CREATE SCHEMA pip;
CREATE ROLE web_pip nologin;
GRANT USAGE ON SCHEMA pip TO web_pip;

CREATE VIEW pip.document_attributes AS
SELECT
    s.file_id,
    s.seclevel,
    src.source
FROM document_seclevel s
JOIN document_source src
  ON s.file_id = src.file_id;

GRANT SELECT ON pip.document_attributes TO web_pip;
CREATE ROLE authenticator noinherit login password 'pippassword';
GRANT web_pip TO authenticator;

-- keycloak:
CREATE DATABASE keycloak;
