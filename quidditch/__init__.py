import numpy
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from scipy.stats import norm
import rgstats as rgs

def year_data(dat,year,distance='A'):
    if(distance=='i'or distance=='I'):
        return dat[dat.gdate>datetime.date(year,6,1)][dat.gdate<datetime.date(year+1,6,1)][dat.distance=='ISR']
    elif(distance=='O'or distance=='o'):
        return dat[dat.gdate>datetime.date(year,6,1)][dat.gdate<datetime.date(year+1,6,1)][dat.distance=='OSR']
    else:
        return dat[dat.gdate>datetime.date(year,6,1)][dat.gdate<datetime.date(year+1,6,1)]

def teams_data(dat,year,kappa=0):
    subset = year_data(dat,year)
    teams = numpy.union1d(subset.wteam.unique(),subset.lteam.unique())
    mttgs = [subset[subset.wteam==team][subset.rtcatch==1][subset.period=='RT'].gtime.median()-1080 for team in teams]
    swim = []
    for team in teams: 
        wisr = len(subset[(subset.wteam==team) & (subset.distance=='ISR')])
        lisr = len(subset[(subset.lteam==team) & (subset.distance=='ISR')])
        if(wisr+lisr==0):
            swim.append(numpy.NaN)
        else:
            swim.append((wisr+kappa)/(wisr+lisr+2*kappa))
    return (pd.Series(mttgs, index=teams),pd.Series(swim,index=teams))

def lsrNormalEquations(x,y):
    if(x.ndim==1):
        n =1
        m = len(x)
        x = x.reshape((m,1))
    else:
        m = len(x)
        n = len(x.T)
    xprime = numpy.hstack((numpy.ones((m,1)),x))
    return (numpy.linalg.pinv(xprime.T.dot(xprime)).dot(xprime.T).dot(y))

def find_record(dat, t1,t2):
	wins = len(dat[(dat.wteam==t1)&(dat.lteam==t2)])
	losses = len(dat[(dat.wteam==t2)&(dat.lteam==t1)])
	return (wins,losses)       

def plotlsr(params,x,y):
#  t = numpy.arange(0,max(y),0.1)
  #  val = params.tolist()[0]+params.tolist()[1]*t
    plt.xlim(0,700)
    plt.ylim(0,1)
    plt.plot(x,y,'.')
    plt.plot(x,params.tolist()[0]+params.tolist()[1]*x,'-') 
    plt.show()
    return params.tolist()[0]+params.tolist()[1]*x-y

def getWL(dat,year):
    subset = year_data(dat,year)
    teams = numpy.union1d(subset.wteam.unique(),subset.lteam.unique())
    stuff = ((len(subset[subset.wteam==team]), len(subset[subset.lteam==team])) for team in teams)
        
    return pd.Series(stuff,index=teams)

def getEverything(dat,team,year):
    gam = year_data(dat,year)
    return gam[(dat.wteam==team) | (dat.lteam==team)]

def team_breakdown(team_dat,name):
    temp = team_dat
    temp.wscore = temp.wscore - (temp.rtcatch%2 + temp.otcatch%2 + temp.sdcatch%2)*30
    temp.lscore = temp.lscore - (round((temp.rtcatch-1)/2)+ round((temp.otcatch-1)/2)+round((temp.sdcatch-1)/2))*30
    winning = temp[temp.wteam==name]
    losing = temp[temp.lteam==name]
    off = numpy.union1d(winning.wscore/winning.gtime,losing.lscore/losing.gtime)*60
    dfn = numpy.union1d(winning.lscore/winning.gtime,losing.wscore/losing.gtime)*60
    
    return (numpy.mean(off),numpy.mean(dfn), numpy.std(off),numpy.std(dfn))
def get_weighted_swim(dat,team,year, kappa=1):
    tdat = getEverything(dat,team,year)
    isr =  tdat[tdat.distance=='ISR']
    wisr = len(isr[isr.wteam==team])
    lisr = len(isr)-wisr
    return ((wisr + kappa)/(lisr+kappa+wisr+kappa))

def get_all_breakdowns(dat,year,include = True): 
    subset = year_data(dat,year)
    teams = numpy.union1d(subset.wteam.unique(),subset.lteam.unique())
    offenses = []
    defenses = []
    stoffs = []
    stdefs = []
    wl = []
    for team in teams: 
        off, dfn,stoff,stdfn = team_breakdown(getEverything(dat,team,year),team)
        offenses.append(off)
        defenses.append(dfn)
        stoffs.append(stoff)
        stdefs.append(stdfn)
        wl.append((len(subset[subset.wteam==team])/(len(subset[subset.lteam==team])+len(subset[subset.wteam==team]))))
    mttg, swim = teams_data(dat,year)
    breakdown = pd.concat([pd.Series(offenses,index=teams),pd.Series(defenses,index=teams),
                             pd.Series(mttg,index=teams),pd.Series( swim,index=teams),
                           pd.Series(stoffs,index=teams),pd.Series(stdefs,index=teams),
                          pd.Series(wl,index=teams)], axis=1
                           )
    breakdown.columns = ['Offense','Defense','MTTG','SWIM','STO','STD','WL']
    if not include:
    	breakdown =breakdown[pd.notnull(breakdown['MTTG'])&pd.notnull(breakdown['SWIM'])]
    return breakdown

def sop_as_dbnm(b1,s1,s2, num):
    b2 = 1-b1
    multiplier = (1-b1*s1-b2*s2)
    p1 = b1*s1*(multiplier**(num)-1)/(multiplier-1)
    p2 = b2*s2*(multiplier**(num)-1)/(multiplier-1)
    return p1 + (1-p1-p2)/2

def ranges (t1qpm,t2qpm,st):
	(zlosr,zm25,zm15,zm5,z5,z15,z25,zwosr) = ((-35,-25,-15,-5,5,15,25,35)-(t1qpm-t2qpm))/st
	return (norm.cdf(zlosr),
												norm.cdf(zm25)-norm.cdf(zlosr),
												norm.cdf(zm15)-norm.cdf(zm25),
												norm.cdf(zm5)-norm.cdf(zm15),
												norm.cdf(z5)-norm.cdf(zm5),
												norm.cdf(z15)-norm.cdf(z5),
												norm.cdf(z25)-norm.cdf(z15),
												norm.cdf(zwosr)-norm.cdf(z25),
												1-norm.cdf(zwosr))


def prediction(dat, team1,team2,params,snit = 12):
    t1stat = dat.transpose()[team1]
    t2stat = dat.transpose()[team2]
    gtime = (t1stat['MTTG'] + t2stat['MTTG'])/2
    t1qpm = (t1stat['Offense'] + t2stat['Defense'])/2*gtime
    t2qpm = (t2stat['Offense'] + t1stat['Defense'])/2*gtime
    swim1 = (t1stat['SWIM'])
    swim2 = t2stat['SWIM']
    mttg1 = (t1stat['MTTG'])
    mttg2 = (t2stat['MTTG'])
    sto1 =  numpy.sqrt(t1stat['STO']**2 + t2stat['STD']**2)*gtime
    sto2 =  numpy.sqrt(t2stat['STO']**2 + t1stat['STD']**2)*gtime
    st = numpy.sqrt(sto1**2 + sto2**2)
    plosr,pm30,pm20,pm10,p0,p10,p20,p30,pwosr = ranges(t1qpm,t2qpm,st/1.5)
    sopb1 = swim1-params.dot(numpy.array([1,mttg1]))
    sopb2 = swim2-params.dot(numpy.array(([1,mttg2])))
    b1= 0.5 + (sopb1-sopb2)/2
    s1= snit/mttg1
    s2 = snit/mttg2
    num = round(gtime/snit)
    p = sop_as_dbnm(b1,s1,s2,num)
    winning = pwosr
    winning = winning + p30*.60 + p30*.40*p + p20*.36+p20*.72*p + p10*.216 + p10*.71*p + p0*.13+p0*.84*p + pm10*.71*p + pm10*.07 + pm20*.72*p + pm30*.40*p
    return winning

def get_scoring_params(dat,name,year):
    team_games = getEverything(dat,name,year)
    wgames = team_games[team_games.wteam==name]
    lgames = team_games[team_games.lteam==name]
    wscores = wgames.wscore.values.reshape(len(wgames),1)
    lscores = lgames.lscore.values.reshape(len(lgames),1)
    wtimes = wgames.gtime.values.reshape(len(wgames),1)
    ltimes = lgames.gtime.values.reshape(len(lgames),1)
    w = numpy.hstack((wscores,wtimes))
    l = numpy.hstack((lscores,ltimes))
    rg = numpy.vstack((w,l))
    #score - time
    rg[:,1]= rg[:,1]-1080
    # time to s.o.p 
    params =  rgs.lsrNormalEquations(rg[:,1],rg[:,0])
    #Regress score vs. time 
    return (params[0]/1080*60,params[1]*60)

def team_scoring_params(dat,year):
    subset = year_data(dat,year)
    teams = numpy.union1d(subset.wteam.unique(),subset.lteam.unique())
    floor = []
    sop = []
    for team in teams: 
        pr = get_scoring_params(dat,team,year)
        floor.append(pr[0])
        sop.append(pr[1])
    return (pd.Series(floor, index=teams),pd.Series(sop,index=teams))
def percent_isr(dat): 
    return len(dat[dat.distance=='ISR'])/len(dat)
def percent_suicides(dat): 
    return len(dat[(dat.distance=='OSR')&(dat.rtcatch==2)])/len(dat[dat.distance=='OSR'])
def get_standings_qpd(dat):
    qpds = []
    catch_modifier=[]
    for game_d in dat.iterrows():
        game = game_d[1]
        if game.period == 'RT':
            qpds.append(game.wscore-game.lscore + (game.rtcatch*2-3)*30)
            catch_modifier.append(game.rtcatch==1)
        elif game.period=='OT': 
            if(game.otcatch==0): 
                qpds.append(game.wscore-game.lscore)
            else:
                qpds.append(game.wscore-game.lscore + (game.otcatch*2-3)*30)
            catch_modifier.append(game.otcatch==1)
        elif game.period== 'SD':
            if(game.sdcatch==0):
                qpds.append(10)
            else:
                qpds.append(0)
            catch_modifier.append(game.sdcatch==1)
    return (qpds,catch_modifier)

def p_adj(qpds):
    adjusted = [min(point,80)+numpy.sqrt(max(point-80,0)) for point in qpds]
    return adjusted

def standings_swim(games, win):
    swim_modifier = 0
    if(win==True):
        swim_modifier=1
    else:
        swim_modifier=-1
    qpds,catch_modifier = get_standings_qpd(games)
    padj = numpy.array(p_adj(qpds))
    in_range = numpy.array([diff<30 for diff in padj])
    catch_modifier = numpy.array(catch_modifier)
    swim = swim_modifier*(padj + 30*catch_modifier*(in_range + (1-in_range)*numpy.exp(-0.033*(padj-20))))
    return swim

def get_team_swim(dat,name): 
    wgames = dat[dat.wteam==name]
    lgames = dat[dat.lteam==name]
    wswim = standings_swim(wgames,True).tolist()
    lswim = standings_swim(lgames,False).tolist()
    if(len(wgames)==0): 
        return (lswim,numpy.mean(lswim))
    elif len(lgames)==0:
        return (wswim,numpy.mean(wswim))
    else:
        return (wswim+lswim,numpy.mean(wswim+lswim))

def get_adj_swims(dat,year):
    subset = year_data(dat,year)
    teams = numpy.union1d(subset.wteam.unique(),subset.lteam.unique())
    raw_swims = [get_team_swim(subset,team)[1] for team in teams]
    offset = min(raw_swims)
    adj_swims = [r-offset for r in raw_swims]
    return pd.Series(adj_swims,index=teams)

def get_teams_played(dat,name):
    wgames = dat[dat.wteam==name]
    lgames = dat[dat.lteam==name]
    beaten_teams = wgames.lteam.tolist()
    better_teams = lgames.wteam.tolist()
    return beaten_teams+better_teams

def team_winp(dat,name,exclude=''):
    wins = len(dat[(dat.wteam==name)&(dat.lteam!=exclude)])
    losses = len(dat[(dat.lteam==name)&(dat.wteam!=exclude)])
    return (numpy.NaN if wins+losses==0 else wins/(wins+losses))

def team_sos_1(dat,name):
    opps = get_teams_played(dat,name)
    opp_percent = numpy.mean([team_winp(dat,opp,exclude=name) for opp in opps])
    oppsopps = [get_teams_played(dat,opp) for opp in opps]
    oppsopps = [t for opp in oppsopps for t in opp]
    oppopp_percent = numpy.mean([team_winp(dat,opp,name) for opp in oppsopps])
    return (2*opp_percent+oppopp_percent)/3
def team_sos_2(dat,name):
    opps = get_teams_played(dat,name)
    opp_percent = numpy.mean([team_winp(dat,opp,exclude=name) for opp in opps])
    oppsopps = [get_teams_played(dat,opp) for opp in opps]
    oppopp_percent = numpy.mean([team_winp(dat,t,exclude=opps[index]) for index in range(len(oppsopps)) for t in oppsopps[index] ])
    return (2*opp_percent+oppopp_percent)/3
def team_sos_3(dat,name):
    opps = get_teams_played(dat,name)
    opp_percent = numpy.mean([team_winp(dat,opp,exclude=name) for opp in opps])
    oppsopps = [get_teams_played(dat,opp) for opp in opps]
    oppopp_percent = numpy.mean([team_winp(dat,t,exclude=opps[index]) for index in range(len(oppsopps)) for t in oppsopps[index] if t!=name])
    return (2*opp_percent+oppopp_percent)/3
def team_sos_4(dat,name):
    opps = get_teams_played(dat,name)
    opp_percent = numpy.mean([team_winp(dat,opp,exclude=name) for opp in opps])
    oppsopps = [get_teams_played(dat,opp) for opp in opps]
    oppopp_percent = numpy.mean([team_winp(dat,t,exclude='') for opp in oppsopps for t in opp if t!=name])
    return (2*opp_percent+oppopp_percent)/3
def team_sos_5(dat,name):
    opps = get_teams_played(dat,name)
    opp_percent = numpy.mean([team_winp(dat,opp,exclude=name) for opp in opps])
    oppsopps = [get_teams_played(dat,opp) for opp in opps]
    oppopp_percent = numpy.mean([team_winp(dat,t,exclude='') for opp in oppsopps for t in opp ])
    return (2*opp_percent+oppopp_percent)/3
def team_sos_6(dat,name):
    opps = get_teams_played(dat,name)
    opp_percent = numpy.mean([team_winp(dat,opp,exclude=name) for opp in opps])
    oppsopps = [get_teams_played(dat,opp) for opp in opps]
    oppopp_percent = numpy.mean([team_winp(dat,t,exclude=name) for opp in oppsopps for t in opp ])
    return (2*opp_percent+oppopp_percent)/3
def team_sos_7(dat,name):
    opps = get_teams_played(dat,name)
    opp_percent = numpy.mean([team_winp(dat,opp,exclude=name) for opp in opps])
    oppsopps = [get_teams_played(dat,opp) for opp in opps]
    games = []
    for i in range(len(oppsopps)): 
        games.append(numpy.mean([team_winp(dat,t,exclude=opps[i]) for t in oppsopps[i]]))
    oppopp_percent = numpy.mean(games)
    return (2*opp_percent+oppopp_percent)/3
def team_sos_8(dat,name):
    opps = get_teams_played(dat,name)
    opp_percent = numpy.mean([team_winp(dat,opp,exclude=name) for opp in opps])
    oppsopps = [get_teams_played(dat,opp) for opp in opps]
    games = []
    for i in range(len(oppsopps)): 
        games.append(numpy.mean([team_winp(dat,t,exclude='') for t in oppsopps[i]]))
    oppopp_percent = numpy.mean(games)
    return (2*opp_percent+oppopp_percent)/3
def team_sos_9(dat,name):
    opps = get_teams_played(dat,name)
    opp_percent = numpy.mean([team_winp(dat,opp,exclude='') for opp in opps])
    oppsopps = [get_teams_played(dat,opp) for opp in opps]
    games = []
    for i in range(len(oppsopps)): 
        games.append(numpy.mean([team_winp(dat,t,exclude='') for t in oppsopps[i]]))
    oppopp_percent = numpy.mean(games)
    return (2*opp_percent+oppopp_percent)/3

def win_perc(dat,name):
    wins = len(dat[dat.wteam==name])
    losses = len(dat[dat.lteam==name])
    return (wins/(wins+losses))
def adj_win_perc(dat,name):
    return (1+win_perc(dat,name))/2

def performances(dat,year):
    subset = year_data(dat,year)
    teams = numpy.union1d(subset.wteam.unique(),subset.lteam.unique())
    adjs = []
    sosses=[]
    for team in teams: 
        adjs.append(adj_win_perc(subset,team))
        sosses.append(team_sos_5(subset,team))
    breakdown = pd.concat([get_adj_swims(subset,year),pd.Series(adjs,index=teams),pd.Series(sosses,index=teams),
                             ], axis=1
                           )
    breakdown.columns = ['Adj_Swim','SOSs','Win']
    return breakdown
def three_mets(dats):
    subset = year_data(dat,year)
    teams = numpy.union1d(subset.wteam.unique(),subset.lteam.unique())
    mttgs = [subset[subset.wteam==team][subset.rtcatch==1][subset.period=='RT'].gtime.median()-1080 for team in teams]
    swim = []
    iodiff=[]
    for team in teams: 

        wisr = len(subset[(subset.wteam==team) & (subset.distance=='ISR')])
        lisr = len(subset[(subset.lteam==team) & (subset.distance=='ISR')])
        if(wisr+lisr==0):
            swim.append(numpy.NaN)
        else:
            swim.append((wisr+kappa)/(wisr+lisr+2*kappa))


    return (pd.Series(mttgs, index=teams),pd.Series(swim,index=teams))

def mm(arr1,arr2):
    pooled = numpy.union1d(arr1,arr2)
    pooled_median = numpy.median(pooled)
    count1 = sum([1 for n in arr1 if n<=pooled_median])
    count2 = sum([1 for n in arr2 if n<=pooled_median])
    obs= numpy.hstack((numpy.array([count1,len(arr1)-count1]).reshape(2,1),numpy.array([count2,len(arr2)-count2]).reshape(2,1)))
    aa = obs[0,0]
    ab = obs[0,1]
    ba = obs[1,0]
    bb = obs[1,1]
    sm = aa+bb+ab+ba
    col1 = numpy.array([(aa+ab)*(aa+ba)/sm,(aa+ba)*(ba+bb)/sm]).reshape(2,1)
    col2 = numpy.array([(aa+ab)*(ab+bb)/sm,(ab+bb)*(ba+bb)/sm]).reshape(2,1)
    exp = numpy.hstack((col1,col2))
    x2 = sum(sum((obs-exp)**2/exp))
    z = -numpy.sqrt(x2)
    p = norm(0, 1).cdf(z)*2
    modifier = 0
    if(numpy.median(arr1)<=numpy.median(arr2)):
        modifier=1
    else:
        modifier=-1
    return modifier*p
def find_time(dat, name,is_isr): 
    subset = dat[(dat.wteam==name) & (dat.period=='RT')]
    isr = ''
    if is_isr:
        isr="ISR"
    else:
        isr="OSR"
    return numpy.median(subset[subset.distance==isr].gtime)-1080
def find_diff (dat,name):
    return find_time(dat,name,False)-find_time(dat,name,True)
def get_three(dat,year): 
    subset = year_data(dat,year)
    teams = numpy.union1d(subset.wteam.unique(),subset.lteam.unique())
    mttg, swim = teams_data(dat,year)
    diffs = pd.Series([find_diff(subset,team) for team in teams],index=teams)
    return (mttg,swim,diffs)





    
    
