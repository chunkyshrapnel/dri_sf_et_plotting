import pandas as pd
import os
from scipy import stats
from bokeh.io import output_file, save, show, curdoc
from bokeh.plotting import figure
from bokeh.models import LinearAxis, Range1d, ColumnDataSource
from bokeh.models.tools import HoverTool
from bokeh.layouts import gridplot

# Bug notice: Some of the data recieved, had the leading '0' truncated off the front.
# For example '09180000' --> '9180000'
# If there are any errors with reading in the raw data, please check the site numbers.
'''site_list = ['09180000',        # 'DOLORES RIVER NEAR CISCO, UT',
             '09209400',        # ' GREEN RIVER NEAR LA BARGE, WY',
             '09260000',        # LITTLE SNAKE RIVER NEAR LILY, CO
             '09302000',        # DUCHESNE RIVER NEAR RANDLETT, UT,
             '09306500',        # WHITE RIVER NEAR WATSON, UTAH
             '09379500',        # SAN JUAN RIVER NEAR BLUFF, UT
             ]'''
site_list = ['09180000']

# Dictionary used to transfer between strings and ints.
month_dict = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Aug',
    9: 'Sept',
    10: 'Oct',
    11: 'Nov',
    12: 'Dec'
}

# Read in the metadata so that the site names can be attached to the graph.
try:
    df_metadata = pd.read_csv('raw_data/metadata.csv')
except:
    print("ERROR WITH READING METADATA")
    exit(1)

curdoc().theme = 'dark_minimal'

for site in site_list:

    site_name = df_metadata.loc[df_metadata['station_id'] == int(site),'site_name'].iloc[0]
    output_file(site + '_time_series.html')

    # Reads the data in for the given site
    try:
        df_fl = pd.read_csv('raw_data/flow/' + site + '_monthly_summary.csv')
        df_et = pd.read_csv('raw_data/ucrb_riparain_et/'
                    'intercomparison_output_main_UCRB_CDA_Riparian_ucrb_cda_'+ site +'_EEMETRIC_monthly_et_etof.csv')
    except:
        print("ERROR WHEN READING DATA FROM SITE: " + site)
        exit(1)

    # If a directory for the site does not exist, make it.
    path = os.getcwd() + '/' + site + '_plots'
    if not (os.path.isdir(path)):
        os.mkdir(site + '_plots')

    # Truncates a column in the evap data so that it matches a column in the flow data.
    # The columns need to match so that a left join can be performed
    df_et['END_DATE'] = df_et['END_DATE'].apply(lambda x: x[0:7])
    df_et.rename({'END_DATE': "date"}, axis=1, inplace=True)
    df_merged = df_et.merge(df_fl, on='date', how='left')

    # Changes the start date column from type 'string' to 'datetime'
    # This is needed for plotting the x axis
    df_merged['START_DATE'] = df_et['START_DATE'].apply(lambda x: pd.to_datetime(x))

    # Here the month column is changed from int to string.
    # Example: 1 --> 'jan'
    df_merged['month'] = df_merged['month'].apply(lambda x: month_dict[x])

    '''   #######################################################
    # Series plot Configuration
    p = figure(x_axis_type="datetime", width=1500)
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.circle(x='START_DATE', y='min_cfs',
           legend_label='Minimum Stream Flow, Monthly (cfs)',
             source=ColumnDataSource(df_merged),
             color='blue', size=5)
    p.line(x='START_DATE', y='min_cfs',
             source=ColumnDataSource(df_merged),
             color='blue')

    p.extra_y_ranges = {"foo": Range1d(start=df_merged['ET_MEAN'].min() - 5, end=df_merged['ET_MEAN'].max() + 5)}
    p.circle(x='START_DATE', y='ET_MEAN',
           source=ColumnDataSource(df_merged),
           y_range_name='foo',
           legend_label='Mean Evapotranspiration, Monthly (mm/d)',#idk if this is the right units
           color='green', size=5)
    p.line(x='START_DATE', y='ET_MEAN',
           source=ColumnDataSource(df_merged),
           y_range_name='foo',
           color='green')

    p.title.text = 'SITE: ' + site_name + ', ' + site + ' - Flow vs. ET'
    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = 'Minimum Stream Flow, Monthly (cfs)'
    p.add_layout(LinearAxis(y_range_name="foo", axis_label='Mean Evapotranspiration, Monthly (mm/d)'), 'right')

    hover = HoverTool()
    p.legend.click_policy='hide'
    hover.tooltips=[
        ('Year', '@year'),
        ('Month', '@month'),
        ('Mean Evapotranspiration', '@ET_MEAN'),
        ('Minimum Stream Flow', '@min_cfs')
    ]
    p.add_tools(hover)

    os.chdir(path)
    save(p)

    #######################################################
    # Scatter plot Configuration
    output_file(site + '_scatter_plot.html')

    p2 = figure(width=900, height=900)
    p2.xgrid.grid_line_color = None
    p2.ygrid.grid_line_color = None
    p2.circle(x='min_cfs', y='ET_MEAN',
             source=ColumnDataSource(df_merged),
             color='black', fill_color="pink",
             size=5)

    p2.title.text = 'SITE: ' + site_name + ', ' + site + ' - Flow vs. ET'
    p2.yaxis.axis_label = 'Mean Evapotranspiration, Monthly (mm/d)'
    p2.xaxis.axis_label = 'Minimum Stream Flow, Monthly (cfs)'

    hover2 = HoverTool()
    hover2.tooltips=[
        ('Year', '@year'),
        ('Month', '@month'),
        ('Mean Evapotranspiration', '@ET_MEAN'),
        ('Minimum Stream Flow', '@min_cfs')
    ]
    p2.add_tools(hover2)

    save(p2)

    #######################################################
    # Monthly scatter plot

    output_file(site + '_monthly_scatter_plot.html')
    list_of_monthly_figs = []

    for i in range(12):

        df_monthly = df_merged[df_merged["month"] == month_dict[i+1]]

        p_month = figure(width=450, height=450)
        p_month.xgrid.grid_line_color = None
        p_month.ygrid.grid_line_color = None
        p_month.circle(x='min_cfs', y='ET_MEAN',
                 source=ColumnDataSource(df_monthly),
                 color='black', fill_color="pink",
                 size=5)

        p_month.title.text = month_dict[i+1] + ' - ' + site_name + ', ' + site
        p_month.yaxis.axis_label = 'Mean Evapotranspiration, Monthly (mm/d)'
        p_month.xaxis.axis_label = 'Minimum Stream Flow, Monthly (cfs)'

        hover3 = HoverTool()
        hover3.tooltips = [
            ('Year', '@year'),
            ('Mean Evapotranspiration', '@ET_MEAN'),
            ('Minimum Stream Flow', '@min_cfs')
        ]
        p_month.add_tools(hover3)

        list_of_monthly_figs.append(p_month)

    save(gridplot([[list_of_monthly_figs[0], list_of_monthly_figs[1], list_of_monthly_figs[2], list_of_monthly_figs[3]],
                  [list_of_monthly_figs[4], list_of_monthly_figs[5], list_of_monthly_figs[6], list_of_monthly_figs[7]],
                  [list_of_monthly_figs[8], list_of_monthly_figs[9], list_of_monthly_figs[10], list_of_monthly_figs[11]]]))

    os.chdir('..')'''

    #######################################################
    # Pearson Correlation Coefficient Calculations

    #new_df = pd.read_excel('monthly_gage_vs_et_correlations.xlsx')
    #print(new_df)

    df_mean_r = pd.DataFrame({'station_id': [], 'site_name': [], 'January': [], 'February': [],
                              'March': [], 'April': [], 'May': [], 'June': [], 'July': [], 'August': [],
                              'September': [], 'October': [], 'November': [], 'December': []})

    df_mean_r = df_mean_r.transpose()
    df_mean_p = df_mean_r.copy(deep=True)
    df_max_r = df_mean_r.copy(deep=True)
    df_max_p = df_mean_r.copy(deep=True)
    df_min_r = df_mean_r.copy(deep=True)
    df_min_p = df_mean_r.copy(deep=True)

    for i in range(12):

        df_monthly = df_merged[df_merged["month"] == month_dict[i+1]]

        r_correlation_mean, p_mean = stats.pearsonr(df_monthly['ET_MEAN'], df_monthly['mean_cfs'])
        r_correlation_max, p_max = stats.pearsonr(df_monthly['ET_MEAN'], df_monthly['max_cfs'])
        r_correlation_min, p_min = stats.pearsonr(df_monthly['ET_MEAN'], df_monthly['min_cfs'])

    writer = pd.ExcelWriter('demo.xlsx', engine='xlsxwriter')

    df_mean_r.to_excel(writer, sheet_name='mean_flow', index=True)
    df_mean_p.to_excel(writer, sheet_name='mean_flow', index=True, startrow=17)
    df_max_r.to_excel(writer, sheet_name='max_flow', index=True)
    df_max_p.to_excel(writer, sheet_name='max_flow', index=True, startrow=17)
    df_min_r.to_excel(writer, sheet_name='min_flow', index=True)
    df_min_p.to_excel(writer, sheet_name='min_flow', index=True, startrow=17)

    ws_mean = writer.sheets['mean_flow']
    ws_mean.write_string(0, 0, 'Pearson Correlation Coefficient: R')
    ws_mean.write_string(17, 0, 'P-value')
    ws_mean.set_column(0, 0, 35)
    ws_mean.set_column(1, 50, 50)
    ws_mean = writer.sheets['max_flow']
    ws_mean.write_string(0, 0, 'Pearson Correlation Coefficient: R')
    ws_mean.write_string(17, 0, 'P-value')
    ws_mean.set_column(0, 0, 35)
    ws_mean.set_column(1, 50, 50)
    ws_mean = writer.sheets['min_flow']
    ws_mean.write_string(0, 0, 'Pearson Correlation Coefficient: R')
    ws_mean.write_string(17, 0, 'P-value')
    ws_mean.set_column(0, 0, 35)
    ws_mean.set_column(1, 50, 50)

    writer.save()

    for i in range(12):

        df_monthly = df_merged[df_merged["month"] == month_dict[i+1]]

        r_correlation_mean, p_mean = stats.pearsonr(df_monthly['ET_MEAN'], df_monthly['mean_cfs'])
        r_correlation_max, p_max = stats.pearsonr(df_monthly['ET_MEAN'], df_monthly['max_cfs'])
        r_correlation_min, p_min = stats.pearsonr(df_monthly['ET_MEAN'], df_monthly['min_cfs'])
