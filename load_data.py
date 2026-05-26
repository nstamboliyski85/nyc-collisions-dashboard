import pandas as pd
import deltalake as dl
import os
import logging
import traceback


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

base_fldr=os.path.dirname(__file__)
file_name="Motor_Vehicle_Collisions_-_Crashes.csv"
data_file=os.path.join(base_fldr, file_name)


def load_and_transform_data(csv_data_file):
      """Loading the datafile and transforming data to be ready for reporting"""
      columns_to_extract=['COLLISION_ID','CRASH DATE','CRASH TIME','BOROUGH','ZIP CODE','LATITUDE','LONGITUDE','LOCATION','ON STREET NAME',
                        'NUMBER OF PERSONS INJURED','NUMBER OF PERSONS KILLED','VEHICLE TYPE CODE 1', 'VEHICLE TYPE CODE 2',
                        'CONTRIBUTING FACTOR VEHICLE 1', 'CONTRIBUTING FACTOR VEHICLE 2',
                        'NUMBER OF PEDESTRIANS INJURED','NUMBER OF PEDESTRIANS KILLED','NUMBER OF CYCLIST INJURED','NUMBER OF CYCLIST KILLED']

      df=pd.read_csv(csv_data_file, usecols=columns_to_extract, dtype={'ZIP CODE':str})
      df=df.sort_values('COLLISION_ID').set_index(['COLLISION_ID'])

      df['ZIP CODE']= df['ZIP CODE'].str.strip()
      df['ZIP CODE']= pd.to_numeric(df['ZIP CODE'], errors='raise')
      df['ZIP CODE']=df['ZIP CODE'].fillna(0).astype(int)

      target_rows_mask = df['LOCATION'].notna() & (df['LOCATION'] != '') & df['LATITUDE'].isna() & df['LONGITUDE'].isna()

      if target_rows_mask.any():
            row_count = target_rows_mask.sum()
            logging.info(f"Data anomaly caught: Found {row_count} rows with LOCATION but missing Latitude and Longitude. Extracting...")
      
            extracted = df['LOCATION'].str.extract(r'\(([-\d.]+),\s*([-\d.]+)\)')
            df.loc[target_rows_mask, 'LATITUDE'] = pd.to_numeric(extracted[0], errors='coerce')
            df.loc[target_rows_mask, 'LONGITUDE'] = pd.to_numeric(extracted[1], errors='coerce')
      else:
            logging.info("Geographic check passed: No missing coordinate floats found for populated locations.")
      df.drop(columns=['LOCATION'], inplace=True)

      df['CRASH DATE']=pd.to_datetime(df['CRASH DATE'], format='%m/%d/%Y')
      df['YEAR']=df['CRASH DATE'].dt.year.astype('int16')
      df['MONTH']=df['CRASH DATE'].dt.month.astype('int8')
      df['CRASH HOUR']= pd.to_datetime(df['CRASH TIME'], format='%H:%M', errors='raise').dt.hour
      df['CRASH HOUR']=df['CRASH HOUR'].fillna(pd.to_datetime(df['CRASH TIME'], format='%I:%M %p', errors='coerce').dt.hour).fillna(-1).astype('int8')
      df['BOROUGH']=df['BOROUGH'].fillna('UNKNOWN').astype(str).str.strip().str.upper().astype(str)
      df['CONTRIBUTING FACTOR VEHICLE 1']=df['CONTRIBUTING FACTOR VEHICLE 1'].fillna('Unspecified').astype(str).str.strip().astype(str)
      df['CONTRIBUTING FACTOR VEHICLE 2']=df['CONTRIBUTING FACTOR VEHICLE 2'].fillna('Unspecified').astype(str).str.strip().astype(str)
      df['VEHICLE TYPE CODE 1']=df['VEHICLE TYPE CODE 1'].fillna('UNKNOWN').astype(str).str.strip().astype(str)
      df['VEHICLE TYPE CODE 2']=df['VEHICLE TYPE CODE 2'].fillna('UNKNOWN').astype(str).str.strip().astype(str)
      df['NUMBER OF PERSONS INJURED']=df['NUMBER OF PERSONS INJURED'].fillna(0).astype(int)
      df['NUMBER OF PERSONS KILLED']=df['NUMBER OF PERSONS KILLED'].fillna(0).astype(int)


      return df

logging.info('Loading the data file into dataframe and data transformation...')
try:
      df=load_and_transform_data(data_file)
except Exception as e:
      logging.error(f"Loading and transform of data failed with error : {str(e)}\n {traceback.format_exc()}")


print(df)
#print(df.dtypes)


logging.info('Adding DaataFrame to the deltalake')

deltalake_path=os.path.join(base_fldr+'/deltalake',file_name.replace('.csv',''))

dl.write_deltalake(deltalake_path,df, mode='overwrite', schema_mode='overwrite', partition_by=['YEAR', 'BOROUGH'])

logging.info(f"Dataframe saved to parquet file path : {deltalake_path}")

