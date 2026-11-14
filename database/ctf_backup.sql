-- MySQL dump 10.13  Distrib 8.4.7, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: ctf
-- ------------------------------------------------------
-- Server version	8.4.7

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `ctf`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `ctf` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `ctf`;

--
-- Table structure for table `Categories`
--

DROP TABLE IF EXISTS `Categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Categories` (
  `Cid` int NOT NULL AUTO_INCREMENT COMMENT '分类编号',
  `Cname` varchar(16) NOT NULL COMMENT '分类名称',
  `Cdesc` varchar(100) DEFAULT NULL COMMENT '分类说明',
  PRIMARY KEY (`Cid`),
  UNIQUE KEY `Cname` (`Cname`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='题目分类';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Categories`
--

LOCK TABLES `Categories` WRITE;
/*!40000 ALTER TABLE `Categories` DISABLE KEYS */;
INSERT INTO `Categories` VALUES (1,'Pwn','二进制漏洞利用'),(2,'Web','Web 应用安全'),(3,'Reverse','逆向工程'),(4,'Crypto','密码学'),(5,'Misc','杂项与取证');
/*!40000 ALTER TABLE `Categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Challenges`
--

DROP TABLE IF EXISTS `Challenges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Challenges` (
  `Chid` int NOT NULL AUTO_INCREMENT COMMENT '题目编号',
  `Cid` int NOT NULL COMMENT '所属分类',
  `Title` varchar(64) NOT NULL COMMENT '题名',
  `Description` varchar(500) DEFAULT NULL COMMENT '题目描述',
  `Difficulty` tinyint NOT NULL DEFAULT '1' COMMENT '难度 1 至 5',
  `Score` int NOT NULL COMMENT '基础分值',
  `FlagHash` char(64) NOT NULL COMMENT 'flag 散列 SHA2(flag+盐,256)',
  `FlagSalt` char(32) NOT NULL COMMENT 'flag 盐',
  `Attachment` varchar(128) DEFAULT NULL COMMENT '附件路径',
  `Status` enum('draft','online','offline') NOT NULL DEFAULT 'draft' COMMENT '上架状态',
  `AuthorUid` int NOT NULL COMMENT '录题管理员',
  `CreatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间',
  `PublishedAt` datetime DEFAULT NULL COMMENT '上架时间',
  PRIMARY KEY (`Chid`),
  KEY `idx_challenge_filter` (`Cid`,`Difficulty`,`Status`),
  KEY `idx_challenge_title` (`Title`),
  KEY `fk_challenge_author` (`AuthorUid`),
  CONSTRAINT `fk_challenge_author` FOREIGN KEY (`AuthorUid`) REFERENCES `Users` (`Uid`),
  CONSTRAINT `fk_challenge_category` FOREIGN KEY (`Cid`) REFERENCES `Categories` (`Cid`),
  CONSTRAINT `ck_challenge_difficulty` CHECK ((`Difficulty` between 1 and 5)),
  CONSTRAINT `ck_challenge_score` CHECK ((`Score` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='训练题目';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Challenges`
--

LOCK TABLES `Challenges` WRITE;
/*!40000 ALTER TABLE `Challenges` DISABLE KEYS */;
INSERT INTO `Challenges` VALUES (1,1,'Welcome Pwn','栈溢出入门：定位返回地址并改写为后门函数地址。',1,100,'6330003ef1195f80f3551678a9bc07927ac4c88c2376a66633876d72f1588661','73a80978efcc893a279a41c30e0b0917','attachments/pwn01.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:00:00'),(2,1,'ret2libc 基础','在关闭 system 符号的二进制中构造 ret2libc 利用链。',3,300,'7a82a7f763bb745a430eddb336df59e29a3a26b805c463254b4e757a104581e2','9aca1d0d8bb1b3c1e4fbf3d1b2a04050','attachments/pwn02.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:05:00'),(3,1,'堆溢出入门','利用堆块溢出改写相邻结构体函数指针。',4,400,'67f14287c753438810537b6fccf9b1a5c8e292b0ac9a3ed9079bcf9a57fc7ac7','fd07edf4190ef62a8fb7f7df4c145350','attachments/pwn03.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:10:00'),(4,2,'SQL 注入初探','登录框存在注入点，绕过口令校验取得管理员身份。',2,200,'282639a8ea414957495275b5ae795979fc2fe7a3dfba338634f9f45bdf10e269','61cc28c0cdef943d9582f680b75b6a51','attachments/web01.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:15:00'),(5,2,'文件包含','通过文件包含读取服务器上的 flag 文件。',2,250,'62975a902d56d6f391e4117fcaaf79f89506c523977a91a6edcaf6584b281a92','98ef2aa66a40228a30764d88d0def343','attachments/web02.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:20:00'),(6,2,'JWT 伪造','密钥强度不足的 JWT 可被离线爆破并伪造管理员令牌。',3,350,'f117142c8ea9df4017b2574f63db564bddd3471337614dc86e55c251c44e987d','d1b0f27887e765df46c7e26013089f5a','attachments/web03.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:25:00'),(7,3,'简单异或','定位校验函数中的异或密钥并还原明文。',1,150,'63d912c8cba60333fcf7c460f5fdf85f07d819da41180c2a2b72d35573b1488d','6fd326a6420fcef85128e4e54bf7f412','attachments/rev01.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:30:00'),(8,3,'迷宫题','从二进制中提取地图数据并搜索可行路径。',3,300,'d994b6f311823be5cd8807318ca2d3b5b06cbbddc6c24852776491cd2813eb51','132b8dcdb637cec2c2c78f9ed1c4b715','attachments/rev02.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:35:00'),(9,3,'VM 逆向','还原自定义虚拟机指令集并推导校验流程。',5,450,'68870b9d3ca93115f23c6e61a5f4f62b3fc9b8fac8df777ab1e78fe74844c409','443a7197af70ccc2ab845e536db967cb','attachments/rev03.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:40:00'),(10,4,'凯撒密码','对密文进行移位枚举，识别可读结果。',1,100,'99a81d9771575501dd4535f6597260f97f22a6b305fad94ae05bad6cd4d4c097','31a43069793d836a6a121551a2adb12d','attachments/crypto01.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:45:00'),(11,4,'RSA 小指数','公钥指数过小且未填充，可直接开方还原明文。',3,300,'fe02f747ec8b09a4d75e93554383a459e4deee9a08b0035941006e773a47a300','13d5c30a63f72e950a9d05997d47222a','attachments/crypto02.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:50:00'),(12,4,'分组模式','ECB 模式下相同明文分组产生相同密文分组，可逐字节恢复。',3,350,'9ae525e6a88ec81e11c2706f8ce4daa746e12115927a9a1f7999bbc00aa92210','316a65f1a7d7bb99c0b5d82fe5219c90','attachments/crypto03.zip','online',1,'2026-11-14 14:03:19','2026-09-13 10:55:00'),(13,5,'隐写入门','图片末尾附加数据中藏有 flag。',1,150,'026d239093094888715dde3b10f0005bf4694b063cf84b2d07f996af5dc3c9d6','7d1d574fd9a2b3c2c8f2ee80fa36c221','attachments/misc01.zip','online',1,'2026-11-14 14:03:19','2026-09-13 11:00:00'),(14,5,'流量分析','从抓包文件中还原被分片传输的 flag。',2,250,'723c0fc8d843396a7d4e62e12f134064b29961dc458c7107df974e2bc794b4a7','56aae00b4cf07205a9196a3ba15736aa','attachments/misc02.zip','offline',1,'2026-11-14 14:03:19',NULL),(15,5,'日志排查','从 Web 访问日志中定位注入成功的请求。',2,200,'1d2f77879711c03092d425611dc38d622e50eb54743d42d93e2ff6e1f5bd267d','565bfb044fb645840cf84c8fc7a85ef5','attachments/misc03.zip','draft',1,'2026-11-14 14:03:19',NULL),(16,2,'反序列化','构造恶意序列化数据触发读取 flag 的调用链。',5,500,'7467c007f92f0834f9862fb2319d6960371c284f5d0f3d26425cc87dc10d0af8','7196e2c1b1d5a835e0d147c14ee48751','attachments/web04.zip','draft',1,'2026-11-14 14:03:19',NULL);
/*!40000 ALTER TABLE `Challenges` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_challenges_after_update` AFTER UPDATE ON `Challenges` FOR EACH ROW BEGIN
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `OperationLogs`
--

DROP TABLE IF EXISTS `OperationLogs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `OperationLogs` (
  `Opid` bigint NOT NULL AUTO_INCREMENT COMMENT '日志编号',
  `Uid` int NOT NULL COMMENT '操作人',
  `Action` varchar(32) NOT NULL COMMENT '操作类型',
  `Target` varchar(64) DEFAULT NULL COMMENT '操作对象',
  `Detail` varchar(200) DEFAULT NULL COMMENT '操作说明',
  `OccurredAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
  PRIMARY KEY (`Opid`),
  KEY `idx_operation_user` (`Uid`,`OccurredAt`),
  CONSTRAINT `fk_operation_user` FOREIGN KEY (`Uid`) REFERENCES `Users` (`Uid`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='管理操作日志';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `OperationLogs`
--

LOCK TABLES `OperationLogs` WRITE;
/*!40000 ALTER TABLE `OperationLogs` DISABLE KEYS */;
INSERT INTO `OperationLogs` VALUES (1,1,'注册账号','admin','新用户注册，角色 admin，邮箱 admin@ctf.edu','2026-11-14 14:03:19'),(2,2,'注册账号','zhangsan','新用户注册，角色 student，邮箱 zhangsan@ctf.edu','2026-11-14 14:03:19'),(3,3,'注册账号','lisi','新用户注册，角色 student，邮箱 lisi@ctf.edu','2026-11-14 14:03:19'),(4,4,'注册账号','wangwu','新用户注册，角色 student，邮箱 wangwu@ctf.edu','2026-11-14 14:03:19'),(5,5,'注册账号','zhaoliu','新用户注册，角色 student，邮箱 zhaoliu@ctf.edu','2026-11-14 14:03:19'),(6,6,'注册账号','sunqi','新用户注册，角色 student，邮箱 sunqi@ctf.edu','2026-11-14 14:03:19'),(7,7,'注册账号','zhouba','新用户注册，角色 student，邮箱 zhouba@ctf.edu','2026-11-14 14:03:19'),(8,8,'注册账号','wujiu','新用户注册，角色 student，邮箱 wujiu@ctf.edu','2026-11-14 14:03:19'),(9,9,'注册账号','zhengshi','新用户注册，角色 student，邮箱 zhengshi@ctf.edu','2026-11-14 14:03:19'),(10,10,'注册账号','chenyi','新用户注册，角色 student，邮箱 chenyi@ctf.edu','2026-11-14 14:03:19'),(11,11,'注册账号','xuer','新用户注册，角色 student，邮箱 xuer@ctf.edu','2026-11-14 14:03:19');
/*!40000 ALTER TABLE `OperationLogs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ScoreLogs`
--

DROP TABLE IF EXISTS `ScoreLogs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ScoreLogs` (
  `LogId` bigint NOT NULL AUTO_INCREMENT COMMENT '日志编号',
  `Uid` int NOT NULL COMMENT '得分人',
  `Chid` int NOT NULL COMMENT '题目编号',
  `DeltaScore` int NOT NULL COMMENT '本次得分变动',
  `TotalAfter` int NOT NULL COMMENT '变动后累计总分',
  `Action` varchar(16) NOT NULL DEFAULT 'solve' COMMENT '动作类型',
  `OccurredAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
  PRIMARY KEY (`LogId`),
  KEY `idx_scorelog_user` (`Uid`,`OccurredAt`),
  KEY `fk_scorelog_challenge` (`Chid`),
  CONSTRAINT `fk_scorelog_challenge` FOREIGN KEY (`Chid`) REFERENCES `Challenges` (`Chid`),
  CONSTRAINT `fk_scorelog_user` FOREIGN KEY (`Uid`) REFERENCES `Users` (`Uid`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='积分变动日志';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ScoreLogs`
--

LOCK TABLES `ScoreLogs` WRITE;
/*!40000 ALTER TABLE `ScoreLogs` DISABLE KEYS */;
INSERT INTO `ScoreLogs` VALUES (1,2,1,100,100,'solve','2026-09-14 09:12:00'),(2,2,4,200,300,'solve','2026-09-14 09:25:00'),(3,2,7,150,450,'solve','2026-09-15 10:05:00'),(4,2,10,100,550,'solve','2026-09-15 10:20:00'),(5,3,1,100,100,'solve','2026-09-14 09:30:00'),(6,3,10,100,200,'solve','2026-09-15 11:00:00'),(7,4,1,100,100,'solve','2026-09-14 10:00:00'),(8,5,1,100,100,'solve','2026-09-14 09:05:00'),(9,5,4,200,300,'solve','2026-09-14 09:40:00'),(10,5,7,150,450,'solve','2026-09-15 09:50:00'),(11,5,10,100,550,'solve','2026-09-15 10:10:00'),(12,6,7,150,150,'solve','2026-09-16 15:00:00'),(13,6,10,100,250,'solve','2026-09-16 15:30:00'),(14,7,4,200,200,'solve','2026-09-15 16:00:00'),(15,7,10,100,300,'solve','2026-09-15 16:20:00'),(16,8,1,100,100,'solve','2026-09-14 09:02:00'),(17,8,4,200,300,'solve','2026-09-14 09:35:00'),(18,8,5,250,550,'solve','2026-09-15 14:00:00'),(19,8,6,350,900,'solve','2026-09-17 10:00:00'),(20,9,1,100,100,'solve','2026-09-18 11:00:00'),(21,10,1,100,100,'solve','2026-09-19 09:00:00'),(22,10,13,150,250,'solve','2026-09-19 10:00:00');
/*!40000 ALTER TABLE `ScoreLogs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Solves`
--

DROP TABLE IF EXISTS `Solves`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Solves` (
  `Uid` int NOT NULL COMMENT '解题人',
  `Chid` int NOT NULL COMMENT '题目编号',
  `Subid` bigint NOT NULL COMMENT '首次正确提交编号',
  `ScoreAwarded` int NOT NULL COMMENT '本次得分',
  `SolvedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '解出时间',
  PRIMARY KEY (`Uid`,`Chid`),
  UNIQUE KEY `uk_solves_submission` (`Subid`),
  KEY `idx_solves_challenge` (`Chid`),
  CONSTRAINT `fk_solves_challenge` FOREIGN KEY (`Chid`) REFERENCES `Challenges` (`Chid`),
  CONSTRAINT `fk_solves_submission` FOREIGN KEY (`Subid`) REFERENCES `Submissions` (`Subid`),
  CONSTRAINT `fk_solves_user` FOREIGN KEY (`Uid`) REFERENCES `Users` (`Uid`),
  CONSTRAINT `ck_solves_score` CHECK ((`ScoreAwarded` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='解题与计分';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Solves`
--

LOCK TABLES `Solves` WRITE;
/*!40000 ALTER TABLE `Solves` DISABLE KEYS */;
INSERT INTO `Solves` VALUES (2,1,7,100,'2026-09-14 09:12:00'),(2,4,8,200,'2026-09-14 09:25:00'),(2,7,9,150,'2026-09-15 10:05:00'),(2,10,10,100,'2026-09-15 10:20:00'),(3,1,11,100,'2026-09-14 09:30:00'),(3,10,12,100,'2026-09-15 11:00:00'),(4,1,13,100,'2026-09-14 10:00:00'),(5,1,14,100,'2026-09-14 09:05:00'),(5,4,15,200,'2026-09-14 09:40:00'),(5,7,16,150,'2026-09-15 09:50:00'),(5,10,17,100,'2026-09-15 10:10:00'),(6,7,18,150,'2026-09-16 15:00:00'),(6,10,19,100,'2026-09-16 15:30:00'),(7,4,20,200,'2026-09-15 16:00:00'),(7,10,21,100,'2026-09-15 16:20:00'),(8,1,22,100,'2026-09-14 09:02:00'),(8,4,23,200,'2026-09-14 09:35:00'),(8,5,24,250,'2026-09-15 14:00:00'),(8,6,25,350,'2026-09-17 10:00:00'),(9,1,26,100,'2026-09-18 11:00:00'),(10,1,27,100,'2026-09-19 09:00:00'),(10,13,28,150,'2026-09-19 10:00:00');
/*!40000 ALTER TABLE `Solves` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_solves_after_insert` AFTER INSERT ON `Solves` FOR EACH ROW BEGIN
    DECLARE v_total INT DEFAULT 0;

    SELECT COALESCE(SUM(ScoreAwarded), 0) INTO v_total FROM Solves WHERE Uid = NEW.Uid;
    INSERT INTO ScoreLogs (Uid, Chid, DeltaScore, TotalAfter, Action, OccurredAt)
    VALUES (NEW.Uid, NEW.Chid, NEW.ScoreAwarded, v_total, 'solve', NEW.SolvedAt);
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `Submissions`
--

DROP TABLE IF EXISTS `Submissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Submissions` (
  `Subid` bigint NOT NULL AUTO_INCREMENT COMMENT '提交编号',
  `Uid` int NOT NULL COMMENT '提交人',
  `Chid` int NOT NULL COMMENT '题目编号',
  `FlagHash` char(64) NOT NULL COMMENT '本次提交 flag 的散列',
  `IsCorrect` tinyint NOT NULL DEFAULT '0' COMMENT '是否正确 1/0',
  `SubmittedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
  PRIMARY KEY (`Subid`),
  KEY `idx_submission_user` (`Uid`,`SubmittedAt`),
  KEY `idx_submission_challenge` (`Chid`,`IsCorrect`),
  CONSTRAINT `fk_submission_challenge` FOREIGN KEY (`Chid`) REFERENCES `Challenges` (`Chid`),
  CONSTRAINT `fk_submission_user` FOREIGN KEY (`Uid`) REFERENCES `Users` (`Uid`),
  CONSTRAINT `ck_submission_correct` CHECK ((`IsCorrect` in (0,1)))
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='flag 提交记录';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Submissions`
--

LOCK TABLES `Submissions` WRITE;
/*!40000 ALTER TABLE `Submissions` DISABLE KEYS */;
INSERT INTO `Submissions` VALUES (1,4,2,'f2c9bb820924800aa64bd119814a40b3378e75f8ba753f758ff6ebfbad6ada92',0,'2026-09-15 08:00:00'),(2,4,2,'f2c9bb820924800aa64bd119814a40b3378e75f8ba753f758ff6ebfbad6ada92',0,'2026-09-15 08:20:00'),(3,3,5,'f2c9bb820924800aa64bd119814a40b3378e75f8ba753f758ff6ebfbad6ada92',0,'2026-09-16 09:00:00'),(4,6,6,'f2c9bb820924800aa64bd119814a40b3378e75f8ba753f758ff6ebfbad6ada92',0,'2026-09-17 09:10:00'),(5,10,6,'f2c9bb820924800aa64bd119814a40b3378e75f8ba753f758ff6ebfbad6ada92',0,'2026-09-18 09:30:00'),(6,11,1,'f2c9bb820924800aa64bd119814a40b3378e75f8ba753f758ff6ebfbad6ada92',0,'2026-09-19 11:00:00'),(7,2,1,'6330003ef1195f80f3551678a9bc07927ac4c88c2376a66633876d72f1588661',1,'2026-09-14 09:12:00'),(8,2,4,'282639a8ea414957495275b5ae795979fc2fe7a3dfba338634f9f45bdf10e269',1,'2026-09-14 09:25:00'),(9,2,7,'63d912c8cba60333fcf7c460f5fdf85f07d819da41180c2a2b72d35573b1488d',1,'2026-09-15 10:05:00'),(10,2,10,'99a81d9771575501dd4535f6597260f97f22a6b305fad94ae05bad6cd4d4c097',1,'2026-09-15 10:20:00'),(11,3,1,'6330003ef1195f80f3551678a9bc07927ac4c88c2376a66633876d72f1588661',1,'2026-09-14 09:30:00'),(12,3,10,'99a81d9771575501dd4535f6597260f97f22a6b305fad94ae05bad6cd4d4c097',1,'2026-09-15 11:00:00'),(13,4,1,'6330003ef1195f80f3551678a9bc07927ac4c88c2376a66633876d72f1588661',1,'2026-09-14 10:00:00'),(14,5,1,'6330003ef1195f80f3551678a9bc07927ac4c88c2376a66633876d72f1588661',1,'2026-09-14 09:05:00'),(15,5,4,'282639a8ea414957495275b5ae795979fc2fe7a3dfba338634f9f45bdf10e269',1,'2026-09-14 09:40:00'),(16,5,7,'63d912c8cba60333fcf7c460f5fdf85f07d819da41180c2a2b72d35573b1488d',1,'2026-09-15 09:50:00'),(17,5,10,'99a81d9771575501dd4535f6597260f97f22a6b305fad94ae05bad6cd4d4c097',1,'2026-09-15 10:10:00'),(18,6,7,'63d912c8cba60333fcf7c460f5fdf85f07d819da41180c2a2b72d35573b1488d',1,'2026-09-16 15:00:00'),(19,6,10,'99a81d9771575501dd4535f6597260f97f22a6b305fad94ae05bad6cd4d4c097',1,'2026-09-16 15:30:00'),(20,7,4,'282639a8ea414957495275b5ae795979fc2fe7a3dfba338634f9f45bdf10e269',1,'2026-09-15 16:00:00'),(21,7,10,'99a81d9771575501dd4535f6597260f97f22a6b305fad94ae05bad6cd4d4c097',1,'2026-09-15 16:20:00'),(22,8,1,'6330003ef1195f80f3551678a9bc07927ac4c88c2376a66633876d72f1588661',1,'2026-09-14 09:02:00'),(23,8,4,'282639a8ea414957495275b5ae795979fc2fe7a3dfba338634f9f45bdf10e269',1,'2026-09-14 09:35:00'),(24,8,5,'62975a902d56d6f391e4117fcaaf79f89506c523977a91a6edcaf6584b281a92',1,'2026-09-15 14:00:00'),(25,8,6,'f117142c8ea9df4017b2574f63db564bddd3471337614dc86e55c251c44e987d',1,'2026-09-17 10:00:00'),(26,9,1,'6330003ef1195f80f3551678a9bc07927ac4c88c2376a66633876d72f1588661',1,'2026-09-18 11:00:00'),(27,10,1,'6330003ef1195f80f3551678a9bc07927ac4c88c2376a66633876d72f1588661',1,'2026-09-19 09:00:00'),(28,10,13,'026d239093094888715dde3b10f0005bf4694b063cf84b2d07f996af5dc3c9d6',1,'2026-09-19 10:00:00');
/*!40000 ALTER TABLE `Submissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Users`
--

DROP TABLE IF EXISTS `Users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Users` (
  `Uid` int NOT NULL AUTO_INCREMENT COMMENT '用户编号',
  `Username` varchar(32) NOT NULL COMMENT '登录名，全局唯一',
  `PasswordHash` char(64) NOT NULL COMMENT '口令散列 SHA2(口令+盐,256)',
  `Salt` char(32) NOT NULL COMMENT '口令盐',
  `Email` varchar(64) NOT NULL COMMENT '电子邮箱',
  `Role` enum('student','admin') NOT NULL DEFAULT 'student' COMMENT '角色',
  `Status` enum('active','disabled') NOT NULL DEFAULT 'active' COMMENT '账号状态',
  `CreatedAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  PRIMARY KEY (`Uid`),
  UNIQUE KEY `Username` (`Username`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Users`
--

LOCK TABLES `Users` WRITE;
/*!40000 ALTER TABLE `Users` DISABLE KEYS */;
INSERT INTO `Users` VALUES (1,'admin','b8c6c29154e6c53027536e659e7d2d4a062352cc7ca1df6f281f57b7e62823e4','9828f78d15994390fa1c355ae7b35a34','admin@ctf.edu','admin','active','2026-11-14 14:03:19'),(2,'zhangsan','91b390c2d140bbeb4d9567814499b576085701d9aa9afb7506125ea2b8c34cd9','b1ee3cabb631080fbbf8db38425663e8','zhangsan@ctf.edu','student','active','2026-11-14 14:03:19'),(3,'lisi','dfb46e7e91e088935b3037de531dce6a705748b6ea73afb9fad91f3568ad460b','0e5123e676d3a6c848ba3de6821f30cc','lisi@ctf.edu','student','active','2026-11-14 14:03:19'),(4,'wangwu','8e3181e5501dc8e1aefc6d5dc16441bf956b52773d19d2fd7fbccea8f519c661','5a43afcecaf3672f322444dba5709cc5','wangwu@ctf.edu','student','active','2026-11-14 14:03:19'),(5,'zhaoliu','90fb367fce99fb3c582c34f7d16f48bcd7a474c15ec6a5b9bce751a49d1dd1e8','4778321df9658eeffce1ba75b0cca160','zhaoliu@ctf.edu','student','active','2026-11-14 14:03:19'),(6,'sunqi','16a9b90d5590c38fc4d0464129711fcbbeaf445a684b26b3fba815a321f47c56','d19b04611a8fedc1fe31ede220f811f7','sunqi@ctf.edu','student','active','2026-11-14 14:03:19'),(7,'zhouba','0bbb1879d74b03e02c80e88c245fdc0fa331d8fa8d27ae1ae30f80deae8bedd4','5d0e54f45a8617a1f72dd6a3df67c043','zhouba@ctf.edu','student','active','2026-11-14 14:03:19'),(8,'wujiu','d7f394c204ffbb3a99b882ece1e2ca192ba0660fe7504318299dd890d42bbc4d','ce9d461fc50c1d6ee63cf4729da53c6d','wujiu@ctf.edu','student','active','2026-11-14 14:03:19'),(9,'zhengshi','479fe11ad36e10ae64b7fae7630c08d2441db0860f00d0b210602bd71c53fb2e','13b6439a99a2a35a3d91ad9eba957c2b','zhengshi@ctf.edu','student','active','2026-11-14 14:03:19'),(10,'chenyi','fbd03453bd7cffea5e545f48f3a268afc2dc6fed2810263745913a481e5e8a2b','129616a95a84fbd693d90bca910135b8','chenyi@ctf.edu','student','active','2026-11-14 14:03:19'),(11,'xuer','c8605de24c57e03d9ffe8f5b5313b41ccc3bcf7d9471d99aa0f4bf9f64ff7567','3887e652db999403d2c9baf67d61c541','xuer@ctf.edu','student','active','2026-11-14 14:03:19');
/*!40000 ALTER TABLE `Users` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_users_after_insert` AFTER INSERT ON `Users` FOR EACH ROW BEGIN
    INSERT INTO OperationLogs (Uid, Action, Target, Detail)
    VALUES (NEW.Uid, '注册账号', NEW.Username,
            CONCAT('新用户注册，角色 ', NEW.Role, '，邮箱 ', NEW.Email));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Temporary view structure for view `v_category_rank`
--

DROP TABLE IF EXISTS `v_category_rank`;
/*!50001 DROP VIEW IF EXISTS `v_category_rank`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_category_rank` AS SELECT 
 1 AS `分类编号`,
 1 AS `分类`,
 1 AS `名次`,
 1 AS `用户编号`,
 1 AS `用户名`,
 1 AS `分类得分`,
 1 AS `解题数`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_challenge_public`
--

DROP TABLE IF EXISTS `v_challenge_public`;
/*!50001 DROP VIEW IF EXISTS `v_challenge_public`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_challenge_public` AS SELECT 
 1 AS `题目编号`,
 1 AS `分类`,
 1 AS `题名`,
 1 AS `题目描述`,
 1 AS `难度`,
 1 AS `分值`,
 1 AS `附件`,
 1 AS `上架时间`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_score_detail`
--

DROP TABLE IF EXISTS `v_score_detail`;
/*!50001 DROP VIEW IF EXISTS `v_score_detail`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_score_detail` AS SELECT 
 1 AS `用户编号`,
 1 AS `用户名`,
 1 AS `分类`,
 1 AS `题名`,
 1 AS `难度`,
 1 AS `得分`,
 1 AS `解出时间`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_submission_record`
--

DROP TABLE IF EXISTS `v_submission_record`;
/*!50001 DROP VIEW IF EXISTS `v_submission_record`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_submission_record` AS SELECT 
 1 AS `提交编号`,
 1 AS `用户编号`,
 1 AS `用户名`,
 1 AS `分类`,
 1 AS `题名`,
 1 AS `题目分值`,
 1 AS `是否答对`,
 1 AS `本次得分`,
 1 AS `提交时间`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_total_rank`
--

DROP TABLE IF EXISTS `v_total_rank`;
/*!50001 DROP VIEW IF EXISTS `v_total_rank`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_total_rank` AS SELECT 
 1 AS `名次`,
 1 AS `用户编号`,
 1 AS `用户名`,
 1 AS `总分`,
 1 AS `解题数`,
 1 AS `最后解题时间`*/;
SET character_set_client = @saved_cs_client;

--
-- Dumping events for database 'ctf'
--

--
-- Dumping routines for database 'ctf'
--
/*!50003 DROP PROCEDURE IF EXISTS `sp_add_challenge` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_add_challenge`(IN p_admin INT, IN p_cid INT, IN p_title VARCHAR(64),
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

    SELECT Role INTO v_role FROM Users WHERE Uid = p_admin AND Status='active';
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
END proc ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_publish_challenge` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_publish_challenge`(IN p_chid INT, IN p_admin INT,
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

    SELECT Role INTO v_role FROM Users WHERE Uid = p_admin AND Status='active';
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
END proc ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_register_user` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_register_user`(IN p_username VARCHAR(32), IN p_password VARCHAR(64),
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
END proc ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_submit_flag` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_submit_flag`(IN p_uid INT, IN p_chid INT, IN p_flag VARCHAR(128),
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

    -- 同一账号的提交串行化，防止跨题并发时积分日志累计值不一致。
    START TRANSACTION;
    SELECT Status INTO v_user_status FROM Users WHERE Uid = p_uid FOR UPDATE;
    IF v_user_status IS NULL THEN
        SET p_message = '用户不存在';
        ROLLBACK;
        LEAVE proc;
    ELSEIF v_user_status <> 'active' THEN
        SET p_message = '账号已停用，无法提交';
        ROLLBACK;
        LEAVE proc;
    END IF;

    SELECT Status, Score, FlagSalt, FlagHash
    INTO v_ch_status, v_ch_score, v_salt, v_target
    FROM Challenges
    WHERE Chid = p_chid FOR SHARE;
    IF v_ch_status IS NULL THEN
        SET p_message = '题目不存在';
        ROLLBACK;
        LEAVE proc;
    ELSEIF v_ch_status <> 'online' THEN
        SET p_message = '题目未上架，暂不可提交';
        ROLLBACK;
        LEAVE proc;
    END IF;

    SET v_flaghash = SHA2(CONCAT(p_flag, v_salt), 256);
    SET v_correct = (v_flaghash = v_target);
    SELECT COUNT(*) INTO v_solved FROM Solves WHERE Uid = p_uid AND Chid = p_chid;
    IF v_solved > 0 THEN
        INSERT INTO Submissions (Uid, Chid, FlagHash, IsCorrect)
        VALUES (p_uid, p_chid, v_flaghash, v_correct);
        COMMIT;
        SET p_result = IF(v_correct=1, 'duplicate', 'wrong'), p_score = 0,
            p_message = IF(v_correct=1, '该题已解出，本次提交不重复计分', 'flag 不正确，该笔提交不计分');
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
END proc ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_user_records` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_user_records`(IN p_uid INT)
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
END proc ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Current Database: `ctf`
--

USE `ctf`;

--
-- Final view structure for view `v_category_rank`
--

/*!50001 DROP VIEW IF EXISTS `v_category_rank`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_category_rank` AS select `ca`.`Cid` AS `分类编号`,`ca`.`Cname` AS `分类`,rank() OVER (PARTITION BY `ca`.`Cid` ORDER BY sum(`so`.`ScoreAwarded`) desc,max(`so`.`SolvedAt`) )  AS `名次`,`u`.`Uid` AS `用户编号`,`u`.`Username` AS `用户名`,sum(`so`.`ScoreAwarded`) AS `分类得分`,count(0) AS `解题数` from (((`Solves` `so` join `Users` `u` on((`so`.`Uid` = `u`.`Uid`))) join `Challenges` `ch` on((`so`.`Chid` = `ch`.`Chid`))) join `Categories` `ca` on((`ch`.`Cid` = `ca`.`Cid`))) group by `ca`.`Cid`,`ca`.`Cname`,`u`.`Uid`,`u`.`Username` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_challenge_public`
--

/*!50001 DROP VIEW IF EXISTS `v_challenge_public`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_challenge_public` AS select `ch`.`Chid` AS `题目编号`,`ca`.`Cname` AS `分类`,`ch`.`Title` AS `题名`,`ch`.`Description` AS `题目描述`,`ch`.`Difficulty` AS `难度`,`ch`.`Score` AS `分值`,`ch`.`Attachment` AS `附件`,`ch`.`PublishedAt` AS `上架时间` from (`Challenges` `ch` join `Categories` `ca` on((`ch`.`Cid` = `ca`.`Cid`))) where (`ch`.`Status` = 'online') */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_score_detail`
--

/*!50001 DROP VIEW IF EXISTS `v_score_detail`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_score_detail` AS select `u`.`Uid` AS `用户编号`,`u`.`Username` AS `用户名`,`ca`.`Cname` AS `分类`,`ch`.`Title` AS `题名`,`ch`.`Difficulty` AS `难度`,`so`.`ScoreAwarded` AS `得分`,`so`.`SolvedAt` AS `解出时间` from (((`Solves` `so` join `Users` `u` on((`so`.`Uid` = `u`.`Uid`))) join `Challenges` `ch` on((`so`.`Chid` = `ch`.`Chid`))) join `Categories` `ca` on((`ch`.`Cid` = `ca`.`Cid`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_submission_record`
--

/*!50001 DROP VIEW IF EXISTS `v_submission_record`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_submission_record` AS select `s`.`Subid` AS `提交编号`,`u`.`Uid` AS `用户编号`,`u`.`Username` AS `用户名`,`ca`.`Cname` AS `分类`,`ch`.`Title` AS `题名`,`ch`.`Score` AS `题目分值`,`s`.`IsCorrect` AS `是否答对`,coalesce(`so`.`ScoreAwarded`,0) AS `本次得分`,`s`.`SubmittedAt` AS `提交时间` from ((((`Submissions` `s` join `Users` `u` on((`s`.`Uid` = `u`.`Uid`))) join `Challenges` `ch` on((`s`.`Chid` = `ch`.`Chid`))) join `Categories` `ca` on((`ch`.`Cid` = `ca`.`Cid`))) left join `Solves` `so` on((`so`.`Subid` = `s`.`Subid`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_total_rank`
--

/*!50001 DROP VIEW IF EXISTS `v_total_rank`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_total_rank` AS select rank() OVER (ORDER BY sum(`so`.`ScoreAwarded`) desc,max(`so`.`SolvedAt`) )  AS `名次`,`u`.`Uid` AS `用户编号`,`u`.`Username` AS `用户名`,sum(`so`.`ScoreAwarded`) AS `总分`,count(0) AS `解题数`,max(`so`.`SolvedAt`) AS `最后解题时间` from (`Solves` `so` join `Users` `u` on((`so`.`Uid` = `u`.`Uid`))) group by `u`.`Uid`,`u`.`Username` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-14 14:03:19
