# CREATE DATABASE Number1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
#
# CREATE USER 'LoveBreaker'@'%' IDENTIFIED BY '123456';
#
# GRANT alter,select,insert,update,delete,create,drop,index,references,CREATE VIEW,TRIGGER,show view, ALTER ROUTINE, create routine, execute, create temporary tables ON Number1.* TO 'LoveBreaker'@'%';

CREATE TABLE IF NOT EXISTS leave_requests (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  leave_id VARCHAR(32) NOT NULL UNIQUE,
  requester VARCHAR(64) NOT NULL,
  leave_type VARCHAR(16) NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  duration_days DECIMAL(5,2) NOT NULL,
  reason VARCHAR(255),
  status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leave_balances (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  requester VARCHAR(64) NOT NULL UNIQUE,
  annual_days DECIMAL(5,2) NOT NULL DEFAULT 0,
  sick_days DECIMAL(5,2) NOT NULL DEFAULT 0,
  personal_days DECIMAL(5,2) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO leave_balances(requester, annual_days, sick_days, personal_days)
VALUES('LoveBreaker', 6.5, 10, 3)
ON DUPLICATE KEY UPDATE annual_days=6.5;

delete from leave_requests where id = 3;
