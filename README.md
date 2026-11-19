

def load_data():
    if not DATA.exists():
        return {'days': [], 'generated_at': None}
    obj = json.loads(DATA.read_text('utf-8'))
    if not isinstance(obj.get('days'), list):
        raise ValueError('data/contributions.json requires a days array')
    return obj


def daily_counts(obj):
    result={}
    for entry in obj.get('days', []):
        try:
            day=dt.date.fromisoformat(entry['date'])
            count=max(0,int(entry['count']))
        except (KeyError,ValueError,TypeError) as exc:
            raise ValueError(f'invalid contribution record: {entry!r}') from exc
        result[day]=count
    return result


def metrics(days):
    if not days:
        return 0,0,None,0
    last=max(days)
    active=sum(n>0 for n in days.values())
    busiest=max(days, key=lambda d:(days[d],-d.toordinal()))
    # Current streak is consecutive days through today or yesterday in UTC;
    # tolerate today's data having zero because the day may be incomplete.
    today=dt.datetime.now(dt.timezone.utc).date()
    current=min(last,today)
    if days.get(current,0)==0:
        current-=dt.timedelta(days=1)
    streak=0
    while days.get(current,0)>0:
        streak+=1
        current-=dt.timedelta(days=1)
    return streak,active,busiest,days[busiest]


def hero():
    b='''<defs><radialGradient id="shine" cx="65%" cy="35%" r="75%"><stop stop-color="#1A3B66"/><stop offset="1" stop-color="#0B1120"/></radialGradient></defs>
<rect x="2" y="2" width="916" height="256" rx="21" fill="url(#shine)"/>
<circle cx="784" cy="125" r="95" fill="none" stroke="#70A5FD" stroke-opacity=".22" stroke-width="1.5"/>
<circle cx="784" cy="125" r="72" fill="none" stroke="#70A5FD" stroke-opacity=".38" stroke-width="1.5"/>
<path d="M725 145 L760 105 L785 130 L845 68" fill="none" stroke="#70A5FD" stroke-width="4" stroke-linecap="round" class="draw"/>
<circle cx="845" cy="68" r="6" fill="#70A5FD"/>
'''
    b += '<g class="reveal">'+pill(42,34,'FRONTEND ENGINEER',183)+text(42,117,'Bhargav Thakar',51,TEXT,700)+text(44,160,'Crafting thoughtful web experiences, one pixel at a time.',19,MUTED)+text(44,218,'RAJKOT, INDIA   /   BUILDING FOR THE WEB',12,ACCENT,700,'letter-spacing="1.6"')+'</g>'
    # Optional portrait: user can add assets/portrait.png; embed it for image proxy compatibility.
    for ext,mime in [('png','image/png'),('jpg','image/jpeg'),('webp','image/webp')]:
        p=ROOT/'assets'/f'portrait.{ext}'
        if p.exists():
            href='data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
            b += f'<defs><clipPath id="portrait"><circle cx="785" cy="125" r="63"/></clipPath></defs><image href="{href}" x="722" y="62" width="126" height="126" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait)"/>'
            break
    write('hero.svg',920,260,b,delay=0,title='Bhargav Thakar — Frontend Engineer')


def tiles():
    configs=[('01 / GITHUB','Explore my code','Repositories & experiments','github.svg'),('02 / LINKEDIN','Let’s connect','Engineering & career','linkedin.svg'),('03 / CODEPEN','Creative playground','UI explorations','codepen.svg')]
    for i,(eyebrow,title,desc,name) in enumerate(configs):
        b='<circle cx="273" cy="40" r="70" fill="#172B48" opacity=".8"/>'
        b+='<g class="reveal">'+text(24,34,eyebrow,11,ACCENT,700,'letter-spacing="1"')+text(24,77,title,21,TEXT,700)+text(24,106,desc,12,MUTED)+text(271,121,'↗',21,ACCENT,700)+'</g>'
        write(name,298,140,b,delay=.55+i*.17,title=title)


def activity(days):
    streak,active,busiest,peak=metrics(days)
    end=max(days) if days else dt.datetime.now(dt.timezone.utc).date()
    months=[]
    month=dt.date(end.year,end.month,1)
    for i in range(11,-1,-1):
        year=month.year+(month.month-1-i)//12
        m=(month.month-1-i)%12+1
        months.append(dt.date(year,m,1))
    totals={m:sum(n for day,n in days.items() if day.year==m.year and day.month==m.month) for m in months}
    maximum=max(totals.values(),default=0)
    b=heading('Contribution cadence','Consistency, measured monthly')
    b+='<g class="reveal">'+pill(40,102,f'{streak} day streak',151)+pill(208,102,f'{active} active days',166)
    busiest_label=busiest.strftime('%d %b %Y') if busiest else 'No activity yet'
    b+=pill(392,102,f'Peak: {peak} on {busiest_label}',235 if busiest else 210)+'</g>'
    base_y=348
    for i,m in enumerate(months):
        n=totals[m]; x=45+i*71; height=15+round(n/max(1,maximum)*151) if n else 5
        b+=f'<rect x="{x}" y="{base_y-height}" width="36" height="{height}" rx="6" fill="{ACCENT}" opacity="{.5+.5*n/max(1,maximum):.2f}" class="{ "" if STATIC else "bar" }" style="animation-delay:{1.35+i*.065:.2f}s"/>'
        b+=text(x+18,373,m.strftime('%b'),12,MUTED,400,'text-anchor="middle"')
        b+=text(x+18,base_y-height-9,str(n),12,TEXT,700,'text-anchor="middle"')
    b+=text(45,404,'Contributions from public and accessible private activity reported by GitHub',12,MUTED)
    write('activity.svg',920,428,b,delay=1.05,title='Monthly contributions and activity metrics')


def projects():
    for i,(name,tag,desc,stack,url) in enumerate(FEATURED):
        b='<rect x="670" y="24" width="214" height="146" rx="18" fill="#12233D"/>'
        b+='<path d="M695 122 L737 82 L776 111 L821 55 L861 88" fill="none" stroke="#70A5FD" stroke-width="3" class="draw"/>'
        b+='<g class="reveal">'+text(40,44,f'FEATURED PROJECT  /  0{i+1}',11,ACCENT,700,'letter-spacing="1.6"')+text(40,91,name,34,TEXT,700)+text(40,125,tag,18,MUTED)+text(40,155,desc,14,MUTED)+pill(40,183,stack,max(200,len(stack)*7.6+25))+'</g>'
        write(f'project-{i+1}.svg',920,236,b,delay=1.65+i*.21,title=f'{name} — {tag}')


def heatmap(days):
    end=max(days) if days else dt.datetime.now(dt.timezone.utc).date()
    start=end-dt.timedelta(days=364)
    # Align to start Sunday, using weekday Sunday=0
    start-=dt.timedelta(days=(start.weekday()+1)%7)
    end_week=start+dt.timedelta(days=371)
    weeks=math.ceil(((end_week-start).days+1)/7)
    values=list(days.values())
    maxv=max(values,default=0)
    b=heading('Contribution graph','A year of showing up')
    b+='<g class="reveal">'+text(40,108,f'{sum(days.get(end-dt.timedelta(days=i),0) for i in range(365)):,} contributions in the last 365 days',14,MUTED)
    for i in range(weeks):
        for weekday in range(7):
            date=start+dt.timedelta(days=i*7+weekday)
            n=days.get(date,0)
            if date>end: continue
            opacity=0 if n==0 else (.22+.78*min(1,math.log1p(n)/math.log1p(max(1,maxv))))
            fill=SOFT if not n else ACCENT
            x=41+i*15.5; y=148+weekday*17
            b+=f'<rect x="{x:.1f}" y="{y}" width="12.8" height="12.8" rx="3" fill="{fill}" opacity="{1 if not n else opacity:.2f}"/>'
    b+='</g>'+text(41,295,f'{start:%d %b %Y}  —  {end:%d %b %Y}',12,MUTED)
    b+=text(744,295,'LESS',11,MUTED)+''.join(f'<rect x="{780+i*19}" y="285" width="13" height="13" rx="3" fill="{ACCENT if i else SOFT}" opacity="{(.18+i*.2) if i else 1}"/>' for i in range(5))
    write('contributions.svg',920,324,b,delay=2.35,title='GitHub contribution heatmap in blue')


def main():
