import pandas as pd
import json
import pandas as pd
import pyodbc
import datetime
#import ceODBC
from time import gmtime, strftime, mktime
from datetime import date,time,timedelta, datetime
import pickle
import json

site_details = pd.io.pickle.read_pickle(r'C:\Users\amohan\Documents\IPython Notebooks\site_details.pkl')
u = '#79BD3B'
site = '#474747'


##########################################################################  FUNCTIONS  #######################################################################

#----------------------------- Peak Classification -----------------------------#

HOLIDAYS = [
    date(2016,1,1),
    date(2016,2,15),
    date(2016,5,30),
    date(2016,7,4),
    date(2016,9,5),
    date(2016,11,11),
    date(2016,11,24),
    date(2016,12,25),
    date(2015,1,1),
    date(2015,2,16),
    date(2015,5,25),
    date(2015,7,4),
    date(2015,9,7),
    date(2015,11,11),
    date(2015,11,26),
    date(2015,12,25),
    date(2014,1,1),
    date(2014,2,17),
    date(2014,5,26),
    date(2014,7,4),
    date(2014,9,1),
    date(2014,11,11),
    date(2014,11,27),
    date(2014,12,25),
    date(2013,1,1),
    date(2013,2,18),
    date(2013,5,27),
    date(2013,7,4),
    date(2013,9,2),
    date(2013,11,11),
    date(2013,11,28),
    date(2013,12,25),
    #...
]

peak, part_peak, off_peak = ('Peak', 'Part-peak', 'Off-peak')

def classify_by_peaksum(ts):

    if ts.date() in HOLIDAYS or ts.weekday() in (5, 6):
        return off_peak

    ts_time = ts.time()

    if ts_time < time(8,30) or ts_time > time(20,30): 
        return off_peak
    if ts_time < time(12,0) or ts_time > time(18,0): 
        return part_peak

    return peak


    

def classify_by_peakwin(ts):        

     
    if ts.weekday() in (5, 6) or ts.date() in HOLIDAYS:
        return off_peak

    ts_time = ts.time()

    if ts_time < time(8,30) or ts_time > time(21,30):
        return off_peak
    
    if time(8,30) <= ts_time <= time(21,30):
        return part_peak

    return peak
    

#----------------------------- Interval Count -----------------------------#

'''
Goes through the received data and estimates the number of data packets that should be there assuming a 15 minute interval so that it can be compared against actual value
'''
def total_time(chunk):
    df1 = chunk
    #print chunk.head()
    try:
        tt = pd.to_datetime(df1.index[len(df1.index)-1]) - pd.to_datetime(df1.index[0])
        ttcount = round(tt.total_seconds()/900,0)
        #ttcount = ttcount+1
    except:
        ttcount = 0
        
    #print ttcount
    return ttcount


#----------------------------- NVD3 usable form conversion -----------------------------#

def for_nvd3(frame, col, color, area):
    frame = frame[col]
    frame = frame.sort_index()
    index = frame.index

    if isinstance(index[0],unicode):
        index = [index[i].encode('utf-8') for i in range(len(index))]
        index = [mktime(datetime.strptime(s, "%Y-%m-%d").timetuple())
                for s in index]
    elif type(index[0]) == pd.tslib.Timestamp:
        index = pd.to_datetime(pd.Series(index))
        index = [str(index[i]) for i in range(len(index))]
        index = [mktime(datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timetuple())
                for s in index]        # time stamp to UTC to Local CA TIME!!!!
    values = frame.tolist()
    frame = pd.DataFrame(frame)
    dic = [{'x': idx*(10**3), 'y': val} for idx, val in zip(index, values)]
    dic = {
            'key': frame.columns.values[0],
            'values': dic,
            'color': color,
            'area': area
        }
    return dic

#----------------------------- individual Site : Status Calculation -----------------------------#

def status_checkfn(site_name, mac):
    
    sql1 = """
    select MeasuredTime, Rolling15MinuteAverage, Rolling15MinStoragePower, TargetPeak, BatSoc, BatteryOutput from peakshaving (nolock)
    where MeasuredTime > DATEADD(day,-1,GETUTCDATE())
    and MeasuredTime < GETUTCDATE()
    and GatewayMac = '%s'
   
    order by MeasuredTime"""%(mac)
    
    conn = pyodbc.connect(DRIVER='{SQL Server}',SERVER='reportingdb',DATABASE='EnergyStorage',Trusted_Connection='yes', autocommit=True)

    df = pd.io.sql.read_frame(sql1, conn)
    try:
        temptime = df['MeasuredTime'][0]
    except:
        print "currently not opertional"
    
    df['MeasuredTime'] = df['MeasuredTime'].apply(lambda x : x.tz_localize('UTC').tz_convert('US/Pacific'))

    df = df.set_index('MeasuredTime', verify_integrity=False)

    unsampled = df
    unsampled = unsampled.reset_index()
    unsampled['MeasuredTime'] = unsampled['MeasuredTime'].apply(lambda t: datetime(t.year,t.month,t.day,t.hour,t.minute,t.second))
    unsampled = unsampled.set_index('MeasuredTime', verify_integrity=False)

    df = df.resample('15min', how='first')
    cnt = df['Rolling15MinuteAverage'].count()-1
    #site_name = site_details[site_details['mac'] == mac]['Name'].reset_index(drop=True)[0]

    
    if cnt == 96:
        #temp = [site_name,mac,'Pass',df['Rolling15MinuteAverage'].max(),df['TargetPeak'][-1],'100', 'NA']
        temp = [site_name,'No',round(df['Rolling15MinuteAverage'].max(),1),df['TargetPeak'].unique().size - 1,df[df['BatSoc'] < 15]['BatSoc'].count(),df[df['BatteryOutput'] > 0]['BatteryOutput'].count(),'100%', temptime,'Yes']


    

    else:
        x = float(cnt*100/96)

        
  
        #plt.show()
        sql2 = """
        select top 1 MeasuredTime, Rolling15MinuteAverage from peakshaving (nolock)
       
        where GatewayMac = '%s'
       
        order by MeasuredTime desc"""%(mac)
        faildt = pd.io.sql.read_frame(sql2, conn)
        t = faildt['MeasuredTime'][0].tz_localize('UTC').tz_convert('US/Pacific')
        faildt['MeasuredTime'][0] = datetime(t.year,t.month,t.day,t.hour,t.minute,t.second)
        #temp = [site_name,'Yes',df['Rolling15MinuteAverage'].max(),'NA',cnt*100/96, faildt['MeasuredTime'][0]]
        if faildt['MeasuredTime'][0] > (datetime.now() - timedelta(0,0,0,0,15)):
            t = 'Yes'
        else:
            t = 'No'
        temp = [site_name,'Yes',round(df['Rolling15MinuteAverage'].max(),1),'NA',df[df['BatSoc'] > 15]['BatSoc'].count(),df[df['BatteryOutput'] > 0]['BatteryOutput'].count(),str(cnt*100/96) + '%', faildt['MeasuredTime'][0],t]        

    
    temp = pd.DataFrame(temp).transpose()
    #temp.columns = ['Site','Mac Address','Status','Max Peak','Target Peak','Time of Operation (%)','Time of Last Operation']
    temp.columns = ['Site','Missing Data','Max Peak','No. Trgt Peak Changes','Energy Constraint','Did Battery Discharge','Uptime Availability','Time of Last Operation', 'Currently Operational']

    
    conn.close()    
    return temp, unsampled


#----------------------------- Individual Site : Monthly Performance Summary -----------------------------#


def monthly_summaryfn(site_name, mac):
    
    dt1 = datetime(gmtime().tm_year,gmtime().tm_mon,gmtime().tm_mday,gmtime().tm_hour,gmtime().tm_min,gmtime().tm_sec)
    st = [1,2,3,11,12]
    if dt1.month in st:
        h = 8
    else:
        h = 7  
        
        
    sql1 = """
    select * from peakshaving (nolock)
    where MeasuredTime > '%d-%d-01 %d:00:00' 
    and MeasuredTime < GETUTCDATE()
    and GatewayMac = '%s'
   
    order by MeasuredTime"""%(dt1.year,dt1.month,h,mac)
    
    #print sql1
    conn = pyodbc.connect(DRIVER='{SQL Server}',SERVER='reportingdb',DATABASE='EnergyStorage',Trusted_Connection='yes', autocommit=True)

    df = pd.io.sql.read_frame(sql1, conn)
    if mac == '0004F3028DE7' or mac == '00409D581833':
        df['Rolling15MinStoragePower'] = df['Rolling15MinStoragePower'] * (-1)
        df['BatteryOutput'] = df['BatteryOutput'] * (-1)
        
    if df['MeasuredTime'][0].month in Summer:
        x = 1 #Summer
    else:
        x = 0 #Winter
        
        
    df = df.set_index('MeasuredTime', verify_integrity=False)
    df.index = df.index.tz_localize('UTC').tz_convert('US/Pacific')
    df = df.resample('15min', how='first')
    
    df['NetLoad'] = df['Rolling15MinuteAverage'] + df['Rolling15MinStoragePower']

    groupednet = df['NetLoad'].max()
    groupednettime = df['NetLoad'].idxmax()
    groupedroll = df['Rolling15MinuteAverage'].max()
    groupedrolltime = df['Rolling15MinuteAverage'].idxmax()
    groupedbat = groupednet - groupedroll
    
#    print mac, groupedbat, grouped5[1:]
    #site_name = site_details[site_details['mac'] == mac]['Name'].reset_index(drop=True)[0]

    cnt = df['Rolling15MinuteAverage'].count()-1
    ideal_count = total_time(df)
    if cnt == ideal_count:
        temp = [site_name,'No',df['Rolling15MinuteAverage'].max(),groupedbat,'100%', 'Yes']

       

    else:
        x = float(cnt*100/ideal_count)

  
        #plt.show()
        sql2 = """
        select top 1 MeasuredTime, Rolling15MinuteAverage from peakshaving (nolock)
       
        where GatewayMac = '%s'
       
        order by MeasuredTime desc"""%(mac)
        faildt = pd.io.sql.read_frame(sql2, conn)
        t = faildt['MeasuredTime'][0].tz_localize('UTC').tz_convert('US/Pacific')
        faildt['MeasuredTime'][0] = datetime(t.year,t.month,t.day,t.hour,t.minute,t.second)

        if faildt['MeasuredTime'][0] > (datetime.now() - timedelta(0,0,0,0,15)):
            t = 'Yes'
        else:
            t = 'No'

        temp = [site_name,'Yes',df['Rolling15MinuteAverage'].max(),groupedbat,str(round(cnt*100/ideal_count,1))+'%', t]
    
    
    temp = pd.DataFrame(temp).transpose()    
    #temp.columns = ['Site','Mac Address','Status','Max Peak','Demand Shaving(kW)','Time of Operation (%)','Time of Last Operation ']
    temp.columns = ['Site','Missing Data','Max Peak','Demand Shaving(kW)','Uptime Availability','Currently Operational']

    conn.close()




    n = df['NetLoad'].resample('d', how= 'max')
    n1 = n.max()
    m = df['Rolling15MinuteAverage'].resample('d', how= 'max')
    m1 = m.max()
    maxmoddemand = n1
    maxactdemand = m1

    def j(chunk):
        try:
            idx = chunk.idxmax()
        except:
            idx = None
        return idx



    load = []
    bat = []
    p = df['NetLoad'].resample('d', how = j)


    for i in range(len(m)):
        try :
            
            #load.append(df['Rolling15MinuteAverage'][p[i]])
            #l = max((df['Rolling15MinStoragePower'][p[i]]),0)
            #tl =  df['Rolling15MinuteAverage'][p[i]] + l
            load.append(m[i])
            batday = n[i] - m[i]
            bat.append(batday)
        except: 
            load.append(0)
            bat.append(0)  

    joined = pd.concat([p,m,n-m], axis = 1)
    joined.columns = ['Peak-Time', 'Peak','Demand Shaving']
    return temp, joined



#----------------------------- Individual Site : Overall Performance Summary -----------------------------#


def summaryfn(site_name, mac):
    
    dt1 = datetime(gmtime().tm_year,gmtime().tm_mon,gmtime().tm_mday,gmtime().tm_hour,gmtime().tm_min,gmtime().tm_sec)
    st = [1,2,3,11,12]
    if dt1.month in st:
        h = 8
    else:
        h = 7  
        
        
    sql1 = """
    select * from peakshaving (nolock)

    where MeasuredTime < GETUTCDATE()
    and GatewayMac = '%s'
   
    order by MeasuredTime"""%(mac)
    
    #print sql1
    conn = pyodbc.connect(DRIVER='{SQL Server}',SERVER='reportingdb',DATABASE='EnergyStorage',Trusted_Connection='yes', autocommit=True)

    df = pd.io.sql.read_frame(sql1, conn)
    if mac == '0004F3028DE7' or mac == '00409D581833':
        df['Rolling15MinStoragePower'] = df['Rolling15MinStoragePower'] * (-1)
        df['BatteryOutput'] = df['BatteryOutput'] * (-1)
        
    if df['MeasuredTime'][0].month in Summer:
        x = 1 #Summer
    else:
        x = 0 #Winter
        
        
    df = df.set_index('MeasuredTime', verify_integrity=False)
    df.index = df.index.tz_localize('UTC').tz_convert('US/Pacific')
    df = df.resample('15min', how='first')
    
    df['NetLoad'] = df['Rolling15MinuteAverage'] + df['Rolling15MinStoragePower']

    groupednet = df['NetLoad'].resample('m', how = 'max')
    
    groupedroll = df['Rolling15MinuteAverage'].resample('m', how = 'max')

    groupedbat = groupednet - groupedroll
    
#    print mac, groupedbat, grouped5[1:]
    #site_name = site_details[site_details['mac'] == mac]['Name'].reset_index(drop=True)[0]

    peak = pd.concat([groupedroll,groupedbat], axis = 1, join = 'inner')
    peak.columns = ['Actual - Max Demand','Demand Shaving']
    peak = peak[peak['Demand Shaving'] < int(site_details[site_details['mac'] == mac]['Battery Size'].reset_index(drop=True)[0])]
    conn.close()
    return peak



##########################################################################  SEASONS  #######################################################################


    
Summer = [5,6,7,8,9,10]
Winter = [1,2,3,4,11,12]