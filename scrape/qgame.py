from datetime import date
class Game:
    def __init__(self,wteam,wscore,lteam,lscore,gdate, gtime, period):
        self.wteam = wteam.replace("'","")
        self.lteam = lteam.replace("'","")
        self.gtime = Game.seconds(gtime)
        mm,dd,yyyy = gdate.split('/')
        self.gdate = date(int(yyyy),int(mm),int(dd))
        self.sd = (period == "(SD)")
        self.ot = (self.sd or period=="(OT)")
        win_stats = Game.get_qp(wscore)
        self.winning_qp = win_stats[1]
        self.wscore = win_stats[1]+win_stats[0]*30
        lose_stats = Game.get_qp(lscore)
        self.losing_qp = lose_stats[1]
        self.lscore = lose_stats[1]+lose_stats[0]*30
        self.rtcatch = 1 if '*' in win_stats[2] else -1
        self.rtcatch = 0 if '*' in lose_stats[2] else self.rtcatch
        if '^'in win_stats[2]:
            self.otcatch =1
        elif '^' in lose_stats[2]:
            self.otcatch=2
        else:
            self.otcatch=0
        if '!' in win_stats[2]:
            self.sdcatch =1
        elif '!' in lose_stats[2]:
            #2OT is sudden death, the team that catches in 2OT will never lose
            self.sdcatch=-1
        else:
            self.sdcatch=0

    # A game is "In snitch range" or "ISR" if at least one of two things are true:
    # 1) The game progressed to double or single overtime
    # 2) The absolute point margin (excluding snitch catches)
    #     was less than or equal to 30
    # IF a game is not in snitch range it is considered to be "out of range" or "OSR"
    
    def is_isr(self):
        if(self.sd or self.ot):
            return True
        elif(abs(self.winning_qp-self.losing_qp)<=30):
            return True
        else:
            return False

    # Snitch catches in quidditch matches are annotated as follows:
    #   * - Regular Time Snitch Catch
    #   ^ - Overtime Snitch catch
    #   ! - Sudden Death Snitch catch
    # So a quidditch score reports the score as 160*^-100
    # This method obtains the non-snitch catch points and the number of catches
    
    def get_qp(score_string):
        temp = score_string
        grabs = 0
        #while temp still has (*,^,!) non numerics, truncate temp, and count it
        # as a grab
        while(not temp.isnumeric()):
            temp = temp[:-1]
            grabs = grabs + 1
        score = int(temp) #Now that temp is numeric, it contains the raw total score
        qp = score-grabs*30 #quaffle points is the score minus 30 points/grab
        text = score_string[len(temp):]
        return (grabs,qp,text) # Return a tuple of (num_grabs,quaffle_points)

    #Turn the time (1:20:34 or 35:51) into an integer number of seconds
    def seconds(time_string):
        mens=  [int(x) for x in time_string.split(':')]
        return mens[0]*3600+mens[1]*60+mens[2] if len(mens)==3 else mens[0]*60+mens[1]
    def is_valid(self):
        if self.wscore<=self.lscore:
            print('Winning Score must be greater than losing score')
            return False
        elif self.gtime <=1080:
            print('Game time under 18 minutes not possible')
            return False
        elif self.rtcatch ==-1:
            print('No regular time catch reported')
            return False
        elif self.sdcatch ==-1:
            print('Improperly notated SD catch')
            return False
        else:
            return True
    # for unique identifier (Team 1 name + Team 2 name) is usually lengthy
    # Drop common useless prefixes 'University of Florida'-> Florida
    # Quidditch Club Boston -> Club Boston
    # Emerson College Quidditch -> Emerson
    def truncated_names(self):
        tr1 = self.wteam
        tr2 = self.lteam
        dropped_words = ['Quidditch','University','College','The','of',' ','-','the']
        for word in dropped_words:
            tr1 = tr1.replace(word,'')
            tr2 = tr2.replace(word,'')
        return tr1[0:35]+'-'+tr2[0:35]
    def get_period(self):
        period = ''
        if(not self.sd and not self.ot):
            period = 'RT'
        elif self.ot:
            period = 'OT'
        else:
            period = 'SD'
        return period
    def get_id(self):
        game_id = str(self.wscore)+'-'+str(self.lscore)
        game_id = game_id + self.get_period()
        game_id = game_id + str(self.rtcatch)+str(self.otcatch)+str(self.sdcatch)
        game_id = game_id + str(self.gtime)+str(self.gdate)+self.truncated_names()
        return game_id
    def __str__(self):
        return self.get_id()
