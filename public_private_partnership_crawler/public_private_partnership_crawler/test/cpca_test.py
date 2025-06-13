import cpca
location_str = ["巴彦淖尔市,巴彦淖尔市 五原县,巴彦淖尔市 乌拉特前旗,巴彦淖尔市 乌拉特中旗",]
df = cpca.transform(location_str)

print(df)
