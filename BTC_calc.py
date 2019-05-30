import requests
import datetime
import pandas as pd
from stockstats import StockDataFrame
from math import pi
from bokeh.plotting import figure, show, output_notebook, output_file
output_notebook()
from bokeh.palettes import Category20
from bokeh.models.widgets import PreText
from bokeh.models import BooleanFilter, CDSView, BoxAnnotation, Band, Span, Select, LinearAxis, DataRange1d, Range1d
from bokeh.models.formatters import PrintfTickFormatter, NumeralTickFormatter
from bokeh.layouts import column

RED = Category20[7][6]
GREEN = Category20[5][4]

BLUE = Category20[3][0]
BLUE_LIGHT = Category20[3][1]

ORANGE = Category20[3][2]
PURPLE = Category20[9][8]
BROWN = Category20[11][10]

TOOLS = 'pan,wheel_zoom,reset'

from_symbol = 'BTC'
to_symbol = 'USD'
exchange = 'Bitstamp'
datetime_interval = 'hour'

def get_filename(from_symbol, to_symbol, exchange, datetime_interval, download_date):
    return '%s_%s_%s_%s_%s.csv' % (from_symbol, to_symbol, exchange, datetime_interval, download_date)

#Define date
now = datetime.datetime.now()
year = '{:02d}'.format(now.year)
month = '{:02d}'.format(now.month)
day = '{:02d}'.format(now.day)
hour = '{:02d}'.format(now.hour)
minute = '{:02d}'.format(now.minute)
day_month_year = '{}-{}-{}'.format(year, month, day)
hour_minute = '{}:{}'.format(hour, minute)

filename = get_filename(from_symbol, to_symbol, exchange, datetime_interval, day_month_year)

def read_dataset(filename):
    print('Reading data from %s' % filename)
    df = pd.read_csv(filename)
    df.datetime = pd.to_datetime(df.datetime) # change type from object to datetime
    df = df.set_index('datetime') 
    df = df.sort_index() # sort by datetime
    print(df.shape)
    return df

#Calc MACD
df = read_dataset(filename)
df = StockDataFrame.retype(df)
df['macd'] = df.get('macd') # calculate MACD

#Calc RSI
stock_df = StockDataFrame.retype(df)
df['rsi']=stock_df['rsi_14']

#Calc SMA
stog_df = StockDataFrame.retype(df)
df['SMA_50']=stog_df['close_50_sma']
stokk_df = StockDataFrame.retype(df)
df['SMA_100']=stokk_df['close_100_sma']

del df['close_12_ema']
del df['close_26_ema']
del df['close_-1_s']
del df['close_-1_d']
del df['rs_14']
del df['rsi_14']
del df['close_100_sma']
del df['close_50_sma']

print('Saving data to MACD & RSI')
df.to_csv('data.csv', index=False)

datetime_from = '2019-01-01 00:00'
datetime_to = day_month_year+' '+hour_minute


def get_candlestick_width(datetime_interval):
    if datetime_interval == 'minute':
        return 30 * 60 * 1000  # half minute in ms
    elif datetime_interval == 'hour':
        return 0.5 * 60 * 60 * 1000  # half hour in ms
    elif datetime_interval == 'day':
        return 12 * 60 * 60 * 1000  # half day in ms


df_limit = df[datetime_from: datetime_to].copy()
inc = df_limit.close > df_limit.open
dec = df_limit.open > df_limit.close

title = 'Data from %s to %s for %s and %s from %s (%s)' % (
    datetime_from, datetime_to, from_symbol, to_symbol, exchange, datetime_interval)
p = figure(title=title, x_axis_type="datetime",  plot_width=1200, plot_height=400, tools=TOOLS, toolbar_location='above')

p.line(df_limit.index, df_limit.close, color='black')
p.line(df_limit.index, df.sma_50, legend='SMA 50',color=BLUE)
p.line(df_limit.index, df.SMA_100, legend='SMA 100',color=ORANGE)

p.legend.location = "top_left"
p.legend.border_line_alpha = 1
p.legend.background_fill_alpha = 1
p.legend.click_policy = "mute"
p.yaxis.formatter = NumeralTickFormatter(format='$ 0,0[.]000')

# plot candlesticks
candlestick_width = get_candlestick_width(datetime_interval)
p.segment(df_limit.index, df_limit.high,
          df_limit.index, df_limit.low, color="black")
p.vbar(df_limit.index[inc], candlestick_width, df_limit.open[inc],
       df_limit.close[inc], fill_color="#D5E1DD", line_color="black")
p.vbar(df_limit.index[dec], candlestick_width, df_limit.open[dec],
       df_limit.close[dec], fill_color="#F2583E", line_color="black")

# plot macd strategy
p2 = figure(x_axis_type="datetime", plot_width=1200, plot_height=300, title="MACD", tools=TOOLS, toolbar_location='above')
#p2.vbar(x=df_limit.index, bottom=[
       #0 for _ in df_limit.index], top=df_limit.macdh, width=4, color=PURPLE)

p2.line(df_limit.index, 0, color='black')
p2.line(df_limit.index, df_limit.macd, color='blue', legend='MACD')
p2.line(df_limit.index, df_limit.macds, color='orange', legend='Signal')

p2.legend.location = "top_left"
p2.legend.border_line_alpha = 1
p2.legend.background_fill_alpha = 1
p2.legend.click_policy = "mute"

#plot RSI
p3 = figure(x_axis_type="datetime",  plot_width=1200, plot_height=300, title='RSI', tools=TOOLS, toolbar_location='above')
p3.line(df_limit.index, df.rsi, line_width=1, color=ORANGE)
#low_box = BoxAnnotation(top=30, fill_alpha=0.1, fill_color=RED)
#p3.add_layout(low_box)
#high_box = BoxAnnotation(bottom=70, fill_alpha=0.1, fill_color=GREEN)
#p3.add_layout(high_box)

box = BoxAnnotation(bottom=30, top=70, fill_alpha=0.25, fill_color=PURPLE)
p3.add_layout(box)
hline = Span(location=30, dimension='width', line_color='black', line_dash=[5,10], line_width=0.5)
p3.renderers.extend([hline])
hline = Span(location=50, dimension='width', line_color='black', line_width=0.5)
p3.renderers.extend([hline])
hline = Span(location=70, dimension='width', line_color='black', line_dash=[5,10], line_width=0.5)
p3.renderers.extend([hline])

#p3.y_range = Range1d(0, 100)
p3.yaxis.ticker = [30, 50, 70]
p3.yaxis.formatter = PrintfTickFormatter(format="%f%%")
p3.grid.grid_line_alpha = 0.3

output_file("Crypto_ta.html", title="Crypto TA")
show(column(p,p2,p3))


