CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> version0.20261113

CREATE TABLE user (
    id VARCHAR(32) NOT NULL COMMENT '主键', 
    username VARCHAR(50) NOT NULL COMMENT '用户名', 
    zh_name VARCHAR(150) COMMENT '中文名', 
    en_name VARCHAR(150) COMMENT '英文名', 
    password VARCHAR(255) NOT NULL COMMENT '密码', 
    email VARCHAR(254) COMMENT '邮箱', 
    phone_number VARCHAR(30) COMMENT '手机号', 
    status INTEGER NOT NULL COMMENT '0=available 1=unavailable', 
    api_key VARCHAR(128) NOT NULL COMMENT 'API key', 
    create_time DATETIME NOT NULL COMMENT '创建时间', 
    update_time DATETIME COMMENT '更新时间', 
    delete_time DATETIME COMMENT '删除时间', 
    is_deleted BOOL NOT NULL COMMENT '软删除标记, 0:否 1:是', 
    first_login BOOL NOT NULL COMMENT '首次登录标记, 0:否 1:是', 
    PRIMARY KEY (id)
)COMMENT='用户表';

CREATE INDEX ix_user_username ON user (username);

CREATE INDEX ix_user_email ON user (email);

CREATE INDEX ix_user_create_time ON user (create_time);

CREATE INDEX ix_user_is_deleted ON user (is_deleted);

CREATE UNIQUE INDEX uq_user_username_active ON user ((CASE WHEN is_deleted = 0 THEN username ELSE NULL END));

CREATE UNIQUE INDEX uq_user_email_active ON user ((CASE WHEN is_deleted = 0 THEN email ELSE NULL END));

CREATE TABLE host (
    id VARCHAR(32) NOT NULL COMMENT '主键', 
    ip_address VARCHAR(45) NOT NULL COMMENT 'IP地址', 
    username VARCHAR(50) NOT NULL COMMENT '用户名', 
    password VARCHAR(255) NOT NULL COMMENT '密码', 
    port INTEGER NOT NULL COMMENT '端口', 
    status INTEGER NOT NULL COMMENT '0=online 1=offline', 
    deploy_path VARCHAR(255) NOT NULL COMMENT '部署家目录', 
    create_time DATETIME NOT NULL COMMENT '创建时间', 
    update_time DATETIME COMMENT '更新时间', 
    delete_time DATETIME COMMENT '删除时间', 
    description VARCHAR(100) COMMENT '主机描述', 
    PRIMARY KEY (id), 
    CONSTRAINT check_port_range CHECK (port >= 1 AND port <= 65535)
)COMMENT='主机表';

CREATE UNIQUE INDEX uq_host_ip_address ON host (ip_address);

CREATE TABLE `system` (
    id VARCHAR(32) NOT NULL COMMENT '主键', 
    secret_key VARCHAR(32) NOT NULL COMMENT 'sk', 
    PRIMARY KEY (id)
)COMMENT='系统表';

INSERT INTO `system` (id, secret_key) VALUES ('f9db678c19974379acad94e5b5ab0000', '93d2803230314efa827ef46457ce86f8');

INSERT INTO alembic_version (version_num) VALUES ('version0.20261113');

