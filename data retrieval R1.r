import pyreadr

result = pyreadr.read_r("C:/Users/mouni/Downloads/ausautoBI8999.rda")
df = result["ausautoBI8999"]   # get the actual DataFrame
print(df.head())