DROP DATABASE IF EXISTS mugshots;
CREATE DATABASE mugshots;

USE nugshots;

CREATE TABLE `inmates` (
  `inmate_id` int(11) NOT NULL AUTO_INCREMENT,
  `case_id` varchar(20) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `sex` varchar(10) NOT NULL,
  `race` varchar(30) NOT NULL,
  `county` varchar(30) NOT NULL,
  `arrest_by` varchar(50) NOT NULL,
  `booked` date NOT NULL,
  `img_url` varchar(100) NOT NULL,
  `img_file` varchar(30) NOT NULL,
  PRIMARY KEY (`inmate_id`),
  KEY `case_id` (`case_id`)
) ENGINE=InnoDB AUTO_INCREMENT=767 DEFAULT CHARSET=utf8;

CREATE TABLE `charges` (
  `charge_id` int(11) NOT NULL AUTO_INCREMENT,
  `case_id` varchar(20) NOT NULL,
  `charge` varchar(50) NOT NULL,
  PRIMARY KEY (`charge_id`),
  KEY `case_id` (`case_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1696 DEFAULT CHARSET=utf8

CREATE TABLE `photos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `case_id` varchar(20) NOT NULL,
  `image` blob NOT NULL,
  PRIMARY KEY (`id`),
  KEY `case_id` (`case_id`)
) ENGINE=InnoDB AUTO_INCREMENT=767 DEFAULT CHARSET=utf8;