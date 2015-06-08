-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

CREATE TABLE  tournament_name(
  id_tournament_name serial,
  name text,
  PRIMARY KEY(id_tournament_name)
);

CREATE TABLE  players(
  id_players serial,
  name text,
  PRIMARY KEY(id_players)
);

CREATE TABLE  course_tournament(
  id_players integer references players(id_players) ,
  id_tournament integer references tournament_name(id_tournament_name),
  PRIMARY KEY(id_players,id_tournament)
);

CREATE TABLE  matches(
  id_match serial,
  id_tournament_name_matches integer references tournament_name(id_tournament_name),
  id_players_one integer references players (id_players),
  id_players_two integer references players (id_players),
  rounds integer,
  PRIMARY KEY(id_match)
);

CREATE TABLE  scores(
  id_score serial,
  id_matches integer references matches (id_match),
  winner integer references players (id_players),
  looser integer references players (id_players),
  id_tournament references tournament_name (id_tournament_name),
  rounds integer,
  PRIMARY KEY(id_score)
);
