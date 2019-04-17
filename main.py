import sqlite3
from sqlite3 import Error
from random import random as rand
from random import sample
import flask
from threading import Lock
import math, sys
from Investors import create_Investors
from dash import Dash, no_update
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
from plotly import graph_objs as go

# Thread lock
lock = Lock()

# Refresh interval in secs
refresh_interval = 10

# The size of Investors pool
population_size = 10000

# Create a Investors table and return a cursor object
con, cursor = create_Investors(population_size)

# curr_week = 0

# Fetch all rows from the Investors table
data_rows = cursor.execute("SELECT * from Investors").fetchall()

# sample 10 initial members ids randomly
initial_members = sample(data_rows, 10)

##<<---Update the status of selected member(s) in Inverstors table to 'Un-Available'--->>##
# Iterator to run the executemany update query
def Status_iterator(rows):
    for r in rows:
        yield "Un-Available", r['id']

# To avoid recursive cursor error we use thread locks for each query
try:
    lock.acquire(True)
    cursor.executemany("Update Investors SET Status=? where id = (?)", Status_iterator(initial_members))
    con.commit()
except Error as e:
    print(e.args[0])
    print("line 44")
    sys.exit()
finally:
    lock.release()

##<<---Create a Members table to hold information for current active members--->>##
try:
    lock.acquire(True)
    # drop the table if it already exists
    cursor.execute("DROP TABLE IF EXISTS Members")
    # commit changes to database
    con.commit()

    # Create the Members table
    cursor.execute("CREATE TABLE Members(M_Id integer PRIMARY KEY, \
        Name text, Innocence real, Experience real, Charisma real, \
        Status text, Money_trend text, Recruitor integer, Investor_id\
        integer, start_week integer, end_week integer)")
    con.commit()

except Error as e:
    print(e.args[0])
    print("line 66")
    sys.exit()
finally:
    lock.release()


##<---Insert Mummy and other 10 members into the Members table--->##
# Iterator/function that returns/yields 
# data to insert into Members table
def insert_Iterator(rows, rec_id, start_week):
    # end_week -> math.floor((1-Innocence) x Experience x Charisma x 10)
    for r in rows:
        yield r['Name'], r['Innocence'], r['Experience'], r['Charisma'],\
            "Active", "0-", rec_id, r['Id'], start_week, start_week + \
            math.floor((1-r['Innocence'])*r['Experience']*r['Charisma']*10)

try:
    lock.acquire(True)
    cursor.execute("Insert into Members(Name, Innocence, Experience, Charisma, \
        Status, Money_trend, Recruitor, Investor_id, start_week, end_week) VALUES\
            ('Mummy', 0, 1, 1, 'Proactive', '5000-', -1, 0, 0, 10000)")
    cursor.executemany("Insert into Members(Name, Innocence, Experience, Charisma, \
        Status, Money_trend, Recruitor, Investor_id, start_week, end_week) VALUES\
            (?,?,?,?,?,?,?,?,?,?)", insert_Iterator(initial_members, 1, 0))
    con.commit()

except Error as e:
    print(e.args[0])
    print("line 94")
    sys.exit()
finally:
    lock.release()

# Function to generate the money trend plot
def get_figure(data):

    member_money = data['Money_trend'].split('-')[:-1]

    y = [int(m) for m in member_money]
    x = list(range(1,len(y)+1))
    hover_info = ["Money Earned : $"+m for m in member_money]

    trace_exp = go.Scatter(
        x=x,
        y=y,
        text=hover_info,
        hoverinfo='text',
        mode="lines+markers",
        name="Money",
        line=dict(color="#bcdeba")
    )

    data=[trace_exp]

    colors = {
        'background': 'white',
        'text': 'black'
    }

    layout = go.Layout(
        showlegend = False,
        hovermode='closest',
        plot_bgcolor = colors['background'],
        paper_bgcolor = colors['background'],
        font = dict(color = colors['text']),
        height=300,
        xaxis=dict(
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=False
        ),
        yaxis=dict(
            autorange=True,
            showgrid=True,
            zeroline=False,
            showline=True,
            tickwidth=2,
            showticklabels=True
        )
    )

    fig = go.Figure(data = data, layout = layout)

    return fig


# Function to generate/update weeks info
def get_weeks_div(data, week, cnt_new, avl_inv):

    avg_money, active_cnt, cnt_elim = 0, 0, 0

    # get mummys' total earnings
    for member in data:
        if member['end_week'] - member['start_week'] == 0:
            cnt_elim += 1
        if member['M_Id'] == 1:
            mummy_total = member['Money_trend'].split('-')[-2]
        else:
            active_cnt += 1
            money = member['Money_trend'].split('-')[-2]
            avg_money += int(money)                

    if active_cnt == 0:
        avg_money = 0
    else:
        avg_money /= active_cnt

    div_data = [
        html.Br(),
        html.H5("Stats for this Week"),
        html.H6("Available Investors   : "+str(avl_inv)),
        html.H6("Total Active Members  : "+str(active_cnt)),
        html.H6("Mummys' Total Earnings: $"+mummy_total, id="mummy_money"),
        html.Br(),
        "New Members: "+str(cnt_new),
        html.Br(),
        "Under Elimination: "+str(cnt_elim),
        html.Br(),
        html.P("Avg. Member Earning: $"+str(round(avg_money, 2)), id="mem_money")
    ]

    return div_data

new_data = cursor.execute("Select * from Members WHERE Status='Active' OR Status='Proactive'").fetchall()

names = [str(d['M_Id']) + '. ' + d['Name'] for d in new_data]

external_stylesheets = [
    'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css'
]

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    
    #### HEADER ####
    html.Div([
        html.H2('''Welcome to Mummy Money Get Rich\u2122'''),
        html.Img(src="/assets/pic.png")
    ], className="banner"),
    
    #### LEFT STATS PANEL ####
    html.Div([      
        html.Div([
                html.Div([html.Div([html.H4("Stats Card")], className="card-title"),
                    html.Div(get_weeks_div(new_data, 0, 10, 9990), id="weeks_div"),
                    html.Br()
                ], id="info_div"),
                html.Button('End Scheme', id="end_btn", className="btn btn-danger"),
        ], className="col-sm-3 mx-auto text-center", id="stats_div"),
        #### RIGHT MONEY TREND PANEL ####
        html.Div([
            html.Div([html.H4("Mummy Money Trend")], className="card-title"),
            html.Div([
                dcc.Dropdown(options=[{'label': v, 'value': v} for v in names], value="1. Mummy", id="ddownbtn", searchable = False)
            ], id="ddownDiv"),
            html.Div([
                html.Div([dcc.Graph(id='live-graph', figure=get_figure(new_data[0]))], id='graph-div'),
                dcc.Interval(id='graph-update', interval=refresh_interval*1000, n_intervals=0),
            ])
        ], className="col-sm-8 mx-auto text-center", id="fig_div")
    ], className="row no-gutter", id="display_div"),

    html.Div([        
        html.Div([
            html.Div(html.H4("New Recruits"), className="card-title"),
            html.Div("NONE", id="recruit_data") 
        ], id="recr_div", className="col-sm-3 mx-auto text-center"),
        
        html.Div([
            html.Div(html.H4("Eliminated"), className="card-title"),
            html.Div("NONE", id="elim_data")
        ], id="elim_div", className="col-sm-3 mx-auto text-center"),

        html.Div([
            html.Div(html.H4("Withdrawn"), className="card-title"),
            html.Div("NONE", id="with_data")
        ], id="with_div", className="col-sm-3 mx-auto text-center")

    ], className="row no-gutter", id="membs_info_div")

], className="container-fluid")

# Iterator to update member tree
def tree_update_iterator(child_members, new_parent):
    for child_member in child_members:
        yield new_parent, child_member['M_Id']


# The function update_member_table:
#   1. Updates the member tree
#   2. Updates leaving member as Inactive 
#   3. Adds money to mummys earning if 
#      members tenure ran out
# Set 'withdrawal' as TRUE if member withdrew his funds deliberately
def update_member_table(leaving_member, active_members, n, withdrawal=False):
    global cursor, con

    # New parent of child members
    new_parent = leaving_member['Recruitor']

    # Get mummys' record
    mummy_record = cursor.execute("SELECT * FROM Members WHERE M_Id = 1").fetchone()

    # Get all child members
    child_members = [member for member in active_members if member['Recruitor'] == leaving_member['M_Id']]

    try:
        lock.acquire(True)
        # Mark the leaving member as inactive
        cursor.execute("UPDATE Members SET Status=? WHERE M_Id=?", ('Inactive', leaving_member['M_Id']))

        # Update the tree
        cursor.executemany("UPDATE Members SET Recruitor=? WHERE M_Id=?", tree_update_iterator(child_members, new_parent))

        if withdrawal == False:
            # Update Mummys' money by adding the leaving members money
            mummy_total_money   = int(mummy_record['Money_trend'].split('-')[-2])
            members_total_money = int(leaving_member['Money_trend'].split('-')[-2])
            new_mummy_money = mummy_record['Money_trend'] + str(mummy_total_money + members_total_money) + '-'
            cursor.execute("UPDATE Members SET Money_trend=? WHERE M_Id=?", (new_mummy_money, 1))

        # Commit changes to database
        con.commit()

    except Error as e:
        print(e.args[0])
        print("Line 275")
        sys.exit()
    finally:
        lock.release()


def insert_member(rows, rec_id, start_week):
    return rows['Name'], rows['Innocence'], rows['Experience'], rows['Charisma'],\
        "Active", "0-", rec_id, rows['Id'], start_week, start_week + \
        math.floor((1-rows['Innocence'])*rows['Experience']*rows['Charisma']*10)


def recruit_member(member, active_members, n):
    
    global con, cursor

    ### If no Investors are available return ###
    try:
        lock.acquire(True)
        available_investors = cursor.execute("SELECT * FROM\
        Investors WHERE Status='Available'").fetchall()
    except Error as e:
        print(e.args[0])
        print("line 298")
        sys.exit()  
    finally:
        lock.release()

    if len(available_investors) < 1:
        return

    ### Else run the recuiting simulation ###
    # Count direct-members recruited by member
    X = sum(1 for membs in active_members if membs['M_Id'] == member["M_Id"])

    # Get mummys' record
    try:
        lock.acquire(True)     
        mummy_record = cursor.execute("SELECT * FROM Members WHERE M_Id = 1").fetchone()
    except Error as e:
        print(e.args[0])
        print("line 316")
        sys.exit()
    finally:
        lock.release()

    # Compute the recruiting threshold probability
    if X == 1:
        p_thresh = 0
    else:
        p_thresh = member['Experience'] * member['Charisma'] * (1-math.log10(X))

    # Probability of recruiting
    p_recruit = rand()

    # A new member is recruited if this condition is met
    if p_recruit > p_thresh:
        # Randomly sample a Investor
        new_member = sample(available_investors, 1)[0]

        # Acceptance threshold probaility
        p_accept_thresh = new_member['Innocence'] * (1 - new_member['Experience'])

        # Probability of acceptance
        p_accept = rand()

        # Investor accepts the offer
        if p_accept > p_accept_thresh:

            # Insert the new member in Members table
            try:
                lock.acquire(True)
                cursor.execute("INSERT into Members(Name, Innocence, Experience, Charisma, \
                    Status, Money_trend, Recruitor, Investor_id, start_week, end_week) VALUES\
                    (?,?,?,?,?,?,?,?,?,?)", (insert_member(new_member, member['M_Id'], n)))

                new_recruit = str(cursor.lastrowid) + '. ' + new_member['Name']

                # Update status of member in Investors table
                cursor.execute("UPDATE Investors SET Status=? WHERE Id=?", ('Un-Available', new_member['Id']))

                # Add $400 to Mummys account and $100 to recruiting members account
                mummy_total_money   = int(mummy_record['Money_trend'].split('-')[-2])
                members_total_money = int(member['Money_trend'].split('-')[-2])
                new_mummy_money     = mummy_record['Money_trend'] + str(mummy_total_money + 400) + '-'
                new_member_money    = member['Money_trend'] + str(members_total_money + 100) + '-'
                cursor.execute("UPDATE Members SET Money_trend=? WHERE M_Id=?",(new_member_money, member['M_Id']))        
                cursor.execute("UPDATE Members SET Money_trend=? WHERE M_Id=?", (new_mummy_money, 1))

                con.commit()
    
            except Error as e:
                print(e.args[0])
                print("Line 368")
                sys.exit()
            finally:
                lock.release()

            return new_recruit
    
    return -1


def run_weeks_simulation(active_members, n):

    week_summ_dict = {
        'recruited'  : [],
        'eliminated' : [],
        'withdrawn'  : []
    }

    for member in active_members:
        # Generate probility of withdrawl
        p_withdraw = rand()

        # Members tenure ran out
        if member['end_week']-member['start_week'] == 0:
            # Update the Members table
            update_member_table(member, active_members, n)
            week_summ_dict['eliminated'].append(\
                str(member['M_Id']) + '. ' + member['Name'])
        
        # Member withdraws
        elif p_withdraw > 0.85:
            update_member_table(member, active_members, n, withdrawal=True)
            week_summ_dict['withdrawn'].append(\
                str(member['M_Id']) + '. ' + member['Name'])

        # Run recruiting simulation
        else:
            res = recruit_member(member, active_members, n)
            if res != -1:
                week_summ_dict['recruited'].append(res)

    return week_summ_dict



@app.callback([Output('graph-div', 'children')], [Input('ddownbtn', 'value')])
def change_graph_member(value):

    global cursor

    # Get selected members M_Id
    m_id = int(value.split('.')[0])

    # Fetch members data from Members table
    try:
        lock.acquire(True)
        data = cursor.execute("SELECT * FROM Members WHERE M_Id=?", [m_id]).fetchone()
    except Error as e:
        print(e.args[0])
        print("line 420")
        sys.exit()
    finally:
        lock.release()
    
    # Generate figure
    fig = get_figure(data)

    new_fig = dcc.Graph(figure=fig, id="live-graph")

    return [new_fig]


# Dynamic update calls
@app.callback([Output('live-graph', 'figure'), Output('ddownDiv', 'children'), \
    Output('weeks_div', 'children'), Output('recruit_data', 'children'),\
    Output('elim_data', 'children'), Output('with_data', 'children')],\
    [Input('graph-update', 'n_intervals')], [State('ddownbtn', 'value')])
def update_graph_scatter(n, value):

    global con, cursor
    # print(n, curr_week)

    # Get list of active members
    try:
        lock.acquire(True)
        active_members = cursor.execute("Select * from Members WHERE Status='Active'").fetchall()
    except Error as e:
        print(e.args[0])
        print("line 447")
        sys.exit()
    finally:
        lock.release()

    # Run the weeks simulation for all active members
    week_summary = run_weeks_simulation(active_members, n)
    # print(week_summary)

    # Update recruited, eliminated and withdrawn members' list
    recruit_list, elim_list, with_list = [], [], []

    if len(week_summary['recruited']) == 0:
        recruit_list = "NONE"
    else:
        for rec_member in week_summary['recruited']:
            recruit_list.append(html.P(rec_member, className="rec_text"))

    if len(week_summary['eliminated']) == 0:
        elim_list = "NONE"
    else:
        for elim_member in week_summary['eliminated']:
            elim_list.append(html.P(elim_member, className="elim_text"))

    if len(week_summary['withdrawn']) == 0:
        with_list = "NONE"
    else:
        for with_member in week_summary['withdrawn']:
            with_list.append(html.P(with_member, className="with_text"))

    # Get updated-list of active members after simulation
    try:
        lock.acquire(True)
        active_members = cursor.execute("Select * from Members WHERE Status='Active' or Status='Proactive'").fetchall()
    except Error as e:
        print(e.args[0])
        print("line 464")
        sys.exit()
    finally:
        lock.release()

    # Update Options for dropdown selector
    opts = [{'label' : str(active_member['M_Id']) + '. ' + active_member['Name'], \
        'value' : str(active_member['M_Id']) + '. ' + active_member['Name']} \
        for active_member in active_members] #+ [{'label' : '1. Mummy', 'value' : '1. Mummy'}]

    # Update value for dropdown selector
    if value != '1. Mummy':    
        # Create selection options from list of active members
        mem_ids = set([str(m['M_Id'])+'. '+m['Name'] for m in active_members])

        if value not in mem_ids:
            new_value = "1. Mummy"
        else:
            new_value = value
    else:
        new_value = "1. Mummy"

    # Create the new dropdown menu
    new_dropdown = dcc.Dropdown(options=opts, value=new_value, id="ddownbtn", searchable = False)

    m_id = int(new_value.split('.')[0])

    # Fetch record for current selected user
    try:
        lock.acquire(True)
        member_record = cursor.execute("Select * from Members WHERE M_Id=?", [m_id]).fetchone()
        avl_inv = cursor.execute("SELECT COUNT(*) as cnt FROM Investors WHERE Status='Available'").fetchone()['cnt']
    except Error as e:
        print(e.args[0])
        print('line 497')
        sys.exit()
    finally:
        lock.release()

    fig = get_figure(member_record)
    weeks_div = get_weeks_div(active_members, n, len(week_summary['recruited']), avl_inv)

    return fig, [new_dropdown], weeks_div, recruit_list, elim_list, with_list

@app.callback([Output('display_div', 'children'), Output('graph-update','max_intervals'),\
        Output('membs_info_div', 'style')], [Input('end_btn', 'n_clicks')], \
        [State('mummy_money', 'children'), State('info_div', 'children'), State('mem_money','children')])
def on_click(n_clicks, mm_text, info_div, m_text):

    global cursor

    if n_clicks is not None and n_clicks == 1:

        print("Button Clicked!!")

        try:
            lock.acquire(True)
            total_members = cursor.execute("SELECT COUNT(*) as mem_cnt FROM Members").fetchone()
        except Error as e:
            print(e.args[0])
            sys.exit()
        finally:
            lock.release()

        res_div = html.Div([
            html.H2("MUMMY TERMINATED THE PROGRAM!!"),
            html.Br(),
            html.Div([
                    html.Div([html.H4("Program Summary: ")], className="card-title"),
                    html.Br(),
                    html.H6(mm_text),
                    html.H6(m_text),
                    html.H6("Total member recruited: "+str(total_members['mem_cnt']))
                ], className="mx-auto text-center col-sm-6", id="stats_div")
        ], className="mx-auto")

        return res_div, 0, {'display': 'none'}
    
    return no_update, no_update, no_update

if __name__ == "__main__":
    app.run_server(debug=False)