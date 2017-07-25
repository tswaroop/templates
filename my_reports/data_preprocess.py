import pandas as pd
from templates.common.common import get_engine
from gramex import DB


def get_max_date():
    engine = get_engine()
    max_date = pd.read_sql('SELECT max(PRG_DATE) FROM FACT_CUST_REV_AGG_DLY', engine)
    return max_date if len(max_date) else None


def get_data(table_name, DB):
    engine = get_engine()
    if table_name not in DB:
      data = pd.read_sql('select * from ' + table_name, engine)
      for col in data.columns:
        data[col] = data[col].astype(str)
      DB[table_name] = data
    else:
      data = DB[table_name]
      data
    return data

emp_acc = get_data('REF_EMPLOYEE_ACCESS', DB)
emp_hierarchy = get_data('REF_EMPLOYEE_HIERARCHY', DB)

def get_emp_channels():
  emp_channels = {}
  emp_channels_advts = {}
  curr_hierarchy = emp_acc['EMPLOYEE_KEY'].unique()
  for emp in curr_hierarchy:
      channels = emp_acc[emp_acc['EMPLOYEE_KEY'] == emp]['CHANNEL_GROUP_KEY'].unique().tolist()
      try:
          emp_name = emp_hierarchy[emp_hierarchy['EMPLOYEE_KEY'] == emp]['EMPLOYEE_NAME'].values[0]
      except IndexError:
          break
      if emp_name in emp_channels:
          emp_channels[emp_name] = list(set(emp_channels[emp_name] + channels))        
      else:
          emp_channels[emp_name] = channels

      try:
        manager = emp_hierarchy[emp_hierarchy['EMPLOYEE_KEY'] == emp]['MANAGER_NAME'].values[0]
        manager_role = emp_hierarchy[emp_hierarchy['EMPLOYEE_NAME'] == manager]['EMPLOYEE_ROLE'].values[0]
        while (manager_role != 'HO GROUP'):
            try:
              if manager in emp_channels:
                  emp_channels[manager] = list(set(emp_channels[manager] + channels))
              else:
                  emp_channels[manager] = channels
              manager = emp_hierarchy[emp_hierarchy['EMPLOYEE_NAME'] == manager]['MANAGER_NAME'].values[0]
              manager_role = emp_hierarchy[emp_hierarchy['MANAGER_NAME'] == manager]['EMPLOYEE_ROLE'].values[0]
            except:
              break
      except:
        pass
  return emp_channels





def get_emp_keys():
  emp_keys = {}
  curr_hierarchy = emp_acc['EMPLOYEE_KEY'].unique()
  for emp in curr_hierarchy:
      try:
        manager = emp_hierarchy[emp_hierarchy['EMPLOYEE_KEY'] == emp]['MANAGER_NAME'].values[0]
        manager_role = emp_hierarchy[emp_hierarchy['EMPLOYEE_NAME'] == manager]['EMPLOYEE_ROLE'].values[0]
        while (manager_role != 'HO GROUP'):
            try:
              if manager in emp_keys:
                  emp_keys[manager].append(emp)
              else:
                  emp_keys[manager] = [str(emp)]
              manager = emp_hierarchy[emp_hierarchy['EMPLOYEE_NAME'] == manager]['MANAGER_NAME'].values[0]
              manager_role = emp_hierarchy[emp_hierarchy['MANAGER_NAME'] == manager]['EMPLOYEE_ROLE'].values[0]
            except:
              break
      except:
        pass
  return emp_keys
