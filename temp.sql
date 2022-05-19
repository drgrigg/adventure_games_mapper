DROP TABLE IF EXISTS `Paths`;
CREATE TABLE `Paths` (
  `ID` integer NOT NULL AUTO_INCREMENT,
  `DirectionID` integer,
  `FromID` integer,
  `ToID` integer,
  PRIMARY KEY (`ID`)
);

INSERT INTO `Paths` (`ID`,`DirectionID`,`FromID`,`ToID`) VALUES (1,1,2,1);
INSERT INTO `Paths` (`ID`,`DirectionID`,`FromID`,`ToID`) VALUES (2,5,1,2);