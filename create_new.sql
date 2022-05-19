DROP TABLE IF EXISTS `Directions`;
CREATE TABLE `Directions` (`ID` integer PRIMARY KEY AUTOINCREMENT, `Name` char(128) NOT NULL, `X` float(128), `Y` float(128), `Z` float(128));
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (1,'North',0,1,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (2,'NorthEast',1,1,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (3,'East',1,0,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (4,'SouthEast',1,-1,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (5,'South',0,-1,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (6,'SouthWest',-1,-1,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (7,'West',-1,0,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (8,'NorthWest',-1,1,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (9,'Up',0,0,1);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (10,'Down',0,0,-1);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (11,'Enter',0.5,0.5,0.5);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (12,'Leave',-0.5,-0.5,-0.5);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (13,'Port',-1,0,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (14,'Starboard',1,0,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (15,'Afore',0,1,0);
INSERT INTO `Directions` (`ID`,`Name`,`X`,`Y`,`Z`) VALUES (16,'Astern',0,-1,0);
DROP TABLE IF EXISTS `Paths`;
CREATE TABLE `Paths` (`DirectionID` integer, `FromID` integer, `ToID` integer);
INSERT INTO `Paths` (`DirectionID`,`FromID`,`ToID`) VALUES (1,2,1);
INSERT INTO `Paths` (`DirectionID`,`FromID`,`ToID`) VALUES (5,1,2);
DROP TABLE IF EXISTS `Rooms`;
CREATE TABLE `Rooms` (`ID` integer PRIMARY KEY AUTOINCREMENT, `Name` char(255) NOT NULL, `Description` varchar(255), `X` float(128), `Y` float(128), `Z` float(128));
INSERT INTO `Rooms` (`ID`,`Name`,`Description`) VALUES (1,'First Room','A place to start', 0.0, 0.0, 0.0);
INSERT INTO `Rooms` (`ID`,`Name`,`Description`) VALUES (2,'Second room','Somewhere to go', 0.0, 0.0, 0.0);