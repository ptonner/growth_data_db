
if __name__ == '__main__':
	from growth_data_db import models, bioscreen
	import pandas as pd

	from growth_data_db.api import create_plate_from_dataframe, add_experimental_design, update_design

	data = pd.read_csv("data/20141221 H2O2 batch 3/20141221H2O2_batch3.csv")
	plate, wells, data_table = create_plate_from_dataframe(data,'pq_test','test',data_columns=range(2,data.shape[1]),useColumnsForNumber=True,time_parse=bioscreen.convert_time)

	key = pd.read_excel("data/20141221 H2O2 batch 3/H2O2_batch3_key.xlsx")

	for v in key['mM H2O2'].unique():
		add_experimental_design('mM H2O2',v,design_type='float')

	g = key.groupby(['mM H2O2'])
	for v in g.groups:
		update_design('mM H2O2',v,g.get_group(v).Well.astype(int).tolist(),plate.name)
