/*
Navicat MySQL Data Transfer

Source Server         : localhost_3306
Source Server Version : 50558
Source Host           : localhost:3306
Source Database       : skill_finder

Target Server Type    : MYSQL
Target Server Version : 50558
File Encoding         : 65001

Date: 2026-08-10 17:17:17
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `collection_runs`
-- ----------------------------
DROP TABLE IF EXISTS `collection_runs`;
CREATE TABLE `collection_runs` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `status` varchar(32) NOT NULL,
  `trigger_type` varchar(32) NOT NULL,
  `started_at` datetime NOT NULL,
  `finished_at` datetime DEFAULT NULL,
  `query_count` int(10) unsigned NOT NULL DEFAULT '0',
  `discovered_count` int(10) unsigned NOT NULL DEFAULT '0',
  `updated_count` int(10) unsigned NOT NULL DEFAULT '0',
  `failed_count` int(10) unsigned NOT NULL DEFAULT '0',
  `rate_limit_remaining` int(11) DEFAULT NULL,
  `rate_limit_reset_at` datetime DEFAULT NULL,
  `error_summary` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_collection_runs_started` (`started_at`),
  KEY `idx_collection_runs_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Records of collection_runs
-- ----------------------------
INSERT INTO `collection_runs` VALUES ('1', 'FAILED', 'manual', '2026-08-10 09:03:00', '2026-08-10 09:07:09', '7', '4377', '3570', '0', '5000', '2026-08-10 10:06:39', 'RemoteProtocolError: Server disconnected without sending a response.', '2026-08-10 09:03:00');
