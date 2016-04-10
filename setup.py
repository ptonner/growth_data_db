
if __name__ == '__main__':
	import models, bioscreen
	import pandas as pd

	from api import create_plate_from_dataframe
	from api.core import *

	# project = models.Project(name='test')
	# session.add(project)
	# session.commit()

	data = pd.read_csv("data/20141221 H2O2 batch 3/20141221H2O2_batch3.csv")
	plate, wells, data_table = create_plate_from_dataframe(data,'pq_test','test',data_columns=range(2,data.shape[1]),useColumnsForNumber=True,time_parse=bioscreen.convert_time)
