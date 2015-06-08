#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import math


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches(tournament):
    """Remove all the match records from the database."""
    DB = connect()
    cur = DB.cursor()

    cur.execute("SELECT id_tournament_name FROM tournament_name WHERE name = (%s)", (tournament,))
    rows = cur.fetchone()
    if(rows is None):
      DB.close()
    else:
      print rows
      id_tournament = rows[0]
      cur.execute("DELETE FROM scores where id_tournament = (%s)", (id_tournament,))
      DB.commit()
      cur.execute("DELETE FROM matches where id_tournament_name_matches = (%s)", (id_tournament,))
      DB.commit()
      DB.close()


def deleteTournaments():

    deleteCourse()

    DB = connect()
    cur = DB.cursor()

    cur.execute("DELETE FROM tournament_name")
    DB.commit()
    DB.close()


def deleteCourse():
    DB = connect()
    cur = DB.cursor()

    cur.execute("DELETE FROM course_tournament")
    DB.commit()
    DB.close()


def deletePlayers():
    """Remove all the player records from the database."""

    deleteTournaments()

    DB = connect()
    cur = DB.cursor()

    cur.execute("DELETE FROM players")
    DB.commit()
    DB.close()


def countPlayers():
    """Returns the number of players currently registered."""
    DB = connect()
    cur = DB.cursor()

    cur.execute("SELECT count (name) as Name FROM players")
    rows = cur.fetchone()
    total = rows[0]
    DB.close()
    return total


def registerTournament(tournament):

    DB = connect()
    cur = DB.cursor()

    cur.execute("INSERT INTO tournament_name (name) VALUES (%s)", (tournament,))
    DB.commit()
    DB.close()


def registerPlayer(name, tournament):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    DB = connect()
    cur = DB.cursor()

    cur.execute("INSERT INTO players (name) VALUES (%s)", (name, ))
    DB.commit()

    cur.execute("SELECT currval(pg_get_serial_sequence('players','id_players'))")
    rows = cur.fetchone()
    id_player = rows[0]

    cur.execute("SELECT id_tournament_name FROM tournament_name WHERE name = (%s)", (tournament,))
    rows = cur.fetchone()
    id_tournament = rows[0]

    cur.execute("INSERT INTO course_tournament (id_players,id_tournament) VALUES (%s,%s)", (id_player, id_tournament))
    DB.commit()

    DB.close()


def playerStandings(id_tournament):
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    DB = connect()
    cur = DB.cursor()

    cur.execute("SELECT id_tournament_name FROM tournament_name WHERE name = (%s)", (id_tournament,))
    rows = cur.fetchone()
    tournament = rows[0]

    cur.execute("select p.*,(select count(*) from scores s where p.id_players in (s.winner) and id_tournament = %s ) as GamesWon,(select count(*) from scores s where p.id_players in (s.winner, s.looser) and id_tournament = %s ) as GamesPlayed from players p order by GamesWon desc;", (tournament, tournament, ))
    rows = cur.fetchall()

    standings = []
    super_standings = []

    for x in rows:
      standings.append(x[0])
      standings.append(x[1])
      standings.append(x[2])
      standings.append(x[3])
      super_standings.append(tuple(standings))

    return rows


def reportMatch(id_tournament, winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    DB = connect()
    cur = DB.cursor()

    cur.execute("SELECT id_tournament_name FROM tournament_name WHERE name = (%s)", (id_tournament, ))
    rows = cur.fetchone()
    tournament = rows[0]

    cur.execute("SELECT id_match,rounds FROM matches where id_tournament_name_matches = %s and (id_players_one=%s or id_players_two=%s) and (id_players_one=%s or id_players_two=%s)", (tournament, winner, winner, loser, loser))
    rows = cur.fetchall()

    array_idmatches = []
    array_rounds = []
    for x in rows:
      array_idmatches.append(x[0])
      array_rounds.append(x[1])

    cur.execute("INSERT INTO scores (id_matches,winner,looser,id_tournament,rounds) VALUES (%s,%s,%s,%s,%s)", (array_idmatches[0], winner, loser, tournament, array_rounds[0]))
    DB.commit()
    DB.close()


def swissPairings(id_tournament):
    """Returns a list of pairs of players for the next rounds of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """

    """
      Getting the number of roundss and matches for each tournament
    """
    DB = connect()
    cur = DB.cursor()

    cur.execute("SELECT id_tournament_name FROM tournament_name WHERE name = (%s)", (id_tournament, ))
    rows = cur.fetchone()
    tournament = rows[0]

    players = getPlayerTournament(tournament)
    roundss = getRoundTournament(players)
    matches = getMatchesTournament(roundss, players)

    played_matches = getplayedMatchesTournament(tournament)

    if played_matches == 0:
      return getFirstRoundTournamenent(tournament)
    elif played_matches >= matches:
      return -1
    else:
      return getRoundsTournamanet(tournament)

    DB.commit()
    DB.close()


def getFirstRoundTournamenent(tournament):
  DB = connect()
  cur = DB.cursor()
  cur.execute("SELECT id_players FROM course_tournament WHERE id_tournament = (%s);", (tournament, ))
  rows = cur.fetchall()
  array_players = []
  for x in rows:
    array_players.append(x[0])

  for a, b in pairwise(array_players):
    cur.execute("SELECT id_players, name FROM players WHERE id_players = (%s) or id_players = (%s);", (a, b, ))
    rows = cur.fetchall()
    cur.execute("INSERT INTO matches (id_tournament_name_matches,id_players_one,id_players_two,rounds) VALUES (%s,%s,%s,%s)", (tournament, a, b, 1))

  DB.commit()
  DB.close()
  return rows


def getRoundsTournamanet(tournament):
  DB = connect()
  cur = DB.cursor()
  cur.execute("SELECT id_players FROM course_tournament WHERE id_tournament = (%s);", (tournament, ))
  rows = cur.fetchall()
  array_players = []
  for x in rows:
    array_players.append(x[0])

  cur.execute("SELECT rounds FROM matches WHERE id_tournament_name_matches = (%s);", (tournament, ))
  rows = cur.fetchall()
  array_roundss = []
  for x in rows:
    array_roundss.append(x[0])

  array_roundss = sorted(set(array_roundss), reverse=True)
  nextrounds= array_roundss[0] + 1
  cur.execute("SELECT winner,looser FROM scores WHERE id_tournament = (%s) and rounds = (%s);", (tournament, array_roundss[0], ))
  rows = cur.fetchall()
  array_winners = []
  array_looser = []
  for x in rows:
    array_winners.append(x[0])
    array_looser.append(x[1])

  pair_tuples = ()
  super_tuple = []

  for a, b in pairwise(array_winners):
    cur.execute("SELECT id_players, name FROM players WHERE id_players = (%s) or id_players = (%s);", (a, b, ))
    rows = cur.fetchall()

    for x in rows:
      pair_tuples = pair_tuples + (x[0], x[1])

    super_tuple.append(pair_tuples)
    cur.execute("INSERT INTO matches (id_tournament_name_matches,id_players_one,id_players_two,rounds) VALUES (%s,%s,%s,%s)", (tournament, a, b, nextrounds))

  pair_tuples = ()
  for a, b in pairwise(array_looser):
    cur.execute("SELECT id_players, name FROM players WHERE id_players = (%s) or id_players = (%s);", (a, b, ))
    rows1 = cur.fetchall()
    for x in rows1:
      pair_tuples = pair_tuples + (x[0], x[1])

    super_tuple.append(pair_tuples)

    cur.execute("INSERT INTO matches (id_tournament_name_matches,id_players_one,id_players_two,rounds) VALUES (%s,%s,%s,%s)", (tournament, a, b, nextrounds))

  DB.commit()
  DB.close()
  return super_tuple


def getPlayerTournament(tournament):
  DB = connect()
  cur = DB.cursor()
  cur.execute("SELECT count(id_players) FROM course_tournament WHERE id_tournament = (%s);", (tournament, ))
  rows = cur.fetchone()
  players = rows[0]
  DB.close()
  return players


def getRoundTournament(players):
  roundss = math.log(players, 2)
  return int(float(roundss))


def getMatchesTournament(roundss, players):
  return (roundss * (players/2))


def getplayedMatchesTournament(tournament):
  DB = connect()
  cur = DB.cursor()
  cur.execute("SELECT count(id_match) FROM matches WHERE id_tournament_name_matches = (%s);", (tournament, ))
  rows = cur.fetchone()
  played_matches = rows[0]
  DB.close()
  return played_matches


def pairwise(it):
    it = iter(it)
    while True:
        yield next(it), next(it)
