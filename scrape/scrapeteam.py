import re,urllib
from bs4 import BeautfiulSoup
from datetime import date
import requests
import pymysql
import qgame as gm

def create_connection(db_name):
	DATABASE = db_name
	try:
		connection=pymysql.connect(host="localhost", user="root",passwd="caoz",db=DATABASE)
		return connection
	except pymysql.Error as error:
		print ("connection error: "+error)
def destroy_connection(conn):
	conn.close()
def scan(qurl,db, table):
    response = requests.get(qurl)
    html = response.content
    soup = BeautifulSoup(html,'lxml')
    name = soup.h2.contents[0]
    year_games = soup.find_all('table')
    for year in year_games:
        games = year.find_all('tr')
        for row_num in range(len(games)):
            if(row_num%2 == 0):
                game = to_game(name,games[row_num],games[row_num+1])
                insert_game(game,db,table)
def insert_game(game,db, table):
    TABLE = table
    prefix = 'insert into ' +TABLE
    prefix = prefix+ '(wteam,wscore,lteam,lscore,period,gtime,isr,rtcatch,otcatch,sdcatch,gdate,game_id) '
    insert_stmt = gen_statement(game)
    if(insert_stmt != ''):
        insert_stmt = prefix + insert_stmt+"')"
        try:
            conn=create_connection(db)
            cur=conn.cursor()
            cur.execute(insert_stmt)
            conn.commit()
            destroy_connection(conn)
        except pymysql.Error as error:
            print ("insert error: " ,error)
def gen_statement(game):
    stmt = "values('"
    if(game.is_valid() and game.gdate>date(2014,6,1)):
        game_id = game.get_id()
        stmt = stmt + "{}','{}','{}','".format(game.wteam,game.wscore,game.lteam)
        stmt = stmt + "{}','{}','{}','".format(game.lscore,game.get_period(),game.gtime)
        stmt = stmt + "{}','{}','{}','".format(game.is_isr(),game.rtcatch,game.otcatch)
        stmt = stmt + str(game.sdcatch)+"',str_to_date('"+str(game.gdate)+"','%Y-%m-%d'),'"
        stmt = stmt + game_id
        return stmt
    else:
        return ''
def to_game(name,row_1,row_2):
    won = False
    wname = ''
    lname = ''
    game_data,team_1,score_1 = [item.contents for item in row_1.find_all('td')]
    team_2,score_2 = [item.contents for item in row_2.find_all('td')]
    if(row_1['class']==['won']):
        won = True
        wname = name
        lname = team_1[0] if wname != team_1[0] else team_2[0]
    else:
        lname = name
        wname = team_1[0] if lname!=team_1[0] else team_2[0]
    wscore = score_1[0] if wname ==team_1[0] else score_2[0]
    lscore = score_2[0] if lname ==team_2[0] else score_1[0]
    gdate,br,period_time =game_data
    gtime,period = period_time.split(' ')
    period = '(RT)' if period =='' else period
    return gm.Game(wname,wscore,lname,lscore,gdate,gtime,period)
