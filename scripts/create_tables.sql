-- 2026-11-02: Java 마이그레이션 참고용 — 실제 운영 MariaDB에서 추출한 CREATE TABLE 스크립트.
-- SQLAlchemy 모델(app/models/*.py)이 아니라 실제 DB(SHOW CREATE TABLE)에서 뽑은 것이라,
-- 수동 ALTER TABLE로 반영된 변경(예: barcode_prefix의 대소문자 무시 collation)까지 그대로 반영됨.
-- 생성 순서는 FK 의존관계 순서(그룹 -> 공통코드 -> 품목 -> 재고조사기록/센서바코드).

CREATE TABLE `common_code_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_code` varchar(30) NOT NULL,
  `group_name` varchar(50) NOT NULL,
  `created_by` varchar(50) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_by` varchar(50) NOT NULL,
  `updated_at` datetime NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_code` (`group_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `common_codes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `code` varchar(30) NOT NULL,
  `name` varchar(50) NOT NULL,
  `sort_order` int(11) NOT NULL,
  `created_by` varchar(50) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_by` varchar(50) NOT NULL,
  `updated_at` datetime NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_common_codes_group_code` (`group_id`,`code`),
  KEY `ix_common_codes_group_active_sort` (`group_id`,`is_active`,`sort_order`),
  CONSTRAINT `common_codes_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `common_code_groups` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_name` varchar(200) NOT NULL,
  `category_id` int(11) NOT NULL,
  `unit_id` int(11) NOT NULL,
  `location_id` int(11) DEFAULT NULL,
  `size_abbr_id` int(11) DEFAULT NULL,
  `size_width` decimal(10,2) DEFAULT NULL,
  `size_length` decimal(10,2) DEFAULT NULL,
  `size_height` decimal(10,2) DEFAULT NULL,
  `created_by` varchar(50) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_by` varchar(50) NOT NULL,
  `updated_at` datetime NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `item_no` varchar(100) DEFAULT NULL,
  `barcode` varchar(100) DEFAULT NULL,
  `barcode_prefix` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `barcode_prefix` (`barcode_prefix`),
  KEY `unit_id` (`unit_id`),
  KEY `size_abbr_id` (`size_abbr_id`),
  KEY `ix_items_item_name` (`item_name`),
  KEY `ix_items_location` (`location_id`),
  KEY `ix_items_category` (`category_id`),
  KEY `ix_items_item_no` (`item_no`),
  KEY `ix_items_barcode` (`barcode`),
  CONSTRAINT `items_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `common_codes` (`id`),
  CONSTRAINT `items_ibfk_2` FOREIGN KEY (`unit_id`) REFERENCES `common_codes` (`id`),
  CONSTRAINT `items_ibfk_3` FOREIGN KEY (`location_id`) REFERENCES `common_codes` (`id`),
  CONSTRAINT `items_ibfk_4` FOREIGN KEY (`size_abbr_id`) REFERENCES `common_codes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `stocktake_records` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `quantity` decimal(12,2) NOT NULL,
  `survey_date` date NOT NULL,
  `note` varchar(500) DEFAULT NULL,
  `created_by` varchar(50) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_by` varchar(50) NOT NULL,
  `updated_at` datetime NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_stocktake_date` (`survey_date`),
  KEY `ix_stocktake_item` (`item_id`),
  CONSTRAINT `stocktake_records_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `sensor_barcodes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `barcode` varchar(100) NOT NULL,
  `created_by` varchar(50) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_by` varchar(50) NOT NULL,
  `updated_at` datetime NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `barcode` (`barcode`),
  KEY `ix_sensor_barcodes_item` (`item_id`),
  CONSTRAINT `sensor_barcodes_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
