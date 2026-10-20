-- ============================================================
-- CTF 训练竞赛平台 数据库初始化脚本
-- 适用环境：MySQL 8.0+
-- 内容：建库、7 张基本表、5 个视图、5 个存储过程、3 个触发器、演示数据
-- 执行方式：mysql -h 127.0.0.1 -P 3306 -u root -p < ctf_init.sql
-- 首次初始化使用：ctf 中不应存在同名对象；本脚本面向全新环境，
-- 重复执行前请先执行 DROP DATABASE ctf; 再重新导入。
-- 演示账号：admin / Admin@123（管理员），zhangsan 等 10 个学生 / Pass@123
-- ============================================================

CREATE DATABASE IF NOT EXISTS ctf DEFAULT CHARACTER SET utf8mb4;
USE ctf;

-- ------------------------------------------------------------
-- 1. 用户表：学生与管理员共用，角色区分权限
-- ------------------------------------------------------------
CREATE TABLE Users
(
    Uid          INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户编号',
    Username     VARCHAR(32)  NOT NULL UNIQUE COMMENT '登录名，全局唯一',
    PasswordHash CHAR(64)     NOT NULL COMMENT '口令散列 SHA2(口令+盐,256)',
    Salt         CHAR(32)     NOT NULL COMMENT '口令盐',
    Email        VARCHAR(64)  NOT NULL COMMENT '电子邮箱',
    Role         ENUM ('student','admin') NOT NULL DEFAULT 'student' COMMENT '角色',
    Status       ENUM ('active','disabled') NOT NULL DEFAULT 'active'
                 COMMENT '账号状态',
    CreatedAt    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户';

-- ------------------------------------------------------------
-- 2. 题目分类表：Pwn / Web / Reverse / Crypto / Misc
-- ------------------------------------------------------------
CREATE TABLE Categories
(
    Cid   INT PRIMARY KEY AUTO_INCREMENT COMMENT '分类编号',
    Cname VARCHAR(16) NOT NULL UNIQUE COMMENT '分类名称',
    Cdesc VARCHAR(100) COMMENT '分类说明'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目分类';

-- ------------------------------------------------------------
-- 3. 题目表：管理员录入，草稿/上架/下线三态控制可见性
-- ------------------------------------------------------------
CREATE TABLE Challenges
(
    Chid        INT PRIMARY KEY AUTO_INCREMENT COMMENT '题目编号',
    Cid         INT            NOT NULL COMMENT '所属分类',
    Title       VARCHAR(64)    NOT NULL COMMENT '题名',
    Description VARCHAR(500) COMMENT '题目描述',
    Difficulty  TINYINT        NOT NULL DEFAULT 1 COMMENT '难度 1 至 5',
    Score       INT            NOT NULL COMMENT '基础分值',
    FlagHash    CHAR(64)       NOT NULL COMMENT 'flag 散列 SHA2(flag+盐,256)',
    FlagSalt    CHAR(32)       NOT NULL COMMENT 'flag 盐',
    Attachment  VARCHAR(128) COMMENT '附件路径',
    Status      ENUM ('draft','online','offline') NOT NULL DEFAULT 'draft'
                COMMENT '上架状态',
    AuthorUid   INT            NOT NULL COMMENT '录题管理员',
    CreatedAt   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间',
    PublishedAt DATETIME COMMENT '上架时间',
    KEY idx_challenge_filter (Cid, Difficulty, Status),
    KEY idx_challenge_title (Title),
    CONSTRAINT fk_challenge_category FOREIGN KEY (Cid) REFERENCES Categories (Cid),
    CONSTRAINT fk_challenge_author FOREIGN KEY (AuthorUid) REFERENCES Users (Uid),
    CONSTRAINT ck_challenge_difficulty CHECK (Difficulty BETWEEN 1 AND 5),
    CONSTRAINT ck_challenge_score CHECK (Score > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='训练题目';

-- ------------------------------------------------------------
-- 4. 提交记录表：每一次 flag 提交都留档，用于答题记录与审计
-- ------------------------------------------------------------
CREATE TABLE Submissions
(
    Subid       BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '提交编号',
    Uid         INT      NOT NULL COMMENT '提交人',
    Chid        INT      NOT NULL COMMENT '题目编号',
    FlagHash    CHAR(64) NOT NULL COMMENT '本次提交 flag 的散列',
    IsCorrect   TINYINT  NOT NULL DEFAULT 0 COMMENT '是否正确 1/0',
    SubmittedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    KEY idx_submission_user (Uid, SubmittedAt),
    KEY idx_submission_challenge (Chid, IsCorrect),
    CONSTRAINT fk_submission_user FOREIGN KEY (Uid) REFERENCES Users (Uid),
    CONSTRAINT fk_submission_challenge FOREIGN KEY (Chid) REFERENCES Challenges (Chid),
    CONSTRAINT ck_submission_correct CHECK (IsCorrect IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='flag 提交记录';

-- ------------------------------------------------------------
-- 5. 解题计分表：主键 (Uid,Chid) 在结构层保证同一题目只计分一次
-- ------------------------------------------------------------
CREATE TABLE Solves
(
    Uid          INT      NOT NULL COMMENT '解题人',
    Chid         INT      NOT NULL COMMENT '题目编号',
    Subid        BIGINT   NOT NULL COMMENT '首次正确提交编号',
    ScoreAwarded INT      NOT NULL COMMENT '本次得分',
    SolvedAt     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '解出时间',
    PRIMARY KEY (Uid, Chid),
    UNIQUE KEY uk_solves_submission (Subid),
    KEY idx_solves_challenge (Chid),
    CONSTRAINT fk_solves_user FOREIGN KEY (Uid) REFERENCES Users (Uid),
    CONSTRAINT fk_solves_challenge FOREIGN KEY (Chid) REFERENCES Challenges (Chid),
    CONSTRAINT fk_solves_submission FOREIGN KEY (Subid) REFERENCES Submissions (Subid),
    CONSTRAINT ck_solves_score CHECK (ScoreAwarded > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='解题与计分';

-- ------------------------------------------------------------
-- 6. 积分变动日志：由触发器在计分时自动写入
-- ------------------------------------------------------------
CREATE TABLE ScoreLogs
(
    LogId      BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志编号',
    Uid        INT      NOT NULL COMMENT '得分人',
    Chid       INT      NOT NULL COMMENT '题目编号',
    DeltaScore INT      NOT NULL COMMENT '本次得分变动',
    TotalAfter INT      NOT NULL COMMENT '变动后累计总分',
    Action     VARCHAR(16) NOT NULL DEFAULT 'solve' COMMENT '动作类型',
    OccurredAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
    KEY idx_scorelog_user (Uid, OccurredAt),
    CONSTRAINT fk_scorelog_user FOREIGN KEY (Uid) REFERENCES Users (Uid),
    CONSTRAINT fk_scorelog_challenge FOREIGN KEY (Chid) REFERENCES Challenges (Chid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='积分变动日志';

-- ------------------------------------------------------------
-- 7. 管理操作日志：注册、录题、上架等关键操作自动留痕
-- ------------------------------------------------------------
CREATE TABLE OperationLogs
(
    Opid       BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志编号',
    Uid        INT          NOT NULL COMMENT '操作人',
    Action     VARCHAR(32)  NOT NULL COMMENT '操作类型',
    Target     VARCHAR(64) COMMENT '操作对象',
    Detail     VARCHAR(200) COMMENT '操作说明',
    OccurredAt DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
    KEY idx_operation_user (Uid, OccurredAt),
    CONSTRAINT fk_operation_user FOREIGN KEY (Uid) REFERENCES Users (Uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理操作日志';

-- ------------------------------------------------------------
-- 视图 1：公共题库。只暴露已上架题目，且不输出 FlagHash / FlagSalt
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_challenge_public AS
SELECT ch.Chid        AS 题目编号,
       ca.Cname       AS 分类,
       ch.Title       AS 题名,
       ch.Description AS 题目描述,
       ch.Difficulty  AS 难度,
       ch.Score       AS 分值,
       ch.Attachment  AS 附件,
       ch.PublishedAt AS 上架时间
FROM Challenges ch
         JOIN Categories ca ON ch.Cid = ca.Cid
WHERE ch.Status = 'online';

-- ------------------------------------------------------------
-- 视图 2：答题记录与得分明细。个人中心按用户名或编号查询
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_submission_record AS
SELECT s.Subid       AS 提交编号,
       u.Uid         AS 用户编号,
       u.Username    AS 用户名,
       ca.Cname      AS 分类,
       ch.Title      AS 题名,
       ch.Score      AS 题目分值,
       s.IsCorrect   AS 是否答对,
       COALESCE(so.ScoreAwarded, 0) AS 本次得分,
       s.SubmittedAt AS 提交时间
FROM Submissions s
         JOIN Users u ON s.Uid = u.Uid
         JOIN Challenges ch ON s.Chid = ch.Chid
         JOIN Categories ca ON ch.Cid = ca.Cid
         LEFT JOIN Solves so ON so.Subid = s.Subid;

-- ------------------------------------------------------------
-- 视图 3：个人得分明细，逐题列出得分与解出时间
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_score_detail AS
SELECT u.Uid         AS 用户编号,
       u.Username    AS 用户名,
       ca.Cname      AS 分类,
       ch.Title      AS 题名,
       ch.Difficulty AS 难度,
       so.ScoreAwarded AS 得分,
       so.SolvedAt   AS 解出时间
FROM Solves so
         JOIN Users u ON so.Uid = u.Uid
         JOIN Challenges ch ON so.Chid = ch.Chid
         JOIN Categories ca ON ch.Cid = ca.Cid;

-- ------------------------------------------------------------
-- 视图 4：总分榜。同分时先解出者名次靠前
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_total_rank AS
SELECT RANK() OVER (ORDER BY SUM(so.ScoreAwarded) DESC, MAX(so.SolvedAt) ASC) AS 名次,
       u.Uid       AS 用户编号,
       u.Username  AS 用户名,
       SUM(so.ScoreAwarded) AS 总分,
       COUNT(*)    AS 解题数,
       MAX(so.SolvedAt)     AS 最后解题时间
FROM Solves so
         JOIN Users u ON so.Uid = u.Uid
GROUP BY u.Uid, u.Username;

-- ------------------------------------------------------------
-- 视图 5：分类榜。按分类分区，分别给出各方向的训练排名
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW v_category_rank AS
SELECT ca.Cid      AS 分类编号,
       ca.Cname    AS 分类,
       RANK() OVER (PARTITION BY ca.Cid ORDER BY SUM(so.ScoreAwarded) DESC,
                    MAX(so.SolvedAt) ASC) AS 名次,
       u.Uid       AS 用户编号,
       u.Username  AS 用户名,
       SUM(so.ScoreAwarded) AS 分类得分,
       COUNT(*)    AS 解题数
FROM Solves so
         JOIN Users u ON so.Uid = u.Uid
         JOIN Challenges ch ON so.Chid = ch.Chid
         JOIN Categories ca ON ch.Cid = ca.Cid
GROUP BY ca.Cid, ca.Cname, u.Uid, u.Username;

-- ============================================================
-- 存储过程
-- ============================================================

-- ------------------------------------------------------------
-- 过程 1：注册。用户名查重、口令加盐散列、格式校验都在库内完成
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_register_user;
DELIMITER //
CREATE PROCEDURE sp_register_user(IN p_username VARCHAR(32), IN p_password VARCHAR(64),
                                  IN p_email VARCHAR(64), OUT p_uid INT,
                                  OUT p_result VARCHAR(16), OUT p_message VARCHAR(100))
proc: BEGIN
    DECLARE v_salt CHAR(32) DEFAULT NULL;

    -- 用户名唯一约束冲突时按“已占用”返回，不再向调用方抛出异常
    DECLARE CONTINUE HANDLER FOR 1062
        SET p_result = 'duplicate', p_message = '用户名已被占用';

    SET p_uid = 0, p_result = 'error', p_message = '注册未完成';

    IF p_username NOT REGEXP '^[A-Za-z0-9_]{3,32}$' THEN
        SET p_result = 'invalid', p_message = '用户名应为 3 至 32 位字母、数字或下划线';
        LEAVE proc;
    END IF;
    IF CHAR_LENGTH(p_password) < 6 THEN
        SET p_result = 'invalid', p_message = '口令至少 6 位';
        LEAVE proc;
    END IF;
    IF p_email NOT LIKE '%_@_%.__%' THEN
        SET p_result = 'invalid', p_message = '电子邮箱格式不正确';
        LEAVE proc;
    END IF;

    SET v_salt = REPLACE(UUID(), '-', '');
    INSERT INTO Users (Username, PasswordHash, Salt, Email)
    VALUES (p_username, SHA2(CONCAT(p_password, v_salt), 256), v_salt, p_email);
    IF ROW_COUNT() = 1 THEN
        SET p_uid = LAST_INSERT_ID(), p_result = 'ok',
            p_message = '注册成功，口令已加盐散列存储';
    END IF;
END proc//
DELIMITER ;

-- ------------------------------------------------------------
-- 过程 2：录题。管理员录入后为草稿状态，flag 只以散列入库
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_add_challenge;
DELIMITER //
CREATE PROCEDURE sp_add_challenge(IN p_admin INT, IN p_cid INT, IN p_title VARCHAR(64),
                                  IN p_desc VARCHAR(500), IN p_difficulty TINYINT,
                                  IN p_score INT, IN p_flag VARCHAR(128),
                                  IN p_attachment VARCHAR(128), OUT p_chid INT,
                                  OUT p_result VARCHAR(16), OUT p_message VARCHAR(100))
proc: BEGIN
    DECLARE v_role VARCHAR(10) DEFAULT NULL;
    DECLARE v_salt CHAR(32) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
        BEGIN
            ROLLBACK;
            SET p_chid = 0, p_result = 'error', p_message = '录题未完成，已回滚';
        END;

    SET p_chid = 0, p_result = 'error', p_message = '录题未完成';

    SELECT Role INTO v_role FROM Users WHERE Uid = p_admin;
    IF v_role IS NULL OR v_role <> 'admin' THEN
        SET p_result = 'denied', p_message = '该操作需要管理员权限';
        LEAVE proc;
    END IF;
    IF p_difficulty NOT BETWEEN 1 AND 5 THEN
        SET p_result = 'invalid', p_message = '难度取值应为 1 至 5';
        LEAVE proc;
    END IF;
    IF p_score <= 0 THEN
        SET p_result = 'invalid', p_message = '分值应为正整数';
        LEAVE proc;
    END IF;
    IF CHAR_LENGTH(p_flag) < 6 THEN
        SET p_result = 'invalid', p_message = 'flag 长度不足 6 位';
        LEAVE proc;
    END IF;

    SET v_salt = REPLACE(UUID(), '-', '');
    START TRANSACTION;
    INSERT INTO Challenges (Cid, Title, Description, Difficulty, Score, FlagHash,
                            FlagSalt, Attachment, Status, AuthorUid)
    VALUES (p_cid, p_title, p_desc, p_difficulty, p_score,
            SHA2(CONCAT(p_flag, v_salt), 256), v_salt, p_attachment, 'draft', p_admin);
    SET p_chid = LAST_INSERT_ID();
    INSERT INTO OperationLogs (Uid, Action, Target, Detail)
    VALUES (p_admin, '录入题目', p_title,
            CONCAT('题目以草稿状态录入，分类编号 ', p_cid));
    COMMIT;
    SET p_result = 'ok', p_message = '题目已录入为草稿，上架后进入公共题库';
END proc//
DELIMITER ;

-- ------------------------------------------------------------
-- 过程 3：上架。状态流转由过程控制，变更动作经触发器自动留痕
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_publish_challenge;
DELIMITER //
CREATE PROCEDURE sp_publish_challenge(IN p_chid INT, IN p_admin INT,
                                      OUT p_result VARCHAR(16),
                                      OUT p_message VARCHAR(100))
proc: BEGIN
    DECLARE v_role VARCHAR(10) DEFAULT NULL;
    DECLARE v_status VARCHAR(10) DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
        BEGIN
            ROLLBACK;
            SET p_result = 'error', p_message = '上架未完成，已回滚';
        END;

    SET p_result = 'error', p_message = '上架未完成';

    SELECT Role INTO v_role FROM Users WHERE Uid = p_admin;
    IF v_role IS NULL OR v_role <> 'admin' THEN
        SET p_result = 'denied', p_message = '该操作需要管理员权限';
        LEAVE proc;
    END IF;

    SELECT Status INTO v_status FROM Challenges WHERE Chid = p_chid;
    IF v_status IS NULL THEN
        SET p_result = 'invalid', p_message = '题目不存在';
        LEAVE proc;
    ELSEIF v_status = 'online' THEN
        SET p_result = 'noop', p_message = '题目已处于上架状态';
        LEAVE proc;
    END IF;

    START TRANSACTION;
    SET @operator_uid = p_admin;
    UPDATE Challenges SET Status = 'online', PublishedAt = NOW() WHERE Chid = p_chid;
    COMMIT;
    SET p_result = 'ok', p_message = '题目已上架并进入公共题库';
END proc//
DELIMITER ;

-- ------------------------------------------------------------
-- 过程 4：flag 提交判定。查重、比对、计分在同一事务内完成
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_submit_flag;
DELIMITER //
CREATE PROCEDURE sp_submit_flag(IN p_uid INT, IN p_chid INT, IN p_flag VARCHAR(128),
                                OUT p_result VARCHAR(16), OUT p_score INT,
                                OUT p_message VARCHAR(100))
proc: BEGIN
    DECLARE v_user_status VARCHAR(10) DEFAULT NULL;
    DECLARE v_ch_status VARCHAR(10) DEFAULT NULL;
    DECLARE v_ch_score INT DEFAULT 0;
    DECLARE v_salt CHAR(32) DEFAULT NULL;
    DECLARE v_target CHAR(64) DEFAULT NULL;
    DECLARE v_flaghash CHAR(64) DEFAULT NULL;
    DECLARE v_solved INT DEFAULT 0;
    DECLARE v_correct TINYINT DEFAULT 0;
    DECLARE v_subid BIGINT DEFAULT 0;

    -- 并发重复计分由主键冲突拦下，交给下方 ROW_COUNT() 分支处理
    DECLARE CONTINUE HANDLER FOR 1062 BEGIN END;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
        BEGIN
            ROLLBACK;
            SET p_result = 'error', p_score = 0,
                p_message = '判定过程出现异常，本次提交已回滚';
        END;

    SET p_result = 'error', p_score = 0, p_message = '判定未完成';

    SELECT Status INTO v_user_status FROM Users WHERE Uid = p_uid;
    IF v_user_status IS NULL THEN
        SET p_message = '用户不存在';
        LEAVE proc;
    ELSEIF v_user_status <> 'active' THEN
        SET p_message = '账号已停用，无法提交';
        LEAVE proc;
    END IF;

    SELECT Status, Score, FlagSalt, FlagHash
    INTO v_ch_status, v_ch_score, v_salt, v_target
    FROM Challenges
    WHERE Chid = p_chid;
    IF v_ch_status IS NULL THEN
        SET p_message = '题目不存在';
        LEAVE proc;
    ELSEIF v_ch_status <> 'online' THEN
        SET p_message = '题目未上架，暂不可提交';
        LEAVE proc;
    END IF;

    SET v_flaghash = SHA2(CONCAT(p_flag, v_salt), 256);

    START TRANSACTION;
    SELECT COUNT(*) INTO v_solved FROM Solves WHERE Uid = p_uid AND Chid = p_chid;
    IF v_solved > 0 THEN
        INSERT INTO Submissions (Uid, Chid, FlagHash, IsCorrect)
        VALUES (p_uid, p_chid, v_flaghash, 1);
        COMMIT;
        SET p_result = 'duplicate', p_score = 0,
            p_message = '该题已解出，本次提交不重复计分';
        LEAVE proc;
    END IF;

    SET v_correct = (v_flaghash = v_target);
    INSERT INTO Submissions (Uid, Chid, FlagHash, IsCorrect)
    VALUES (p_uid, p_chid, v_flaghash, v_correct);
    SET v_subid = LAST_INSERT_ID();

    IF v_correct = 1 THEN
        INSERT INTO Solves (Uid, Chid, Subid, ScoreAwarded)
        VALUES (p_uid, p_chid, v_subid, v_ch_score);
        IF ROW_COUNT() = 1 THEN
            SET p_result = 'correct', p_score = v_ch_score,
                p_message = CONCAT('判定正确，本次得分 ', v_ch_score, ' 分');
        ELSE
            SET p_result = 'duplicate', p_score = 0,
                p_message = '该题已解出，本次提交不重复计分';
        END IF;
    ELSE
        SET p_result = 'wrong', p_score = 0, p_message = 'flag 不正确，可继续尝试';
    END IF;
    COMMIT;
END proc//
DELIMITER ;

-- ------------------------------------------------------------
-- 过程 5：个人答题记录。一次调用返回个人中心所需的全部明细
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_user_records;
DELIMITER //
CREATE PROCEDURE sp_user_records(IN p_uid INT)
proc: BEGIN
    DECLARE v_exists INT DEFAULT 0;

    SELECT COUNT(*) INTO v_exists FROM Users WHERE Uid = p_uid;
    IF v_exists = 0 THEN
        SELECT '用户不存在' AS 提示信息;
        LEAVE proc;
    END IF;

    SELECT s.Subid                      AS 提交编号,
           ca.Cname                     AS 分类,
           ch.Title                     AS 题名,
           ch.Score                     AS 题目分值,
           s.IsCorrect                  AS 是否答对,
           COALESCE(so.ScoreAwarded, 0) AS 本次得分,
           s.SubmittedAt                AS 提交时间
    FROM Submissions s
             JOIN Challenges ch ON s.Chid = ch.Chid
             JOIN Categories ca ON ch.Cid = ca.Cid
             LEFT JOIN Solves so ON so.Subid = s.Subid
    WHERE s.Uid = p_uid
    ORDER BY s.SubmittedAt;
END proc//
DELIMITER ;

-- ============================================================
-- 触发器：关键操作自动留痕
-- ============================================================

-- 触发器 1：注册成功即写入操作日志
DROP TRIGGER IF EXISTS trg_users_after_insert;
DELIMITER //
CREATE TRIGGER trg_users_after_insert
    AFTER INSERT
    ON Users
    FOR EACH ROW
BEGIN
    INSERT INTO OperationLogs (Uid, Action, Target, Detail)
    VALUES (NEW.Uid, '注册账号', NEW.Username,
            CONCAT('新用户注册，角色 ', NEW.Role, '，邮箱 ', NEW.Email));
END//
DELIMITER ;

-- 触发器 2：题目状态变更时记录操作人与新旧状态
DROP TRIGGER IF EXISTS trg_challenges_after_update;
DELIMITER //
CREATE TRIGGER trg_challenges_after_update
    AFTER UPDATE
    ON Challenges
    FOR EACH ROW
BEGIN
    IF NEW.Status <> OLD.Status THEN
        INSERT INTO OperationLogs (Uid, Action, Target, Detail)
        VALUES (COALESCE(@operator_uid, NEW.AuthorUid),
                CASE NEW.Status
                    WHEN 'online' THEN '题目上架'
                    WHEN 'offline' THEN '题目下线'
                    ELSE '题目转草稿' END,
                NEW.Title,
                CONCAT('状态由 ', OLD.Status, ' 变为 ', NEW.Status));
    END IF;
END//
DELIMITER ;

-- 触发器 3：计分成功即记录得分变动与变动后总分
DROP TRIGGER IF EXISTS trg_solves_after_insert;
DELIMITER //
CREATE TRIGGER trg_solves_after_insert
    AFTER INSERT
    ON Solves
    FOR EACH ROW
BEGIN
    DECLARE v_total INT DEFAULT 0;

    SELECT COALESCE(SUM(ScoreAwarded), 0) INTO v_total FROM Solves WHERE Uid = NEW.Uid;
    INSERT INTO ScoreLogs (Uid, Chid, DeltaScore, TotalAfter, Action, OccurredAt)
    VALUES (NEW.Uid, NEW.Chid, NEW.ScoreAwarded, v_total, 'solve', NEW.SolvedAt);
END//
DELIMITER ;

-- ============================================================
-- 演示数据
-- 用户编号：1 为管理员，2 至 11 依次为 zhangsan、lisi、wangwu、zhaoliu、sunqi、
--           zhouba、wujiu、zhengshi、chenyi、xuer
-- 演示口令盐由用户名推导，真实注册由 sp_register_user 生成随机盐。
-- ============================================================

INSERT INTO Categories (Cname, Cdesc)
VALUES ('Pwn', '二进制漏洞利用'),
       ('Web', 'Web 应用安全'),
       ('Reverse', '逆向工程'),
       ('Crypto', '密码学'),
       ('Misc', '杂项与取证');

INSERT INTO Users (Username, PasswordHash, Salt, Email, Role)
VALUES ('admin', '', '', 'admin@ctf.edu', 'admin'),
       ('zhangsan', '', '', 'zhangsan@ctf.edu', 'student'),
       ('lisi', '', '', 'lisi@ctf.edu', 'student'),
       ('wangwu', '', '', 'wangwu@ctf.edu', 'student'),
       ('zhaoliu', '', '', 'zhaoliu@ctf.edu', 'student'),
       ('sunqi', '', '', 'sunqi@ctf.edu', 'student'),
       ('zhouba', '', '', 'zhouba@ctf.edu', 'student'),
       ('wujiu', '', '', 'wujiu@ctf.edu', 'student'),
       ('zhengshi', '', '', 'zhengshi@ctf.edu', 'student'),
       ('chenyi', '', '', 'chenyi@ctf.edu', 'student'),
       ('xuer', '', '', 'xuer@ctf.edu', 'student');

-- 口令盐按用户名生成，口令散列再由本行盐计算
UPDATE Users SET Salt = LEFT(SHA2(CONCAT('ctf-user-', Username), 256), 32);
UPDATE Users
SET PasswordHash = SHA2(CONCAT(IF(Role = 'admin', 'Admin@123', 'Pass@123'), Salt), 256);

    -- 题目先录入基本属性，flag 散列随后由临时清单统一生成
INSERT INTO Challenges (Cid, Title, Description, Difficulty, Score, FlagHash, FlagSalt,
                        Attachment, Status, AuthorUid, PublishedAt)
VALUES (1, 'Welcome Pwn',
        '栈溢出入门：定位返回地址并改写为后门函数地址。', 1, 100, '', '',
        'attachments/pwn01.zip', 'online', 1, '2026-09-13 10:00:00'),
       (1, 'ret2libc 基础',
        '在关闭 system 符号的二进制中构造 ret2libc 利用链。', 3, 300, '', '',
        'attachments/pwn02.zip', 'online', 1, '2026-09-13 10:05:00'),
       (1, '堆溢出入门',
        '利用堆块溢出改写相邻结构体函数指针。', 4, 400, '', '',
        'attachments/pwn03.zip', 'online', 1, '2026-09-13 10:10:00'),
       (2, 'SQL 注入初探',
        '登录框存在注入点，绕过口令校验取得管理员身份。', 2, 200, '', '',
        'attachments/web01.zip', 'online', 1, '2026-09-13 10:15:00'),
       (2, '文件包含',
        '通过文件包含读取服务器上的 flag 文件。', 2, 250, '', '',
        'attachments/web02.zip', 'online', 1, '2026-09-13 10:20:00'),
       (2, 'JWT 伪造',
        '密钥强度不足的 JWT 可被离线爆破并伪造管理员令牌。', 3, 350, '', '',
        'attachments/web03.zip', 'online', 1, '2026-09-13 10:25:00'),
       (3, '简单异或',
        '定位校验函数中的异或密钥并还原明文。', 1, 150, '', '',
        'attachments/rev01.zip', 'online', 1, '2026-09-13 10:30:00'),
       (3, '迷宫题',
        '从二进制中提取地图数据并搜索可行路径。', 3, 300, '', '',
        'attachments/rev02.zip', 'online', 1, '2026-09-13 10:35:00'),
       (3, 'VM 逆向',
        '还原自定义虚拟机指令集并推导校验流程。', 5, 450, '', '',
        'attachments/rev03.zip', 'online', 1, '2026-09-13 10:40:00'),
       (4, '凯撒密码',
        '对密文进行移位枚举，识别可读结果。', 1, 100, '', '',
        'attachments/crypto01.zip', 'online', 1, '2026-09-13 10:45:00'),
       (4, 'RSA 小指数',
        '公钥指数过小且未填充，可直接开方还原明文。', 3, 300, '', '',
        'attachments/crypto02.zip', 'online', 1, '2026-09-13 10:50:00'),
       (4, '分组模式',
        'ECB 模式下相同明文分组产生相同密文分组，可逐字节恢复。', 3, 350, '', '',
        'attachments/crypto03.zip', 'online', 1, '2026-09-13 10:55:00'),
       (5, '隐写入门',
        '图片末尾附加数据中藏有 flag。', 1, 150, '', '',
        'attachments/misc01.zip', 'online', 1, '2026-09-13 11:00:00'),
       (5, '流量分析',
        '从抓包文件中还原被分片传输的 flag。', 2, 250, '', '',
        'attachments/misc02.zip', 'offline', 1, NULL),
       (5, '日志排查',
        '从 Web 访问日志中定位注入成功的请求。', 2, 200, '', '',
        'attachments/misc03.zip', 'draft', 1, NULL),
       (2, '反序列化',
        '构造恶意序列化数据触发读取 flag 的调用链。', 5, 500, '', '',
        'attachments/web04.zip', 'draft', 1, NULL);

-- 演示 flag 明文只在本临时清单中出现，用于生成散列；库中保存的是加盐散列
CREATE TEMPORARY TABLE tmp_demo_flags (Chid INT PRIMARY KEY, PlainFlag VARCHAR(128));
INSERT INTO tmp_demo_flags (Chid, PlainFlag) VALUES
(1, 'flag{w3lc0me_pwn}'),
       (2, 'flag{r3t2l1bc_b4s1c}'),
       (3, 'flag{h34p_0v3rfl0w}'),
       (4, 'flag{sql_1nj3ct10n}'),
       (5, 'flag{f1l3_1nclus10n}'),
       (6, 'flag{jwt_f0rg3ry}'),
       (7, 'flag{x0r_1s_34sy}'),
       (8, 'flag{m4z3_w4lk3r}'),
       (9, 'flag{vm_r3v3r53}'),
       (10, 'flag{c4es4r_c1ph3r}'),
       (11, 'flag{sm4ll_3xp0n3nt}'),
       (12, 'flag{3cb_p4tt3rn}'),
       (13, 'flag{st3g0_1ntr0}'),
       (14, 'flag{tr4ff1c_4n4lys1s}'),
       (15, 'flag{l0g_4ud1t}'),
       (16, 'flag{un53r14l1z3_m3}');

UPDATE Challenges SET FlagSalt = LEFT(SHA2(CONCAT('ctf-challenge-', Chid), 256), 32);
UPDATE Challenges c
    JOIN tmp_demo_flags f ON f.Chid = c.Chid
SET c.FlagHash = SHA2(CONCAT(f.PlainFlag, c.FlagSalt), 256);
DROP TEMPORARY TABLE tmp_demo_flags;

-- 错误提交：记录尝试过程，不计分
INSERT INTO Submissions (Uid, Chid, FlagHash, IsCorrect, SubmittedAt)
VALUES (4, 2, SHA2('flag{wrong_guess}', 256), 0, '2026-09-15 08:00:00'),
       (4, 2, SHA2('flag{wrong_guess}', 256), 0, '2026-09-15 08:20:00'),
       (3, 5, SHA2('flag{wrong_guess}', 256), 0, '2026-09-16 09:00:00'),
       (6, 6, SHA2('flag{wrong_guess}', 256), 0, '2026-09-17 09:10:00'),
       (10, 6, SHA2('flag{wrong_guess}', 256), 0, '2026-09-18 09:30:00'),
       (11, 1, SHA2('flag{wrong_guess}', 256), 0, '2026-09-19 11:00:00');

-- 正确提交：flag 散列直接取自题目表，保证与题目定义一致
INSERT INTO Submissions (Uid, Chid, FlagHash, IsCorrect, SubmittedAt)
SELECT v.Uid, v.Chid, c.FlagHash, 1, v.SubmittedAt
FROM (SELECT 2 AS Uid, 1 AS Chid, CAST('2026-09-14 09:12:00' AS DATETIME) AS SubmittedAt
      UNION ALL SELECT 2, 4, '2026-09-14 09:25:00'
      UNION ALL SELECT 2, 7, '2026-09-15 10:05:00'
      UNION ALL SELECT 2, 10, '2026-09-15 10:20:00'
      UNION ALL SELECT 3, 1, '2026-09-14 09:30:00'
      UNION ALL SELECT 3, 10, '2026-09-15 11:00:00'
      UNION ALL SELECT 4, 1, '2026-09-14 10:00:00'
      UNION ALL SELECT 5, 1, '2026-09-14 09:05:00'
      UNION ALL SELECT 5, 4, '2026-09-14 09:40:00'
      UNION ALL SELECT 5, 7, '2026-09-15 09:50:00'
      UNION ALL SELECT 5, 10, '2026-09-15 10:10:00'
      UNION ALL SELECT 6, 7, '2026-09-16 15:00:00'
      UNION ALL SELECT 6, 10, '2026-09-16 15:30:00'
      UNION ALL SELECT 7, 4, '2026-09-15 16:00:00'
      UNION ALL SELECT 7, 10, '2026-09-15 16:20:00'
      UNION ALL SELECT 8, 1, '2026-09-14 09:02:00'
      UNION ALL SELECT 8, 4, '2026-09-14 09:35:00'
      UNION ALL SELECT 8, 5, '2026-09-15 14:00:00'
      UNION ALL SELECT 8, 6, '2026-09-17 10:00:00'
      UNION ALL SELECT 9, 1, '2026-09-18 11:00:00'
      UNION ALL SELECT 10, 1, '2026-09-19 09:00:00'
      UNION ALL SELECT 10, 13, '2026-09-19 10:00:00') v
         JOIN Challenges c ON c.Chid = v.Chid;

-- 计分记录：由正确提交派生，分值取自题目表；插入过程触发积分日志
INSERT INTO Solves (Uid, Chid, Subid, ScoreAwarded, SolvedAt)
SELECT s.Uid, s.Chid, s.Subid, c.Score, s.SubmittedAt
FROM Submissions s
         JOIN Challenges c ON s.Chid = c.Chid
WHERE s.IsCorrect = 1;
