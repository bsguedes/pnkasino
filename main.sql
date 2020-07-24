/*
Navicat SQLite Data Transfer

Source Server         : flaskauth
Source Server Version : 30706
Source Host           : :0

Target Server Type    : SQLite
Target Server Version : 30706
File Encoding         : 65001

Date: 2020-07-23 22:25:37
*/

-- ----------------------------
-- Table structure for "main"."user"
-- ----------------------------

CREATE TABLE "user" (
"id"  SERIAL PRIMARY KEY NOT NULL,
"email"  VARCHAR(100),
"password"  VARCHAR(100),
"name"  VARCHAR(1000),
"pnkoins"  INTEGER NOT NULL
);

-- ----------------------------
-- Table structure for "main"."league"
-- ----------------------------

CREATE TABLE "league" (
"id"  SERIAL PRIMARY KEY NOT NULL,
"name"  VARCHAR(200) NOT NULL
);

-- ----------------------------
-- Table structure for "main"."category"
-- ----------------------------

CREATE TABLE "category" (
"id"  SERIAL PRIMARY KEY NOT NULL,
"question"  VARCHAR(200) NOT NULL,
"max_bet"  INTEGER NOT NULL,
"state"  VARCHAR(20) NOT NULL,
"winner_option_id"  INTEGER,
"league_id"  INTEGER,
FOREIGN KEY ("league_id") REFERENCES "league" ("id")
);

-- ----------------------------
-- Table structure for "main"."option"
-- ----------------------------

CREATE TABLE "option" (
"id"  SERIAL PRIMARY KEY NOT NULL,
"category_id"  INTEGER NOT NULL,
"name"  VARCHAR(100) NOT NULL,
"odds"  REAL NOT NULL,
CONSTRAINT "category_id_RK" FOREIGN KEY ("category_id") REFERENCES "category" ("id")
);

ALTER TABLE "category"
ADD CONSTRAINT "fkey0" 
FOREIGN KEY ("winner_option_id") 
REFERENCES "option" ("id");


-- ----------------------------
-- Table structure for "main"."bet"
-- ----------------------------

CREATE TABLE "bet" (
"id"  SERIAL PRIMARY KEY NOT NULL,
"user_id"  INTEGER NOT NULL,
"option_id"  INTEGER NOT NULL,
"value"  INTEGER NOT NULL,
"category_id"  INTEGER NOT NULL,
CONSTRAINT "fkey0" FOREIGN KEY ("user_id") REFERENCES "user" ("id"),
CONSTRAINT "fkey2" FOREIGN KEY ("option_id") REFERENCES "option" ("id"),
CONSTRAINT "fkey1" FOREIGN KEY ("category_id") REFERENCES "category" ("id")
);

