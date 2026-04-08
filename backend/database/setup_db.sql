-- MariaDB dump 10.19  Distrib 10.4.28-MariaDB, for osx10.10 (x86_64)
--
-- Host: localhost    Database: reva_db
-- ------------------------------------------------------
-- Server version	10.4.28-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `app_report`
--

DROP TABLE IF EXISTS `app_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `app_report` (
  `report_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) unsigned NOT NULL,
  `email` varchar(255) NOT NULL,
  `Name` varchar(255) DEFAULT NULL,
  `Age` int(3) DEFAULT NULL,
  `Gender` enum('Male','Female','Other') DEFAULT NULL,
  `affected_side` enum('left knee','right knee') NOT NULL,
  `affected_date` date NOT NULL,
  `height` decimal(5,2) NOT NULL,
  `weight` decimal(5,2) NOT NULL,
  `bmi` decimal(5,2) NOT NULL,
  `leg_length` decimal(5,2) NOT NULL,
  `thigh_length` decimal(5,2) NOT NULL,
  `circumfrence_thigh` decimal(5,2) NOT NULL,
  `posterior_st` decimal(5,2) NOT NULL,
  `posterior_gracilis` decimal(5,2) NOT NULL,
  `lateral_st` decimal(5,2) NOT NULL,
  `lateral_gracilis` decimal(5,2) NOT NULL,
  `submission_time` timestamp NOT NULL DEFAULT current_timestamp(),
  `graft_diameter_1` decimal(5,2) DEFAULT NULL,
  `graft_diameter_2` decimal(5,2) DEFAULT NULL,
  `hamstring_autograft` decimal(5,2) DEFAULT NULL,
  `quadriceps_tendon_diameter` decimal(5,2) DEFAULT NULL,
  `minimum_st_length` decimal(5,2) DEFAULT NULL,
  `predicted_st_value` decimal(5,2) DEFAULT NULL,
  `gracilis_length` decimal(5,2) DEFAULT NULL,
  `pdf_report` longblob DEFAULT NULL,
  PRIMARY KEY (`report_id`),
  KEY `user_id` (`user_id`),
  KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daily_metrics`
--

DROP TABLE IF EXISTS `daily_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daily_metrics` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `date` datetime DEFAULT NULL,
  `water_intake` varchar(50) DEFAULT NULL,
  `steps` int(11) DEFAULT NULL,
  `sleep_hours` varchar(20) DEFAULT NULL,
  `symptoms` text DEFAULT NULL,
  `heart_rate` int(11) DEFAULT NULL,
  `calories_burned` int(11) DEFAULT NULL,
  `active_minutes` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `daily_metrics_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `followup_comparisons`
--

DROP TABLE IF EXISTS `followup_comparisons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `followup_comparisons` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `patient_id` int(11) NOT NULL,
  `previous_report_id` int(11) DEFAULT NULL,
  `current_report_id` int(11) NOT NULL,
  `improvement_percentage` float DEFAULT NULL,
  `decline_percentage` float DEFAULT 0,
  `health_trend` varchar(50) DEFAULT NULL,
  `comparison_summary` text DEFAULT NULL,
  `comparisons_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`comparisons_json`)),
  `activity_improvement` float DEFAULT 0,
  `wellness_improvement` float DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `patient_id` (`patient_id`),
  KEY `previous_report_id` (`previous_report_id`),
  KEY `current_report_id` (`current_report_id`),
  CONSTRAINT `followup_comparisons_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`),
  CONSTRAINT `followup_comparisons_ibfk_2` FOREIGN KEY (`previous_report_id`) REFERENCES `health_reports` (`id`),
  CONSTRAINT `followup_comparisons_ibfk_3` FOREIGN KEY (`current_report_id`) REFERENCES `health_reports` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `health_reports`
--

DROP TABLE IF EXISTS `health_reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `health_reports` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `patient_id` int(11) NOT NULL,
  `report_type` varchar(100) NOT NULL,
  `report_file` varchar(255) DEFAULT NULL,
  `medical_metrics_json` text DEFAULT NULL,
  `recovery_score` int(11) DEFAULT NULL,
  `risk_level` varchar(50) DEFAULT NULL,
  `primary_risk` varchar(255) DEFAULT NULL,
  `diagnosis` text DEFAULT NULL,
  `recommendations_json` text DEFAULT NULL,
  `medications_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`medications_json`)),
  `created_at` datetime DEFAULT NULL,
  `patient_identity_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`patient_identity_json`)),
  `activity_score` int(11) DEFAULT NULL,
  `wellness_score` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `patient_id` (`patient_id`),
  CONSTRAINT `health_reports_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=111 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `medical_metrics_data`
--

DROP TABLE IF EXISTS `medical_metrics_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `medical_metrics_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `report_id` int(11) NOT NULL,
  `metric_name` varchar(100) NOT NULL,
  `value` varchar(50) DEFAULT NULL,
  `unit` varchar(50) DEFAULT NULL,
  `confidence` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `report_id` (`report_id`),
  CONSTRAINT `medical_metrics_data_ibfk_1` FOREIGN KEY (`report_id`) REFERENCES `health_reports` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=747 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `password_reset`
--

DROP TABLE IF EXISTS `password_reset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `password_reset` (
  `email` varchar(255) NOT NULL,
  `otp` varchar(6) DEFAULT NULL,
  `expiry` datetime DEFAULT NULL,
  PRIMARY KEY (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `patients`
--

DROP TABLE IF EXISTS `patients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `patients` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `patient_name` varchar(100) DEFAULT NULL,
  `patient_id` varchar(100) DEFAULT NULL,
  `age` varchar(20) DEFAULT NULL,
  `gender` varchar(20) DEFAULT NULL,
  `hospital` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `patients_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shared_report`
--

DROP TABLE IF EXISTS `shared_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shared_report` (
  `sno` int(11) NOT NULL AUTO_INCREMENT,
  `from_mail` varchar(50) NOT NULL,
  `to_mail` varchar(50) NOT NULL,
  `Date` date NOT NULL,
  `reort_no` int(11) NOT NULL,
  PRIMARY KEY (`sno`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `signin`
--

DROP TABLE IF EXISTS `signin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `signin` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT 'Unique ID for each user',
  `first_name` varchar(100) NOT NULL COMMENT 'User’s first name',
  `last_name` varchar(100) NOT NULL COMMENT 'User’s last name',
  `email` varchar(150) NOT NULL COMMENT 'User’s email (login identifier)',
  `phone` varchar(20) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL COMMENT 'Hashed password',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp() COMMENT 'Account creation time',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT 'Last updated time',
  `user` varchar(10) NOT NULL DEFAULT 'Patient' COMMENT 'Doctor, Patient, Admin',
  `auth_provider` enum('local','google') NOT NULL DEFAULT 'local',
  `google_sub` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=98454279091 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_details`
--

DROP TABLE IF EXISTS `user_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_details` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `dob` date NOT NULL,
  `gender` enum('Male','Female','Other') NOT NULL,
  `age` int(11) NOT NULL,
  `language` enum('English','Tamil') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `dob` varchar(20) DEFAULT NULL,
  `height` varchar(20) DEFAULT NULL,
  `weight` varchar(20) DEFAULT NULL,
  `blood_type` varchar(10) DEFAULT NULL,
  `allergies` varchar(255) DEFAULT NULL,
  `patient_id` varchar(20) DEFAULT NULL,
  `patient_internal_id` varchar(20) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `otp` varchar(6) DEFAULT NULL,
  `otp_expiry` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-08  9:13:59
