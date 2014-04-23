from django.shortcuts import render, render_to_response
from django.http import HttpResponse	
from django.template.loader import get_template
from django.template import Context
from django.views.generic.base import TemplateView
import pandas as pd
import json
import pandas as pd
import datetime
#import ceODBC
from time import gmtime, strftime, mktime
from datetime import date,time,timedelta, datetime
import json
from fns.functions import *


'''	 
dsn = 'sqlserverdatasource'
user = 'SolarGrid' # SolarGrid
password = 'nq761ScU' # nq761ScU
database = 'EnergyStorage' #SolarWorks
	 
con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
conn = pyodbc.connect(con_string)
'''

conn = pyodbc.connect(DRIVER='{SQL Server}',SERVER='reportingdb',DATABASE='EnergyStorage',Trusted_Connection='yes', autocommit=True)


# Create your views here.

def individual_index(request):
    jobid = []

    for mac in site_details['mac']:
    
        sql = """
        select top 1 vci.JobID, g.installationid, p.gatewaymac
        from Energystorage..peakshaving p(nolock)
        left join solarworks..gateways g on g.MacAddress = p.GatewayMac
        left join solarworks..vcustomersinstallationswithutility vci on vci.installationid = g.installationid
        where p.gatewaymac = '%s' 
        """%(mac)
        print site_details
        df = pd.io.sql.read_frame(sql,conn)
        site_name = site_details[site_details['mac'] == mac]['Name'].reset_index(drop=True)[0]
    
        df = pd.io.sql.read_frame(sql,conn)
        #df = pd.concat([df,site_name], axis = 1)
        jobid.append(df['JobID'][0])
    
    dic = {'gateways': site_details['mac'].tolist(), 'names': site_details['Name'].tolist(), 'jobid': jobid}
    data = json.dumps([dic])  
    data = zip(dic['jobid'], dic['names'], dic['gateways'])
    
    return render_to_response('individual_index.html', {'data': data })

    #return render_to_response('individual_index.html', {'g': site_details['mac'].tolist(), 'n' : site_details['Name'].tolist(), 'j' : jobid })


def hello(request):

	name = "Ara"
	html = "<html><body> Hi %s, this worked</body><html>" %name
	return HttpResponse(html)

def hello_template(request):

    name = "Ara"
    t = get_template('hello.html') # Load the template
    html = t.render(Context({'name' : name})) # Render it with the parameters we wish to pass
    return HttpResponse(html) # Send it back to the webserver in html format

def hello_template_simple(request):
    name = "Ara"
    return render_to_response('hello.html', {'name': name})


def home(request):

	name = "Ara"
	html = "<html><h2> home </h2><html>" 
	return HttpResponse(html)

class HelloTemplate(TemplateView):
    template_name = 'hello_class.html'

    def get_context_data(self, **kwargs):
        context = super(HelloTemplate, self).get_context_data(**kwargs)
        context['name'] = 'Ara'
        return context




##########################################################################  INDEX PAGE  #######################################################################
'''
The options to be shown are hard-coded in the .html file
'''

def index(request):

    t = get_template('index.html') 
    html = t.render(Context({})) 
    return HttpResponse(html) 
        
        
##########################################################################  FLEET STATUS CHECK  #######################################################################


def status_check(request):
    #DAILY CHECK


    status = pd.DataFrame()


    macs = site_details['mac'].tolist()


    for mac in macs:
        
        sql1 = """
        select MeasuredTime, Rolling15MinuteAverage, Rolling15MinStoragePower, TargetPeak, BatSoc, BatteryOutput from peakshaving (nolock)
        where MeasuredTime > DATEADD(day,-1,GETUTCDATE())
        and MeasuredTime < GETUTCDATE()
        and GatewayMac = '%s'
       
        order by MeasuredTime"""%(mac)
        #print sql1
        
        df = pd.io.sql.read_frame(sql1, conn)
        
        if len(df) != 0:
            
            t = df['MeasuredTime'][len(df)-1].tz_localize('UTC').tz_convert('US/Pacific')
            temptime = datetime(t.year,t.month,t.day,t.hour,t.minute,t.second)

        

        df = df.set_index('MeasuredTime', verify_integrity=False)
        try:
            df.index = df.index.tz_localize('UTC').tz_convert('US/Pacific')
        except:
            print mac, "could not localize"
        df = df.resample('15min', how='first')[1:]
        if mac == '0004F3028DE7' or mac == '00409D581833':
            df['Rolling15MinStoragePower'] = df['Rolling15MinStoragePower'] * (-1)
            df['BatteryOutput'] = df['BatteryOutput'] * (-1)

        cnt = df['Rolling15MinuteAverage'].count()
        
        site_name = site_details[site_details['mac'] == mac]['Name'].reset_index(drop=True)[0]

        
        if cnt == 96:
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
            if faildt['MeasuredTime'][0] > (datetime.now() - timedelta(0,0,0,0,15)):
                t = 'Yes'
            else:
                t = 'No'
                
            temp = [site_name,'Yes',round(df['Rolling15MinuteAverage'].max(),1),'NA',df[df['BatSoc'] > 15]['BatSoc'].count(),df[df['BatteryOutput'] > 0]['BatteryOutput'].count(),str(cnt*100/96) + '%', faildt['MeasuredTime'][0],t]        
            
        status = status.append(pd.DataFrame(temp).transpose())



    
    status.columns = ['Site','Missing Data','Max Peak','No. Trgt Peak Changes','Energy Constraint','Did Battery Discharge','Uptime Availability','Time of Last Operation', 'Currently Operational']

    '''
    if status['Time of Last Operation'].all() =='NA':
        status = status.drop('Time of Last Operation',1)
    if status['Energy Constraint'].all() ==0:
        status = status.drop('Energy Constraint',1)
    '''


   
    data = status.set_index('Site').to_html()


    return render_to_response("status_check.html",
                            {'data': data})




##########################################################################  FLEET MONTHLY SUMMARY  #######################################################################


def monthly_summary(request):
    #MONTHLY CHECK
    def rounding(x):
        return round(x,1)

    status = pd.DataFrame()


    macs = site_details['mac'].tolist()
    dt1 = datetime(gmtime().tm_year,gmtime().tm_mon,gmtime().tm_mday,gmtime().tm_hour,gmtime().tm_min,gmtime().tm_sec)
    st = [1,2,3,11,12]
    if dt1.month in st:
        h = 8
    else:
        h = 7  


    for mac in macs:

        sql1 = """
        select * from peakshaving (nolock)
        where MeasuredTime > '%d-%d-01 %d:00:00' 
        and MeasuredTime < GETUTCDATE()
        and GatewayMac = '%s'
       
        order by MeasuredTime"""%(dt1.year,dt1.month,h,mac)
        
        #print sql1

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
        site_name = site_details[site_details['mac'] == mac]['Name'].reset_index(drop=True)[0]

        cnt = df['Rolling15MinuteAverage'].count() - 1
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
            
        status = status.append(pd.DataFrame(temp).transpose())
        
   
    status.columns = ['Site','Missing Data','Max Peak','Demand Shaving(kW)','Uptime Availability','Currently Operational']
    status['Max Peak'] = status['Max Peak'].apply(rounding)
    status['Demand Shaving(kW)'] = status['Demand Shaving(kW)'].apply(rounding)
   
    data = status.set_index('Site').to_html()

    return render_to_response("monthly_summary.html",
                              {'data': data})




##########################################################################  INDIVIDUAL SITE ANALYSIS  #######################################################################



def individual_site(request, jobid):

    sql = """
    select top 1 vci.customername, g.installationid, p.gatewaymac
    from Energystorage..peakshaving p(nolock)
    left join solarworks..gateways g on g.MacAddress = p.GatewayMac
    left join solarworks..vcustomersinstallationswithutility vci on vci.installationid = g.installationid
    where vci.JobID = '%s' 
    """%(jobid)
    df = pd.io.sql.read_frame(sql,conn)
    mac = df['gatewaymac'][0]
    site_name = df['customername'][0]

    data1,unsampled1 = status_checkfn(site_name, mac)
    data1 = data1.set_index('Site').to_html()
 

    batdis = for_nvd3(unsampled1, 'Rolling15MinStoragePower', u, True)
    util = for_nvd3(unsampled1, 'Rolling15MinuteAverage', site, True)
    chart1 = json.dumps([util,batdis])
    # get customer details

    data2,joined = monthly_summaryfn(site_name, mac)
    data2 = data2.set_index('Site').to_html()
    mds = for_nvd3(joined, 'Demand Shaving', u, True)
    mpeak = for_nvd3(joined, 'Peak', site, True)
    
    chart2 = json.dumps([mpeak,mds])
    data3 = summaryfn(site_name, mac)
    actload = for_nvd3(data3, 'Actual - Max Demand', site, True)
    batload = for_nvd3(data3, 'Demand Shaving', u, True)
    chart3 = json.dumps([actload,batload])
    
    return render_to_response("indchart1.html",
    {'data1' : data1,
    'data2' : data2,
    'chart1' : chart1,
    'chart2' : chart2,
    'chart3' : chart3})