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
site_list = ['09180000',        # 'DOLORES RIVER NEAR CISCO, UT',
             '09209400',        # ' GREEN RIVER NEAR LA BARGE, WY',
             '09260000',        # LITTLE SNAKE RIVER NEAR LILY, CO
             '09302000',        # DUCHESNE RIVER NEAR RANDLETT, UT,
             '09306500',        # WHITE RIVER NEAR WATSON, UTAH
             '09379500',        # SAN JUAN RIVER NEAR BLUFF, UT
             ]

# Right now the script is set up so that it only works with one ET variable at a time.
# For example, the script works with 'ET_MEAN' or 'EToF_MEAN', not both at the same time.
# To export different variables, the global variable below must be changed.
ET_var = 'ET_MEAN'
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

# These dfs are used for exporting stats to the .xlsx files.
# Each time the loop is executed, a record is appended onto each df.
# When the loop is finished, the dfs are exported to the corresponding .xlsx files.
df_pearson_mean_r = pd.DataFrame({'station_id': [], 'site_name': [], 'January': [], 'February': [],
                          'March': [], 'April': [], 'May': [], 'June': [], 'July': [], 'August': [],
                          'September': [], 'October': [], 'November': [], 'December': []})
df_pearson_mean_p = df_pearson_mean_r.copy(deep=True)
df_pearson_max_r = df_pearson_mean_r.copy(deep=True)
df_pearson_max_p = df_pearson_mean_r.copy(deep=True)
df_pearson_min_r = df_pearson_mean_r.copy(deep=True)
df_pearson_min_p = df_pearson_mean_r.copy(deep=True)

df_kendall_mean_r = df_pearson_mean_r.copy(deep=True)
df_kendall_mean_p = df_pearson_mean_r.copy(deep=True)
df_kendall_max_r = df_pearson_mean_r.copy(deep=True)
df_kendall_max_p = df_pearson_mean_r.copy(deep=True)
df_kendall_min_r = df_pearson_mean_r.copy(deep=True)
df_kendall_min_p = df_pearson_mean_r.copy(deep=True)

# Read in the metadata so that the site names can be attached to the graph.
try:
    df_metadata = pd.read_csv('raw_data/metadata.csv')
except:
    print("ERROR WITH READING METADATA")
    exit(1)

# Create a folder for 'plots'
path = os.getcwd() + '/plots'
if not (os.path.isdir(path)):
    os.mkdir('plots')
os.chdir('plots')

for site in site_list:

    site_name = df_metadata.loc[df_metadata['station_id'] == int(site),'site_name'].iloc[0]
    output_file(site + '_' + ET_var + '_time_series.html')

    # Reads the data in for the given site
    try:
        df_fl = pd.read_csv('../raw_data/flow/' + site + '_monthly_summary.csv')
        df_et = pd.read_csv('../raw_data/ucrb_riparain_et/'
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

    #######################################################
    # Series plot Configuration
    p = figure(x_axis_type="datetime", width=1500)
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.circle(x='START_DATE', y='min_cfs',
           legend_label='min_cfs, Monthly (cfs)',
             source=ColumnDataSource(df_merged),
             color='blue', size=5)
    p.line(x='START_DATE', y='min_cfs',
             source=ColumnDataSource(df_merged),
             color='blue')

    p.extra_y_ranges = {"foo": Range1d(start=df_merged[ET_var].min() - 5, end=df_merged[ET_var].max() + 5)}
    p.circle(x='START_DATE', y=ET_var,
           source=ColumnDataSource(df_merged),
           y_range_name='foo',
           legend_label= ET_var + ', Monthly (mm/d)',#idk if this is the right units
           color='green', size=5)
    p.line(x='START_DATE', y=ET_var,
           source=ColumnDataSource(df_merged),
           y_range_name='foo',
           color='green')

    p.title.text = 'SITE: ' + site_name + ', ' + site + ' - min_cfs vs. ' + ET_var
    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = 'min_cf, Monthly (cfs)'
    p.add_layout(LinearAxis(y_range_name="foo", axis_label = ET_var + ', Monthly (mm/d)'), 'right')

    hover = HoverTool()
    p.legend.click_policy='hide'
    hover.tooltips=[
        ('Year', '@year'),
        ('Month', '@month'),
        ('Mean Evapotranspiration', '@' + ET_var),
        ('Minimum Stream Flow', '@min_cfs')
    ]
    p.add_tools(hover)

    os.chdir(path)
    save(p)

    #######################################################
    # Scatter plot Configuration
    output_file(site + '_' + ET_var + '_scatter_plot.html')

    p2 = figure(width=900, height=900)
    p2.xgrid.grid_line_color = None
    p2.ygrid.grid_line_color = None
    p2.circle(x='min_cfs', y=ET_var,
             source=ColumnDataSource(df_merged),
             color='black', fill_color="pink",
             size=5)

    p2.title.text = 'SITE: ' + site_name + ', ' + site + ' - Flow vs. ET'
    p2.yaxis.axis_label = ET_var + ', Monthly (mm/d)'
    p2.xaxis.axis_label = 'min_cfs, Monthly (cfs)'

    hover2 = HoverTool()
    hover2.tooltips=[
        ('Year', '@year'),
        ('Month', '@month'),
        ('Mean Evapotranspiration', '@' + ET_var),
        ('Minimum Stream Flow', '@min_cfs')
    ]
    p2.add_tools(hover2)

    save(p2)

    #######################################################
    # Monthly scatter plot

    output_file(site + '_' + ET_var + '_monthly_scatter_plot.html')
    list_of_monthly_figs = []

    for i in range(12):

        df_monthly = df_merged[df_merged["month"] == month_dict[i+1]]

        p_month = figure(width=450, height=450)
        p_month.xgrid.grid_line_color = None
        p_month.ygrid.grid_line_color = None
        p_month.circle(x='min_cfs', y=ET_var,
                 source=ColumnDataSource(df_monthly),
                 color='black', fill_color="pink",
                 size=5)

        p_month.title.text = month_dict[i+1] + ' - ' + site_name + ', ' + site
        p_month.yaxis.axis_label = ET_var + ', Monthly (mm/d)'
        p_month.xaxis.axis_label = 'min_cfs, Monthly (cfs)'

        hover3 = HoverTool()
        hover3.tooltips = [
            ('Year', '@year'),
            ('Mean Evapotranspiration', '@' + ET_var),
            ('Minimum Stream Flow', '@min_cfs')
        ]
        p_month.add_tools(hover3)

        list_of_monthly_figs.append(p_month)

    save(gridplot([[list_of_monthly_figs[0], list_of_monthly_figs[1], list_of_monthly_figs[2], list_of_monthly_figs[3]],
                  [list_of_monthly_figs[4], list_of_monthly_figs[5], list_of_monthly_figs[6], list_of_monthly_figs[7]],
                  [list_of_monthly_figs[8], list_of_monthly_figs[9], list_of_monthly_figs[10], list_of_monthly_figs[11]]]))

    os.chdir('..')

    ##########################################################################
    # Pearson Correlation Coefficient Calculations
    #
    # Note: It would be prettier to change the next 2 sections into 1 function

    record_pearson_mean_r = [site, site_name]
    record_pearson_mean_p = [site, site_name]
    record_pearson_max_r = [site, site_name]
    record_pearson_max_p = [site, site_name]
    record_pearson_min_r = [site, site_name]
    record_pearson_min_p = [site, site_name]

    for i in range(12):

        df_monthly = df_merged[df_merged["month"] == month_dict[i+1]]

        r_correlation_mean, p_mean = stats.pearsonr(df_monthly[ET_var], df_monthly['mean_cfs'])
        r_correlation_max, p_max = stats.pearsonr(df_monthly[ET_var], df_monthly['max_cfs'])
        r_correlation_min, p_min = stats.pearsonr(df_monthly[ET_var], df_monthly['min_cfs'])

        record_pearson_mean_r.append(r_correlation_mean)
        record_pearson_mean_p.append(p_mean)
        record_pearson_max_r.append(r_correlation_max)
        record_pearson_max_p.append(p_max)
        record_pearson_min_r.append(r_correlation_min)
        record_pearson_min_p.append(p_min)

    df_pearson_mean_r.loc[len(df_pearson_mean_r.index)] = record_pearson_mean_r
    df_pearson_mean_p.loc[len(df_pearson_mean_p.index)] = record_pearson_mean_p
    df_pearson_max_r.loc[len(df_pearson_max_r.index)] = record_pearson_max_r
    df_pearson_max_p.loc[len(df_pearson_max_p.index)] = record_pearson_max_p
    df_pearson_min_r.loc[len(df_pearson_min_r.index)] = record_pearson_min_r
    df_pearson_min_p.loc[len(df_pearson_min_p.index)] = record_pearson_min_p

    #######################################################
    # Kendall Rank Correlation Coefficient Calculations

    record_kendall_mean_r = [site, site_name]
    record_kendall_mean_p = [site, site_name]
    record_kendall_max_r = [site, site_name]
    record_kendall_max_p = [site, site_name]
    record_kendall_min_r = [site, site_name]
    record_kendall_min_p = [site, site_name]

    for i in range(12):

        df_monthly = df_merged[df_merged["month"] == month_dict[i+1]]

        tau_correlation_mean, p_mean = stats.kendalltau(df_monthly[ET_var], df_monthly['mean_cfs'])
        tau_correlation_max, p_max = stats.kendalltau(df_monthly[ET_var], df_monthly['max_cfs'])
        tau_correlation_min, p_min = stats.kendalltau(df_monthly[ET_var], df_monthly['min_cfs'])

        record_kendall_mean_r.append(tau_correlation_mean)
        record_kendall_mean_p.append(p_mean)
        record_kendall_max_r.append(tau_correlation_max)
        record_kendall_max_p.append(p_max)
        record_kendall_min_r.append(tau_correlation_min)
        record_kendall_min_p.append(p_min)

    df_kendall_mean_r.loc[len(df_kendall_mean_r.index)] = record_kendall_mean_r
    df_kendall_mean_p.loc[len(df_kendall_mean_p.index)] = record_kendall_mean_p
    df_kendall_max_r.loc[len(df_kendall_max_r.index)] = record_kendall_max_r
    df_kendall_max_p.loc[len(df_kendall_max_p.index)] = record_kendall_max_p
    df_kendall_min_r.loc[len(df_kendall_min_r.index)] = record_kendall_min_r
    df_kendall_min_p.loc[len(df_kendall_min_p.index)] = record_kendall_min_p

################################################################
# Set the metadata for the .xlsx files and export the dataframes.
# We do this for both kendall and pearson files.

os.chdir('..')
path = os.getcwd() + '/tables'
if not (os.path.isdir(path)):
    os.mkdir('tables')
os.chdir('tables')

# Pearson start
df_pearson_mean_r = df_pearson_mean_r.transpose()
df_pearson_mean_p = df_pearson_mean_p.transpose()
df_pearson_max_r = df_pearson_max_r.transpose()
df_pearson_max_p = df_pearson_max_p.transpose()
df_pearson_min_r = df_pearson_min_r.transpose()
df_pearson_min_p = df_pearson_min_p.transpose()

writer = pd.ExcelWriter('pearson_' + ET_var + '_monthly_gage_vs_et_correlations.xlsx', engine='xlsxwriter')

df_pearson_mean_r.to_excel(writer, sheet_name='mean_flow', index=True)
df_pearson_mean_p.to_excel(writer, sheet_name='mean_flow', index=True, startrow=17)
df_pearson_max_r.to_excel(writer, sheet_name='max_flow', index=True)
df_pearson_max_p.to_excel(writer, sheet_name='max_flow', index=True, startrow=17)
df_pearson_min_r.to_excel(writer, sheet_name='min_flow', index=True)
df_pearson_min_p.to_excel(writer, sheet_name='min_flow', index=True, startrow=17)

ws = writer.sheets['mean_flow']
ws.write_string(0, 0, 'Pearson Correlation Coefficient: R')
ws.write_string(17, 0, 'P-value')
ws.set_column(0, 0, 35)
ws.set_column(1, 50, 50)
ws = writer.sheets['max_flow']
ws.write_string(0, 0, 'Pearson Correlation Coefficient: R')
ws.write_string(17, 0, 'P-value')
ws.set_column(0, 0, 35)
ws.set_column(1, 50, 50)
ws = writer.sheets['min_flow']
ws.write_string(0, 0, 'Pearson Correlation Coefficient: R')
ws.write_string(17, 0, 'P-value')
ws.set_column(0, 0, 35)
ws.set_column(1, 50, 50)

# Kendall start
df_kendall_mean_r = df_kendall_mean_r.transpose()
df_kendall_mean_p = df_kendall_mean_p.transpose()
df_kendall_max_r = df_kendall_max_r.transpose()
df_kendall_max_p = df_kendall_max_p.transpose()
df_kendall_min_r = df_kendall_min_r.transpose()
df_kendall_min_p = df_kendall_min_p.transpose()

writer2 = pd.ExcelWriter('kendall_' + ET_var + '_monthly_gage_vs_et_correlations.xlsx', engine='xlsxwriter')

df_kendall_mean_r.to_excel(writer2, sheet_name='mean_flow', index=True)
df_kendall_mean_p.to_excel(writer2, sheet_name='mean_flow', index=True, startrow=17)
df_kendall_max_r.to_excel(writer2, sheet_name='max_flow', index=True)
df_kendall_max_p.to_excel(writer2, sheet_name='max_flow', index=True, startrow=17)
df_kendall_min_r.to_excel(writer2, sheet_name='min_flow', index=True)
df_kendall_min_p.to_excel(writer2, sheet_name='min_flow', index=True, startrow=17)

ws = writer2.sheets['mean_flow']
ws.write_string(0, 0, "Kendall's Correlation: Tau")
ws.write_string(17, 0, 'P-value')
ws.set_column(0, 0, 35)
ws.set_column(1, 50, 50)
ws = writer2.sheets['max_flow']
ws.write_string(0, 0, "Kendall's Correlation: Tau")
ws.write_string(17, 0, 'P-value')
ws.set_column(0, 0, 35)
ws.set_column(1, 50, 50)
ws = writer2.sheets['min_flow']
ws.write_string(0, 0, "Kendall's Correlation: Tau")
ws.write_string(17, 0, 'P-value')
ws.set_column(0, 0, 35)
ws.set_column(1, 50, 50)

writer.save()
writer2.save()

