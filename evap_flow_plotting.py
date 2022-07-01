import pandas as pd
import os
from bokeh.io import output_file, save, show, curdoc
from bokeh.plotting import figure
from bokeh.models import LinearAxis, Range1d, ColumnDataSource
from bokeh.models.tools import HoverTool

# Bug notice: Some of the data recieved had the leading '0' truncated off the front.
# For example '09180000' --> '9180000'
# If there are any errors with reading in the raw data, please check the site numbers.
site_list = ['09180000',        # 'DOLORES RIVER NEAR CISCO, UT',
             '09209400',        # ' GREEN RIVER NEAR LA BARGE, WY',
             '09260000',        # LITTLE SNAKE RIVER NEAR LILY, CO
             '09302000',        # DUCHESNE RIVER NEAR RANDLETT, UT,
             '09306500',        # WHITE RIVER NEAR WATSON, UTAH
             '09379500',        # SAN JUAN RIVER NEAR BLUFF, UT
             ]
curdoc().theme = 'dark_minimal'

for site in site_list:
    output_file(site + '_time_series.html')

    # Reads the data in for the given site
    try:
        df_fl = pd.read_csv('raw_data/flow/' + site + '_monthly_summary.csv')
        df_et = pd.read_csv('raw_data/ucrb_riparain_et/'
                    'intercomparison_output_main_UCRB_CDA_Riparian_ucrb_cda_'+ site +'_EEMETRIC_monthly_et_etof.csv')
    except:
        print("ERROR WITH READING DATA FOR SITE: " + site)
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

    #######################################################
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

    p.title.text = 'SITE: ' + site + ' - Stream Flow vs. Evapotranspiration'
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
    os.chdir('..')

    #######################################################
    # Scatter plot Configuration
    output_file(site + '_scatter_plot.html')

    p2 = figure(width=900, height=900)
    p2.xgrid.grid_line_color = None
    p2.ygrid.grid_line_color = None
    p2.circle(x='min_cfs', y='ET_MEAN',
             source=ColumnDataSource(df_merged),
             color='blue', size=5)

    p2.title.text = 'SITE: ' + site + ' - Stream Flow vs. Evapotranspiration'
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

    os.chdir(path)
    save(p2)
    os.chdir('..')

