CREATE DATABASE IF NOT EXISTS `aqi_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE `aqi_db`;

CREATE USER IF NOT EXISTS 'aqi_user'@'localhost'
  IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON `aqi_db`.* TO 'aqi_user'@'localhost';
FLUSH PRIVILEGES;

DROP TABLE IF EXISTS `air_quality_records`;

CREATE TABLE `air_quality_records` (
  `SiteId`            INT NOT NULL,
  `SiteName`          VARCHAR(255) NOT NULL,
  `County`            VARCHAR(255),
  `AQI`               INT,
  `Status`            VARCHAR(255),
  `DataCreationDate`  DATETIME NOT NULL,
  `Latitude`          DECIMAL(10,7),
  `Longitude`         DECIMAL(11,7),
  `created_at`        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`SiteId`, `DataCreationDate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS `historical_aqi_analysis`;

CREATE TABLE `historical_aqi_analysis` (
  `SiteId`            INT NOT NULL,
  `SiteName`          VARCHAR(255) NOT NULL,
  `County`            VARCHAR(255),
  `AQI`               INT,
  `Status`            VARCHAR(255),
  `DataCreationDate`  DATETIME NOT NULL,
  PRIMARY KEY (`SiteId`, `DataCreationDate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
